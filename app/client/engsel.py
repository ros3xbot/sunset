import os
import json
import uuid
import requests
from datetime import datetime, timezone

from app.config.theme_config import get_theme
from app.client.encrypt import (
    encryptsign_xdata,
    java_like_timestamp,
    decrypt_xdata,
    API_KEY,
)

BASE_API_URL = os.getenv("BASE_API_URL")
if not BASE_API_URL:
    raise ValueError("BASE_API_URL environment variable not set")
UA = os.getenv("UA")


def print_with_border(title: str, content: str):
    theme = get_theme()
    border_char = theme.get("border_char", "─")
    width = max(len(title), len(content)) + 4
    top = border_char * width
    print(top)
    print(f"{title.center(width)}")
    print(border_char * width)
    print(content)
    print(top)


def send_api_request(api_key: str, path: str, payload_dict: dict, id_token: str, method: str = "POST"):
    encrypted_payload = encryptsign_xdata(
        api_key=api_key,
        method=method,
        path=path,
        id_token=id_token,
        payload=payload_dict,
    )

    xtime = int(encrypted_payload["encrypted_body"]["xtime"])
    now = datetime.now(timezone.utc).astimezone()
    sig_time_sec = xtime // 1000

    body = encrypted_payload["encrypted_body"]
    x_sig = encrypted_payload["x_signature"]

    headers = {
        "host": BASE_API_URL.replace("https://", ""),
        "content-type": "application/json; charset=utf-8",
        "user-agent": UA,
        "x-api-key": API_KEY,
        "authorization": f"Bearer {id_token}",
        "x-hv": "v3",
        "x-signature-time": str(sig_time_sec),
        "x-signature": x_sig,
        "x-request-id": str(uuid.uuid4()),
        "x-request-at": java_like_timestamp(now),
        "x-version-app": "8.9.1",
    }

    url = f"{BASE_API_URL}/{path}"
    resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)

    try:
        return decrypt_xdata(api_key, json.loads(resp.text))
    except Exception as e:
        print_with_border("ERROR", f"Gagal decrypt response: {e}")
        return {"error": str(e), "raw": resp.text}


def get_profile(api_key: str, access_token: str, id_token: str) -> dict:
    path = "api/v8/profile"
    raw_payload = {
        "access_token": access_token,
        "app_version": "8.9.1",
        "is_enterprise": False,
        "lang": "en",
    }
    return send_api_request(api_key, path, raw_payload, id_token, "POST").get("data")


def get_balance(api_key: str, id_token: str) -> dict | None:
    path = "api/v8/packages/balance-and-credit"
    raw_payload = {"is_enterprise": False, "lang": "en"}
    res = send_api_request(api_key, path, raw_payload, id_token, "POST")
    if "data" in res and "balance" in res["data"]:
        return res["data"]["balance"]
    print_with_border("ERROR", f"Balance error: {res.get('error', 'Unknown error')}")
    return None


def get_family(api_key: str, tokens: dict, family_code: str,
               is_enterprise: bool | None = None,
               migration_type: str | None = None) -> dict | None:
    is_enterprise_list = [False, True] if is_enterprise is None else [is_enterprise]
    migration_type_list = ["NONE", "PRE_TO_PRIOH", "PRIOH_TO_PRIO", "PRIO_TO_PRIOH"] if migration_type is None else [migration_type]
    path = "api/v8/xl-stores/options/list"
    id_token = tokens.get("id_token")

    for mt in migration_type_list:
        for ie in is_enterprise_list:
            payload_dict = {
                "is_show_tagging_tab": True,
                "is_dedicated_event": True,
                "is_transaction_routine": False,
                "migration_type": mt,
                "package_family_code": family_code,
                "is_autobuy": False,
                "is_enterprise": ie,
                "is_pdlp": True,
                "referral_code": "",
                "is_migration": False,
                "lang": "en",
            }
            res = send_api_request(api_key, path, payload_dict, id_token, "POST")
            if res.get("status") == "SUCCESS":
                return res["data"]
    print_with_border("ERROR", f"Family data not found for {family_code}")
    return None


def get_families(api_key: str, tokens: dict, package_category_code: str) -> dict | None:
    path = "api/v8/xl-stores/families"
    payload_dict = {
        "migration_type": "",
        "is_enterprise": False,
        "is_shareable": False,
        "package_category_code": package_category_code,
        "with_icon_url": True,
        "is_migration": False,
        "lang": "en",
    }
    res = send_api_request(api_key, path, payload_dict, tokens["id_token"], "POST")
    if res.get("status") != "SUCCESS":
        print_with_border("ERROR", f"Families error for {package_category_code}")
        return None
    return res["data"]


def get_package(api_key: str, tokens: dict,
                package_option_code: str,
                package_family_code: str = "",
                package_variant_code: str = "") -> dict | None:
    path = "api/v8/xl-stores/options/detail"
    raw_payload = {
        "is_transaction_routine": False,
        "migration_type": "NONE",
        "package_family_code": package_family_code,
        "family_role_hub": "",
        "is_autobuy": False,
        "is_enterprise": False,
        "is_shareable": False,
        "is_migration": False,
        "lang": "id",
        "package_option_code": package_option_code,
        "is_upsell_pdp": False,
        "package_variant_code": package_variant_code,
    }
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    if "data" not in res:
        print_with_border("ERROR", f"Package error for {package_option_code}")
        return None
    return res["data"]


def get_addons(api_key: str, tokens: dict, package_option_code: str) -> dict | None:
    path = "api/v8/xl-stores/options/addons-pinky-box"
    raw_payload = {"is_enterprise": False, "lang": "en", "package_option_code": package_option_code}
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    if "data" not in res:
        print_with_border("ERROR", f"Addons error for {package_option_code}")
        return None
    return res["data"]


def intercept_page(api_key: str, tokens: dict, option_code: str, is_enterprise: bool = False):
    path = "misc/api/v8/utility/intercept-page"
    raw_payload = {"is_enterprise": is_enterprise, "lang": "en", "package_option_code": option_code}
    return send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")


def login_info(api_key: str, tokens: dict, is_enterprise: bool = False) -> dict | None:
    path = "api/v8/auth/login"
    raw_payload = {
        "access_token": tokens["access_token"],
        "is_enterprise": is_enterprise,
        "lang": "en",
    }
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    if "data" not in res:
        print_with_border("ERROR", f"Login info error: {res.get('error', 'Unknown error')}")
        return None
    return res["data"]


def get_package_details(api_key: str, tokens: dict,
                        family_code: str, variant_code: str, option_order: int,
                        is_enterprise: bool | None = None,
                        migration_type: str | None = None) -> dict | None:
    family_data = get_family(api_key, tokens, family_code, is_enterprise, migration_type)
    if not family_data:
        print_with_border("ERROR", f"Family data error for {family_code}")
        return None
    option_code = None
    for variant in family_data.get("package_variants", []):
        if variant["package_variant_code"] == variant_code:
            for option in variant.get("package_options", []):
                if option["order"] == option_order:
                    option_code = option["package_option_code"]
                    break
    if not option_code:
        print_with_border("ERROR", "Option code not found")
        return None
    package_details_data = get_package(api_key, tokens, option_code)
    if not package_details_data:
        print_with_border("ERROR", "Failed to get package details")
        return None
    return package_details_data


def get_notifications(api_key: str, tokens: dict):
    path = "api/v8/notification-non-grouping"
    raw_payload = {"is_enterprise": False, "lang": "en"}
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    if isinstance(res, dict) and res.get("status") != "SUCCESS":
        print_with_border("ERROR", f"Notifications error: {res.get('error', 'Unknown error')}")
        return None
    return res


def get_notification_detail(api_key: str, tokens: dict, notification_id: str):
    path = "api/v8/notification/detail"
    raw_payload = {"is_enterprise": False, "lang": "en", "notification_id": notification_id}
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    if isinstance(res, dict) and res.get("status") != "SUCCESS":
        print_with_border("ERROR", f"Notification detail error: {res.get('error', 'Unknown error')}")
        return None
    return res


def get_pending_transaction(api_key: str, tokens: dict) -> dict | None:
    path = "api/v8/profile"
    raw_payload = {"is_enterprise": False, "lang": "en"}
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    if res.get("status") != "SUCCESS":
        print_with_border("ERROR", "Failed to get pending transactions")
        return None
    data = res.get("data", {})
    if not data or "pending_payment" not in data:
        print_with_border("INFO", "No pending transactions found")
        return None
    return data


def get_transaction_history(api_key: str, tokens: dict) -> dict | None:
    path = "payments/api/v8/transaction-history"
    raw_payload = {"is_enterprise": False, "lang": "en"}
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    if res.get("status") != "SUCCESS":
        print_with_border("ERROR", "Failed to get transaction history")
        return None
    data = res.get("data", {})
    if not data or "list" not in data:
        print_with_border("INFO", "No transaction history found")
        return None
    return data


def get_tiering_info(api_key: str, tokens: dict) -> dict:
    path = "gamification/api/v8/loyalties/tiering/info"
    raw_payload = {"is_enterprise": False, "lang": "en"}
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    if not res or res.get("status") != "SUCCESS":
        print_with_border("ERROR", "Failed to get tiering info")
        return {}
    return res.get("data", {})


def unsubscribe(api_key: str, tokens: dict,
                quota_code: str, product_domain: str, product_subscription_type: str) -> bool:
    path = "api/v8/packages/unsubscribe"
    raw_payload = {
        "product_subscription_type": product_subscription_type,
        "quota_code": quota_code,
        "product_domain": product_domain,
        "is_enterprise": False,
        "unsubscribe_reason_code": "",
        "lang": "en",
        "family_member_id": "",
    }
    try:
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
        if res and res.get("code") == "000":
            print_with_border("INFO", f"Successfully unsubscribed quota {quota_code}")
            return True
        print_with_border("ERROR", f"Failed to unsubscribe quota {quota_code}")
        return False
    except Exception as e:
        print_with_border("ERROR", f"Exception: {e}")
        return False


def dashboard_segments(api_key: str, tokens: dict) -> dict:
    path = "dashboard/api/v8/segments"
    raw_payload = {"access_token": tokens["access_token"]}
    return send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")


def dash_segments(api_key: str, id_token: str, access_token: str, balance: int = 0) -> dict | None:
    path = "dashboard/api/v8/segments"
    payload = {
        "access_token": access_token,
        "app_version": "8.9.1",
        "current_balance": balance,
        "family_plan_role": "NO_ROLE",
        "is_enterprise": False,
        "lang": "id",
        "manufacturer_name": "samsung",
        "model_name": "SM-N935F",
    }

    try:
        res = send_api_request(api_key, path, payload, id_token, "POST")
    except Exception as e:
        print_with_border("ERROR", f"Failed to send segments request: {e}")
        return None

    if not (isinstance(res, dict) and "data" in res):
        err = res.get("error", "Unknown error") if isinstance(res, dict) else res
        print_with_border("ERROR", f"Segments response error: {err}")
        return None

    data = res["data"]

    loyalty_data = data.get("loyalty", {}).get("data", {})
    loyalty_info = {
        "current_point": loyalty_data.get("current_point", 0),
        "tier_name": loyalty_data.get("detail_tier", {}).get("name", ""),
    }

    notifications = data.get("notification", {}).get("data", [])

    sfy_data = data.get("special_for_you", {}).get("data", {})
    sfy_banners = sfy_data.get("banners", [])
    special_packages = []

    for pkg in sfy_banners:
        try:
            if not pkg.get("action_param"):
                continue
            kuota_total = sum(
                int(benefit.get("total", 0))
                for benefit in pkg.get("benefits", [])
                if benefit.get("data_type") == "DATA"
            )
            kuota_gb = kuota_total / (1024 ** 3)
            original_price = int(pkg.get("original_price", 0))
            discounted_price = int(pkg.get("discounted_price", original_price))
            diskon_percent = int(round((original_price - discounted_price) / original_price * 100)) if original_price else 0

            formatted_pkg = {
                "name": f"{pkg.get('family_name', '')} ({pkg.get('title', '')}) {pkg.get('validity', '')}",
                "kode_paket": pkg.get("action_param", ""),
                "original_price": original_price,
                "diskon_price": discounted_price,
                "diskon_percent": diskon_percent,
                "kuota_gb": kuota_gb,
            }
            special_packages.append(formatted_pkg)
        except Exception as e:
            print_with_border("WARN", f"Failed to parse SFY package: {e}")
            continue

    return {
        "loyalty": loyalty_info,
        "notification": notifications,
        "special_packages": special_packages,
    }


def get_quota(api_key: str, id_token: str) -> dict | None:
    path = "api/v8/packages/quota-summary"
    payload = {"is_enterprise": False, "lang": "en"}
    try:
        res = send_api_request(api_key, path, payload, id_token, "POST")
    except Exception as e:
        print_with_border("ERROR", f"Failed quota request: {e}")
        return None
    if isinstance(res, dict):
        quota = res.get("data", {}).get("quota", {}).get("data")
        if quota:
            return {
                "remaining": quota.get("remaining", 0),
                "total": quota.get("total", 0),
                "has_unlimited": quota.get("has_unlimited", False),
            }
    print_with_border("INFO", "No quota data found")
    return None
