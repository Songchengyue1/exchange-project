from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

import bcrypt

from app.database import SessionLocal
from app.models.app_setting import AppSetting
from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.user import User

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_UPLOADS_DIR = _BACKEND_DIR / "uploads"
_SEED_IMAGES_DIR = _BACKEND_DIR / "seed_images"

# product_id -> 图片文件名（seed_images/ 与 uploads/ 使用同名）
DEMO_PRODUCT_IMAGES: list[tuple[int, str]] = [
    (1, "demo_p1_iphone.png"),
    (2, "demo_p2_macbook.png"),
    (3, "demo_p3_nike.png"),
    (4, "demo_p4_book.png"),
    (5, "demo_p5_desk.png"),
    (6, "demo_p6_switch.png"),
]

DEMO_PASSWORD = "demo123"


def _hash_password(password: str) -> str:
    """种子脚本用 bcrypt 直哈希，避免部分环境下 passlib 与 bcrypt 版本不兼容。"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

DEFAULT_CATEGORIES = [
    ("数码", 10),
    ("服饰", 20),
    ("图书", 30),
    ("家居", 40),
    ("其他", 99),
]


def seed_app_settings(db: Session) -> None:
    defaults = {
        "hot_rating_threshold": "4.5",
    }
    for key, value in defaults.items():
        if db.get(AppSetting, key) is None:
            db.add(AppSetting(key=key, value=value))


def seed_categories(db: Session) -> None:
    if db.execute(select(Category.id).limit(1)).first():
        return
    db.add_all([Category(name=n, sort_order=o) for n, o in DEFAULT_CATEGORIES])


def _get_or_create_user(
    db: Session,
    *,
    username: str,
    nickname: str,
    role: str = "user",
    rating_avg: float | None = None,
    phone: str | None = None,
) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if user is not None:
        return user
    user = User(
        username=username,
        password_hash=_hash_password(DEMO_PASSWORD),
        nickname=nickname,
        role=role,
        rating_avg=rating_avg,
        phone=phone,
    )
    db.add(user)
    db.flush()
    return user


def seed_demo_users_and_products(db: Session) -> None:
    """演示用户与商品（仅当尚无 demo_seller1 时写入）。"""
    if db.scalar(select(User.id).where(User.username == "demo_seller1")) is not None:
        return

    seller1 = _get_or_create_user(
        db,
        username="demo_seller1",
        nickname="阿杰",
        rating_avg=4.85,
        phone="13800001111",
    )
    seller2 = _get_or_create_user(
        db,
        username="demo_seller2",
        nickname="小雨",
        rating_avg=4.2,
        phone="13800002222",
    )
    _get_or_create_user(
        db,
        username="demo_buyer",
        nickname="买家小明",
        phone="13800003333",
    )

    cats = {c.name: c.id for c in db.scalars(select(Category)).all()}
    if not cats:
        seed_categories(db)
        db.flush()
        cats = {c.name: c.id for c in db.scalars(select(Category)).all()}

    demos: list[dict] = [
        {
            "seller": seller1,
            "category": "数码",
            "title": "iPhone 13 128G 蓝色",
            "description": "自用一年，电池健康 89%，无拆修，附原装充电线。",
            "price": 2899.00,
            "condition": "excellent",
            "trade_type": "both",
            "stock": 1,
            "status": "approved",
        },
        {
            "seller": seller1,
            "category": "数码",
            "title": "MacBook Air M1 8G+256G",
            "description": "轻度办公，键盘无油光，箱说齐全。",
            "price": 4500.00,
            "condition": "like_new",
            "trade_type": "shipping",
            "stock": 1,
            "status": "approved",
        },
        {
            "seller": seller2,
            "category": "服饰",
            "title": "Nike Air Force 1 42码",
            "description": "穿过几次，鞋底正常磨损，已清洗。",
            "price": 399.00,
            "condition": "good",
            "trade_type": "pickup",
            "stock": 1,
            "status": "approved",
        },
        {
            "seller": seller2,
            "category": "图书",
            "title": "算法导论（第三版）",
            "description": "专业课用书，少量笔记，无缺页。",
            "price": 58.00,
            "condition": "good",
            "trade_type": "both",
            "stock": 3,
            "status": "approved",
        },
        {
            "seller": seller1,
            "category": "家居",
            "title": "宜家 LINNMON 书桌 120cm",
            "description": "自提优先，桌腿可调，轻微使用痕迹。",
            "price": 120.00,
            "condition": "fair",
            "trade_type": "pickup",
            "stock": 1,
            "status": "approved",
        },
        {
            "seller": seller2,
            "category": "其他",
            "title": "Switch 游戏卡带合集（3张）",
            "description": "塞尔达、马里奥奥德赛、健身环，盒装齐全。",
            "price": 680.00,
            "condition": "like_new",
            "trade_type": "shipping",
            "stock": 1,
            "status": "approved",
        },
        {
            "seller": seller2,
            "category": "数码",
            "title": "索尼 WH-1000XM4 耳机",
            "description": "待审核示例商品，降噪正常。",
            "price": 899.00,
            "condition": "excellent",
            "trade_type": "both",
            "stock": 1,
            "status": "pending",
        },
    ]

    for item in demos:
        seller: User = item["seller"]
        cat_name: str = item["category"]
        db.add(
            Product(
                seller_id=seller.id,
                category_id=cats[cat_name],
                title=item["title"],
                description=item["description"],
                price=item["price"],
                condition=item["condition"],
                trade_type=item["trade_type"],
                stock=item["stock"],
                status=item["status"],
            )
        )

def seed_demo_product_images(db: Session, assets_dir: Path | None = None) -> None:
    """为演示商品复制封面图并写入 product_images（已有关联图的商品跳过）。"""
    root = assets_dir or _SEED_IMAGES_DIR
    _UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    for product_id, filename in DEMO_PRODUCT_IMAGES:
        has_image = db.scalar(
            select(ProductImage.id).where(ProductImage.product_id == product_id).limit(1)
        )
        if has_image is not None:
            continue

        src = root / filename
        if not src.is_file():
            continue

        dest = _UPLOADS_DIR / filename
        shutil.copy2(src, dest)
        db.add(
            ProductImage(
                product_id=product_id,
                path=f"/static/{filename}",
                sort_order=0,
            )
        )


def seed_admin_user(db: Session, username: str = "admin", password: str = "admin123") -> None:
    """可选：首次启动创建演示管理员（仅当不存在时）。"""
    exists = db.scalar(select(User.id).where(User.username == username))
    if exists is not None:
        return
    db.add(
        User(
            username=username,
            password_hash=_hash_password(password),
            nickname="管理员",
            role="admin",
        )
    )


def run_seed_data(
    include_demo_admin: bool = False,
    include_demo_products: bool = False,
    include_demo_images: bool = False,
    assets_dir: Path | None = None,
) -> None:
    with SessionLocal() as db:
        seed_app_settings(db)
        seed_categories(db)
        if include_demo_admin:
            seed_admin_user(db)
            db.flush()
        if include_demo_products:
            seed_demo_users_and_products(db)
            db.flush()
        if include_demo_images:
            seed_demo_product_images(db, assets_dir=assets_dir)
        db.commit()
