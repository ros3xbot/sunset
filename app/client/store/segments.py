import json
from app.client.engsel import send_api_request
from app.menus.util import live_loading, print_error, print_success, print_panel
from app.config.theme_config import get_theme


def get_segments(api_key: str, tokens: dict, is_enterprise: bool = False) -> dict | None:
    path = "api/v8/configs/store/segments"
    payload = {"is_enterprise": is_enterprise, "lang": "en"}

    with live_loading("📊 Fetching store segments...", get_theme()):
        res = send_api_request(api_key, path, payload, tokens["id_token"], "POST")

    if not res or res.get("status") != "SUCCESS":
        print_error("❌", "Failed to fetch segments.")
        print_panel("📑 Response", json.dumps(res, indent=2))
        return None

    print_success("✅", "Store segments fetched successfully")
    return res
