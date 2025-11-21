import json
from app.client.engsel import send_api_request
from app.client.encrypt import encrypt_circle_msisdn
from app.menus.util import live_loading, print_error, print_success, print_panel
from app.config.theme_config import get_theme


def get_group_data(api_key: str, tokens: dict) -> dict:
    path = "family-hub/api/v8/groups/status"
    raw_payload = {"is_enterprise": False, "lang": "en"}
    with live_loading("👥 Fetching group detail...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    if not res or res.get("status") != "SUCCESS":
        print_error("❌", f"Failed to fetch group detail: {res.get('error', 'Unknown error')}")
        print_panel("📑 Response", json.dumps(res, indent=2))
    return res


def get_group_members(api_key: str, tokens: dict, group_id: str) -> dict:
    path = "family-hub/api/v8/members/info"
    raw_payload = {"group_id": group_id, "is_enterprise": False, "lang": "en"}
    with live_loading(f"👥 Fetching members for group {group_id}...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    return res


def validate_circle_member(api_key: str, tokens: dict, msisdn: str) -> dict:
    path = "family-hub/api/v8/members/validate"
    encrypted_msisdn = encrypt_circle_msisdn(api_key, msisdn)
    raw_payload = {"msisdn": encrypted_msisdn, "is_enterprise": False, "lang": "en"}
    with live_loading(f"🔍 Validating member {msisdn}...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    return res


def invite_circle_member(api_key: str, tokens: dict, msisdn: str, name: str,
                         group_id: str, member_id_parent: str) -> dict:
    path = "family-hub/api/v8/members/invite"
    encrypted_msisdn = encrypt_circle_msisdn(api_key, msisdn)
    raw_payload = {
        "access_token": tokens["access_token"],
        "group_id": group_id,
        "is_enterprise": False,
        "members": [{"msisdn": encrypted_msisdn, "name": name}],
        "lang": "en",
        "member_id_parent": member_id_parent,
    }
    with live_loading(f"📩 Inviting {msisdn} to Circle...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    return res


def remove_circle_member(api_key: str, tokens: dict, member_id: str,
                         group_id: str, member_id_parent: str,
                         is_last_member: bool = False) -> dict:
    path = "family-hub/api/v8/members/remove"
    raw_payload = {
        "member_id": member_id,
        "group_id": group_id,
        "is_enterprise": False,
        "is_last_member": is_last_member,
        "lang": "en",
        "member_id_parent": member_id_parent,
    }
    with live_loading(f"🗑️ Removing member {member_id}...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    return res


def accept_circle_invitation(api_key: str, tokens: dict, group_id: str, member_id: str) -> dict:
    path = "family-hub/api/v8/groups/accept-invitation"
    raw_payload = {
        "access_token": tokens["access_token"],
        "group_id": group_id,
        "member_id": member_id,
        "is_enterprise": False,
        "lang": "en",
    }
    with live_loading(f"✅ Accepting invitation to Circle {group_id}...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    return res


def create_circle(api_key: str, tokens: dict, parent_name: str,
                  group_name: str, member_msisdn: str, member_name: str) -> dict:
    path = "family-hub/api/v8/groups/create"
    raw_payload = {
        "access_token": tokens["access_token"],
        "parent_name": parent_name,
        "group_name": group_name,
        "is_enterprise": False,
        "members": [{"msisdn": encrypt_circle_msisdn(api_key, member_msisdn), "name": member_name}],
        "lang": "en",
    }
    with live_loading(f"➕ Creating Circle with member {member_msisdn}...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    return res


def spending_tracker(api_key: str, tokens: dict, parent_subs_id: str, family_id: str) -> dict:
    path = "gamification/api/v8/family-hub/spending-tracker"
    raw_payload = {"is_enterprise": False, "parent_subs_id": parent_subs_id, "family_id": family_id, "lang": "en"}
    with live_loading("💸 Fetching spending tracker...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    return res


def get_bonus_data(api_key: str, tokens: dict, parent_subs_id: str, family_id: str) -> dict:
    path = "gamification/api/v8/family-hub/bonus/list"
    raw_payload = {"is_enterprise": False, "parent_subs_id": parent_subs_id, "family_id": family_id, "lang": "en"}
    with live_loading("🎁 Fetching bonus data...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    return res
