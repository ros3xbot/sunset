import json
from app.client.engsel import send_api_request
from app.menus.util import live_loading
from app.config.theme_config import get_theme


def get_redeemables(api_key: str, tokens: dict, is_enterprise: bool = False) -> dict | None:
    path = "api/v8/personalization/redeemables"
    payload = {"is_enterprise": is_enterprise, "lang": "en"}

    with live_loading("🎁 Fetching redeemables...", get_theme()):
        res = send_api_request(api_key, path, payload, tokens["id_token"], "POST")

    if not res or res.get("status") != "SUCCESS":
        return None

    return res
