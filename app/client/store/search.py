import json
from app.client.engsel import send_api_request
from app.menus.util import live_loading, print_error, print_success, print_panel
from app.config.theme_config import get_theme


def get_family_list(api_key: str, tokens: dict,
                    subs_type: str = "PREPAID",
                    is_enterprise: bool = False) -> dict | None:
    path = "api/v8/xl-stores/options/search/family-list"
    payload = {"is_enterprise": is_enterprise, "subs_type": subs_type, "lang": "en"}

    with live_loading("👨‍👩‍👧 Fetching family list...", get_theme()):
        res = send_api_request(api_key, path, payload, tokens["id_token"], "POST")

    if not res or res.get("status") != "SUCCESS":
        print_error("❌ Family List", "Failed to fetch family list.")
        print_panel("📑 Response", json.dumps(res, indent=2))
        return None

    print_success("✅ Family List", "Family list fetched successfully")
    return res


def get_store_packages(api_key: str, tokens: dict,
                       subs_type: str = "PREPAID",
                       is_enterprise: bool = False) -> dict | None:
    path = "api/v9/xl-stores/options/search"
    payload = {
        "is_enterprise": is_enterprise,
        "filters": [
            {"unit": "THOUSAND", "id": "FIL_SEL_P", "type": "PRICE", "items": []},
            {"unit": "GB", "id": "FIL_SEL_MQ", "type": "DATA_TYPE", "items": []},
            {"unit": "PACKAGE_NAME", "id": "FIL_PKG_N", "type": "PACKAGE_NAME",
             "items": [{"id": "", "label": ""}]},
            {"unit": "DAY", "id": "FIL_SEL_V", "type": "VALIDITY", "items": []},
        ],
        "substype": subs_type,
        "text_search": "",
        "lang": "en",
    }

    with live_loading("📦 Fetching store packages...", get_theme()):
        res = send_api_request(api_key, path, payload, tokens["id_token"], "POST")

    if not res or res.get("status") != "SUCCESS":
        print_error("❌ Store Packages", "Failed to fetch store packages.")
        print_panel("📑 Response", json.dumps(res, indent=2))
        return None

    print_success("✅ Store Packages", "Store packages fetched successfully")
    return res
