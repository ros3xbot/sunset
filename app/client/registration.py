import json
from app.client.engsel import send_api_request
from app.menus.util import live_loading, print_panel
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

    with live_loading(f"🔐 Lagi ngecek PUK buat {msisdn} bro...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, "", "POST")

    if not res or res.get("status") != "SUCCESS":
        print_panel("⚠️ Ups", f"Validasi PUK gagal buat {msisdn} 🚨")
        return None
    
    print_panel("✅ Mantap", f"PUK valid buat {msisdn} 🚀")
    return res


def dukcapil(api_key: str, msisdn: str, kk: str, nik: str) -> dict | None:
    path = "api/v8/auth/regist/dukcapil"
    raw_payload = {
        "msisdn": msisdn,
        "kk": kk,
        "nik": nik,
        "lang": "en",
    }

    with live_loading(f"🪪 Lagi ngecek Dukcapil buat {msisdn} bro...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, "", "POST")

    if not res or res.get("status") != "SUCCESS":
        print_panel("⚠️ Ups", f"Validasi Dukcapil gagal buat {msisdn} 🚨")
        return None
    
    print_panel("✅ Mantap", f"Dukcapil valid buat {msisdn} 🚀")
    return res
