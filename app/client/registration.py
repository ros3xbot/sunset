import json
from app.client.engsel import send_api_request
from app.menus.util import live_loading
from app.config.theme_config import get_theme


def validate_puk(api_key: str, msisdn: str, puk: str) -> dict | None:
    path = "api/v8/infos/validate-puk"
    raw_payload = {
        "is_enterprise": False,
        "puk": puk,
        "is_enc": False,
        "msisdn": msisdn,
        "lang": "en",
    }

    with live_loading(f"🔐 Validating PUK for {msisdn}...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, "", "POST")

    if not res or res.get("status") != "SUCCESS":
        return None
    return res


def dukcapil(api_key: str, msisdn: str, kk: str, nik: str) -> dict | None:
    path = "api/v8/auth/regist/dukcapil"
    raw_payload = {
        "msisdn": msisdn,
        "kk": kk,
        "nik": nik,
        "lang": "en",
    }

    with live_loading(f"🪪 Validating Dukcapil for {msisdn}...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, "", "POST")

    if not res or res.get("status") != "SUCCESS":
        return None
    return res
