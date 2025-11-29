import json
import time
import uuid
import requests
from datetime import timezone, datetime

from app.client.encrypt import (
    API_KEY,
    build_encrypted_field,
    decrypt_xdata,
    encryptsign_xdata,
    get_x_signature_payment,
    java_like_timestamp,
)
from app.client.engsel import BASE_API_URL, UA, intercept_page, send_api_request
from app.type_dict import PaymentItem
from app.menus.util import live_loading, print_error, print_success, print_panel
from app.config.theme_config import get_theme


def settlement_balance(
    api_key: str,
    tokens: dict,
    items: list[PaymentItem],
    payment_for: str,
    ask_overwrite: bool,
    overwrite_amount: int = -1,
    token_confirmation_idx: int = 0,
    amount_idx: int = -1,
    topup_number: str = "",
    stage_token: str = "",
):
    if overwrite_amount == -1 and not ask_overwrite:
        print_error("⚠️ Ups", "Harus ada overwrite_amount atau flag ask_overwrite bro 🚨")
        return None

    token_confirmation = items[token_confirmation_idx]["token_confirmation"]
    payment_targets = ";".join([item["item_code"] for item in items])

    # Tentukan amount
    if overwrite_amount != -1:
        amount_int = overwrite_amount
    elif amount_idx == -1:
        amount_int = items[amount_idx]["item_price"]

    if ask_overwrite:
        print_panel("💰 Amount", f"Total {amount_int}. Masukin nominal baru kalo mau overwrite bro ✌️")
        amount_str = input("Enter buat skip & pake default: ")
        if amount_str != "":
            try:
                amount_int = int(amount_str)
            except ValueError:
                print_panel("⚠️ Ups", "Input overwrite ngaco, pake harga asli aja 🚨")

    intercept_page(api_key, tokens, items[0]["item_code"], False)

    # Ambil payment methods
    payment_path = "payments/api/v8/payment-methods-option"
    payment_payload = {
        "payment_type": "PURCHASE",
        "is_enterprise": False,
        "payment_target": items[token_confirmation_idx]["item_code"],
        "lang": "en",
        "is_referral": False,
        "token_confirmation": token_confirmation,
    }

    with live_loading("💳 Lagi ngumpulin payment methods bro...", get_theme()):
        payment_res = send_api_request(api_key, payment_path, payment_payload, tokens["id_token"], "POST")

    if payment_res.get("status") != "SUCCESS":
        print_panel("⚠️ Ups", "Gagal ambil payment methods bro 🚨")
        print_panel("📑 Response", json.dumps(payment_res, indent=2))
        return payment_res

    token_payment = payment_res["data"]["token_payment"]
    ts_to_sign = payment_res["data"]["timestamp"]

    # Build settlement payload
    path = "payments/api/v8/settlement-multipayment"
    settlement_payload = {...}  # sama kayak versi asli

    encrypted_payload = encryptsign_xdata(
        api_key=api_key,
        method="POST",
        path=path,
        id_token=tokens["id_token"],
        payload=settlement_payload,
    )

    xtime = int(encrypted_payload["encrypted_body"]["xtime"])
    sig_time_sec = xtime // 1000
    x_requested_at = datetime.fromtimestamp(sig_time_sec, tz=timezone.utc).astimezone()
    settlement_payload["timestamp"] = ts_to_sign

    body = encrypted_payload["encrypted_body"]
    x_sig = get_x_signature_payment(...)

    headers = {...}

    url = f"{BASE_API_URL}/{path}"
    with live_loading("📤 Lagi kirim settlement request bro...", get_theme()):
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)

    try:
        decrypted_body = decrypt_xdata(api_key, json.loads(resp.text))
        if decrypted_body.get("status") != "SUCCESS":
            print_panel("⚠️ Ups", "Settlement gagal bro 🚨")
            print_panel("📑 Response", json.dumps(decrypted_body, indent=2))
            return decrypted_body

        print_panel("✅ Mantap", "Pembelian sukses bro 🚀")
        print_panel("🧾 Purchase Result", json.dumps(decrypted_body, indent=2))
        return decrypted_body
    except Exception as e:
        print_panel("⚠️ Ups", f"Error decrypt: {e} 🤯")
        print_panel("📑 Raw Response", resp.text)
        return resp.text
