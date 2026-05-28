from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.security import hash_password
from app.database import get_db
from app.deps import get_current_admin
from app.models.admin_audit_log import AdminAuditLog
from app.models.category import Category
from app.models.user import User
from app.repositories import (
    CategoryRepository,
    FeedbackRepository,
    OrderRepository,
    ProductRepository,
    SettingsRepository,
    UserRepository,
)
from app.schemas.admin import (
    AdminAuditLogItem,
    AdminOrderItem,
    AdminRefundRejectBody,
    AdminResetPasswordBody,
    AdminUserItem,
    AdminUserPatch,
)
from app.schemas.category import CategoryCreate, CategoryPublic, CategoryUpdate
from app.schemas.feedback import FeedbackAdminItem, FeedbackAdminUpdate, FeedbackPublic
from app.schemas.order import OrderDetail
from app.schemas.product import ProductDetail, RejectBody
from app.services.admin_audit import log_admin_action
from app.services.order_serializers import serialize_order_detail
from app.services.product_serializers import serialize_product_detail, touch_product_updated

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


@router.get("/categories", response_model=list[CategoryPublic])
def admin_list_categories(db: Session = Depends(get_db)) -> list[CategoryPublic]:
    rows = CategoryRepository(db).list_all()
    return [CategoryPublic.model_validate(c) for c in rows]


@router.post("/categories", response_model=CategoryPublic, status_code=status.HTTP_201_CREATED)
def admin_create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> CategoryPublic:
    cats = CategoryRepository(db)
    name = payload.name.strip()
    if cats.name_exists(name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="分类名称已存在")
    cat = cats.create(Category(name=name, sort_order=payload.sort_order))
    return CategoryPublic.model_validate(cat)


@router.patch("/categories/{category_id}", response_model=CategoryPublic)
def admin_update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
) -> CategoryPublic:
    cats = CategoryRepository(db)
    cat = cats.get_by_id(category_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        name = data["name"].strip()
        if cats.name_exists(name, exclude_id=category_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="分类名称已存在")
        data["name"] = name
    for k, v in data.items():
        setattr(cat, k, v)
    cat = cats.save(cat)
    return CategoryPublic.model_validate(cat)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_category(category_id: int, db: Session = Depends(get_db)) -> None:
    cats = CategoryRepository(db)
    cat = cats.get_by_id(category_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    if cats.count_products(category_id) > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该分类下仍有商品，无法删除")
    cats.delete(cat)


@router.get("/products/pending", response_model=list[ProductDetail])
def admin_list_pending_products(db: Session = Depends(get_db)) -> list[ProductDetail]:
    hot = SettingsRepository(db).hot_rating_threshold()
    rows = ProductRepository(db).list_pending()
    return [serialize_product_detail(p, viewer=None, hot_threshold=hot) for p in rows]


@router.post("/products/{product_id}/approve", response_model=ProductDetail)
def admin_approve_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> ProductDetail:
    products = ProductRepository(db)
    product = products.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    if product.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅待审核商品可通过审核")
    product.status = "approved"
    product.reject_reason = None
    touch_product_updated(product)
    products.save(product)
    loaded = products.get_detail(product_id)
    assert loaded is not None
    hot = SettingsRepository(db).hot_rating_threshold()
    return serialize_product_detail(loaded, viewer=admin, hot_threshold=hot)


@router.post("/products/{product_id}/reject", response_model=ProductDetail)
def admin_reject_product(
    product_id: int,
    payload: RejectBody,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> ProductDetail:
    products = ProductRepository(db)
    product = products.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    if product.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅待审核商品可驳回")
    product.status = "rejected"
    product.reject_reason = payload.reason.strip()
    touch_product_updated(product)
    products.save(product)
    loaded = products.get_detail(product_id)
    assert loaded is not None
    hot = SettingsRepository(db).hot_rating_threshold()
    return serialize_product_detail(loaded, viewer=admin, hot_threshold=hot)


@router.get("/feedback", response_model=list[FeedbackAdminItem])
def admin_list_feedback(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[FeedbackAdminItem]:
    rows = FeedbackRepository(db).list_all(status_filter)
    return [
        FeedbackAdminItem(
            id=f.id,
            user_id=f.user_id,
            username=f.user.username,
            nickname=f.user.nickname,
            subject=f.subject,
            content=f.content,
            status=f.status,
            admin_reply=f.admin_reply,
            created_at=f.created_at,
            updated_at=f.updated_at,
        )
        for f in rows
    ]


@router.get("/users", response_model=list[AdminUserItem])
def admin_list_users(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[AdminUserItem]:
    rows = UserRepository(db).list_for_admin(limit=min(limit, 200), offset=max(offset, 0))
    return [AdminUserItem.model_validate(u) for u in rows]


@router.patch("/users/{user_id}", response_model=AdminUserItem)
def admin_patch_user(
    user_id: int,
    payload: AdminUserPatch,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> AdminUserItem:
    users = UserRepository(db)
    user = users.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if user.id == admin.id and payload.is_disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能禁用当前登录的管理员账号")
    if user.role == "admin" and payload.is_disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能禁用管理员账号")

    user.is_disabled = payload.is_disabled
    user = users.save(user)
    action = "user_enable" if not payload.is_disabled else "user_disable"
    log_admin_action(db, admin.id, action, "user", user.id)
    return AdminUserItem.model_validate(user)


@router.post("/users/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def admin_reset_user_password(
    user_id: int,
    payload: AdminResetPasswordBody,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> None:
    users = UserRepository(db)
    user = users.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user.password_hash = hash_password(payload.new_password)
    users.save(user)
    log_admin_action(db, admin.id, "user_reset_password", "user", user.id)


@router.get("/orders", response_model=list[AdminOrderItem])
def admin_list_orders(
    status_filter: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[AdminOrderItem]:
    rows = OrderRepository(db).list_all(status_filter=status_filter, limit=min(limit, 200))
    return [
        AdminOrderItem(
            id=o.id,
            product_id=o.product_id,
            product_title=o.product_title,
            amount=float(o.amount),
            quantity=o.quantity,
            status=o.status,
            trade_type=o.trade_type,
            refund_reason=o.refund_reason,
            refund_reject_reason=o.refund_reject_reason,
            buyer_id=o.buyer_id,
            buyer_nickname=o.buyer.nickname,
            seller_id=o.seller_id,
            seller_nickname=o.seller.nickname,
            created_at=o.created_at,
            updated_at=o.updated_at,
        )
        for o in rows
    ]


@router.post("/orders/{order_id}/refund-approve", response_model=OrderDetail)
def admin_approve_refund(
    order_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> OrderDetail:
    orders = OrderRepository(db)
    order = orders.get_detail(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if order.status != "refund_pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅退款待审核订单可通过")

    product = ProductRepository(db).get_by_id(order.product_id)
    if product is not None:
        product.stock += order.quantity
        touch_product_updated(product)
        db.add(product)

    order.status = "refunded"
    order.refund_reject_reason = None
    order.updated_at = datetime.now(timezone.utc)
    orders.save(order)
    log_admin_action(db, admin.id, "refund_approve", "order", order.id, order.refund_reason)
    loaded = orders.get_detail(order_id)
    assert loaded is not None
    return serialize_order_detail(loaded)


@router.post("/orders/{order_id}/refund-reject", response_model=OrderDetail)
def admin_reject_refund(
    order_id: int,
    payload: AdminRefundRejectBody,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> OrderDetail:
    orders = OrderRepository(db)
    order = orders.get_by_id(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if order.status != "refund_pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅退款待审核订单可驳回")

    note = payload.note.strip() if payload.note else None
    order.status = "pending_receipt" if order.fulfilled_at is not None else "pending_fulfillment"
    order.refund_reject_reason = note or "管理员驳回退款申请"
    order.updated_at = datetime.now(timezone.utc)
    orders.save(order)
    log_admin_action(db, admin.id, "refund_reject", "order", order.id, note)
    loaded = orders.get_detail(order_id)
    assert loaded is not None
    return serialize_order_detail(loaded)


@router.get("/audit-logs", response_model=list[AdminAuditLogItem])
def admin_list_audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[AdminAuditLogItem]:
    stmt = (
        select(AdminAuditLog)
        .options(selectinload(AdminAuditLog.admin))
        .order_by(AdminAuditLog.created_at.desc())
        .limit(min(limit, 100))
    )
    rows = list(db.scalars(stmt).all())
    return [
        AdminAuditLogItem(
            id=r.id,
            admin_id=r.admin_id,
            admin_username=r.admin.username,
            action=r.action,
            target_type=r.target_type,
            target_id=r.target_id,
            detail=r.detail,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.patch("/feedback/{feedback_id}", response_model=FeedbackPublic)
def admin_update_feedback(
    feedback_id: int,
    payload: FeedbackAdminUpdate,
    db: Session = Depends(get_db),
) -> FeedbackPublic:
    fb = FeedbackRepository(db).get_by_id(feedback_id)
    if fb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="反馈不存在")
    fb.status = payload.status
    if payload.admin_reply is not None:
        fb.admin_reply = payload.admin_reply.strip() or None
    fb = FeedbackRepository(db).save(fb)
    return FeedbackPublic.model_validate(fb)
