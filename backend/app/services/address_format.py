from __future__ import annotations

from app.models.user_address import UserAddress


def format_address(addr: UserAddress) -> str:
    region = "".join(p for p in (addr.province, addr.city, addr.district) if p)
    if addr.poi_name and addr.detail:
        body = f"{addr.poi_name} {addr.detail}".strip()
    else:
        body = addr.detail
    if region and body.startswith(region):
        return body
    return f"{region}{body}".strip() if region else body

