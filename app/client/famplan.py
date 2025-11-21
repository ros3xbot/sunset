import json
from app.client.engsel import send_api_request
from app.menus.util import format_quota_byte, live_loading, print_error, print_success, print_panel
from app.config.theme_config import get_theme


def get_family_data(api_key: str, tokens: dict) -> dict:
    path = "sharings/api/v8/family-plan/member-info"
    raw_payload = {"group_id": 0, "is_enterprise": False, "lang": "en"}

    with live_loading("👨‍👩‍👧 Fetching family data...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    if not res or res.get("status") != "SUCCESS":
        print_error("❌ Family", f"Failed to fetch family data: {res.get('error', 'Unknown error')}")
        print_panel("📑 Response", json.dumps(res, indent=2))
    return res


def validate_msisdn(api_key: str, tokens: dict, msisdn: str) -> dict:
    path = "api/v8/auth/check-dukcapil"
    raw_payload = {
        "with_bizon": True,
        "with_family_plan": True,
        "is_enterprise": False,
        "with_optimus": True,
        "lang": "en",
        "msisdn": msisdn,
        "with_regist_status": True,
        "with_enterprise": True,
    }

    with live_loading(f"🔍 Validating msisdn {msisdn}...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    if not res or res.get("status") != "SUCCESS":
        print_error("❌ Validation", f"Failed to validate {msisdn}")
        print_panel("📑 Response", json.dumps(res, indent=2))
    return res


def change_member(api_key: str, tokens: dict, parent_alias: str, alias: str,
                  slot_id: int, family_member_id: str, new_msisdn: str) -> dict:
    path = "sharings/api/v8/family-plan/change-member"
    raw_payload = {
        "parent_alias": parent_alias,
        "is_enterprise": False,
        "slot_id": slot_id,
        "alias": alias,
        "lang": "en",
        "msisdn": new_msisdn,
        "family_member_id": family_member_id,
    }

    with live_loading(f"🔄 Assigning slot {slot_id} to {new_msisdn}...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    if not res or res.get("status") != "SUCCESS":
        print_error("❌ Change Member", f"Failed to assign slot {slot_id} to {new_msisdn}")
        print_panel("📑 Response", json.dumps(res, indent=2))
    return res


def remove_member(api_key: str, tokens: dict, family_member_id: str) -> dict:
    path = "sharings/api/v8/family-plan/remove-member"
    raw_payload = {"is_enterprise": False, "family_member_id": family_member_id, "lang": "en"}

    with live_loading(f"🗑️ Removing family member {family_member_id}...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    if not res or res.get("status") != "SUCCESS":
        print_error("❌ Remove Member", f"Failed to remove family member {family_member_id}")
        print_panel("📑 Response", json.dumps(res, indent=2))
    return res


def set_quota_limit(api_key: str, tokens: dict,
                    original_allocation: int, new_allocation: int,
                    family_member_id: str) -> dict:
    path = "sharings/api/v8/family-plan/allocate-quota"
    raw_payload = {
        "is_enterprise": False,
        "member_allocations": [{
            "new_text_allocation": 0,
            "original_text_allocation": 0,
            "original_voice_allocation": 0,
            "original_allocation": original_allocation,
            "new_voice_allocation": 0,
            "message": "",
            "new_allocation": new_allocation,
            "family_member_id": family_member_id,
            "status": "",
        }],
        "lang": "en",
    }

    formatted_new_allocation = format_quota_byte(new_allocation)

    with live_loading(f"📊 Setting quota limit for {family_member_id} to {formatted_new_allocation} MB...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    if not res or res.get("status") != "SUCCESS":
        print_error("❌ Quota Limit", f"Failed to set quota for {family_member_id}")
        print_panel("📑 Response", json.dumps(res, indent=2))
    else:
        print_success("✅ Quota Limit", f"Quota for {family_member_id} set to {formatted_new_allocation} MB")
    return res

