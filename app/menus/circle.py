from datetime import datetime
import json
from app.config.imports import *
from app.client.circle import (
    get_group_data,
    get_group_members,
    create_circle,
    validate_circle_member,
    invite_circle_member,
    remove_circle_member,
    accept_circle_invitation,
    spending_tracker,
    get_bonus_data,
)
from app.client.encrypt import decrypt_circle_msisdn


WIDTH = 55


def show_circle_creation(api_key: str, tokens: dict):
    clear_screen()
    theme = get_theme()

    console.print(Panel(
        Align.center("Create a new Circle", vertical="middle"),
        border_style=theme["border_info"],
        padding=(1, 2),
        expand=True
    ))

    parent_name = console.input(f"[{theme['text_sub']}]Enter your name (Parent):[/{theme['text_sub']}] ").strip()
    group_name = console.input(f"[{theme['text_sub']}]Enter Circle name:[/{theme['text_sub']}] ").strip()
    member_msisdn = console.input(f"[{theme['text_sub']}]Enter initial member's MSISDN (e.g., 6281234567890):[/{theme['text_sub']}] ").strip()
    member_name = console.input(f"[{theme['text_sub']}]Enter initial member's name:[/{theme['text_sub']}] ").strip()

    with live_loading("🔄 Creating circle...", theme):
        create_res = create_circle(api_key, tokens, parent_name, group_name, member_msisdn, member_name)

    res_text = Text()
    res_text.append("Server Response:\n", style="bold")
    res_text.append(json.dumps(create_res, indent=2), style=theme["text_body"])
    console.print(Panel(res_text, border_style=theme["border_primary"], expand=True))
    pause()


def show_bonus_list(api_key: str, tokens: dict, parent_subs_id: str, family_id: str):
    theme = get_theme()
    in_circle_bonus_menu = True

    while in_circle_bonus_menu:
        clear_screen()

        with live_loading("🔶 Fetching bonus data...", theme):
            bonus_data = get_bonus_data(api_key, tokens, parent_subs_id, family_id)

        if bonus_data.get("status") != "SUCCESS":
            print_panel("❌ Error", "Failed to fetch bonus data.")
            pause()
            return

        bonus_list = bonus_data.get("data", {}).get("bonuses", [])
        if not bonus_list:
            print_panel("ℹ️ Info", "No bonus data available.")
            pause()
            return

        console.print(Panel(
            Align.center("🎁 Circle Bonus List", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 1),
            expand=True
        ))

        # tampilkan bonus vertikal agar muat di layar kecil
        for idx, bonus in enumerate(bonus_list, start=1):
            bonus_name = bonus.get("name", "N/A")
            bonus_type = bonus.get("bonus_type", "N/A")
            action_type = bonus.get("action_type", "N/A")
            action_param = bonus.get("action_param", "N/A")
            if isinstance(action_param, (int, float)):
                action_param = get_rupiah(action_param)

            bonus_text = Text()
            bonus_text.append(f"{idx}. {bonus_name}\n", style="bold")
            bonus_text.append(f"Type: {bonus_type}\n", style=theme["text_body"])
            bonus_text.append(f"Action: {action_type}\n", style=theme["text_body"])
            bonus_text.append(f"Param: {action_param}\n", style=theme["text_sub"])

            console.print(Panel(bonus_text, border_style=theme["border_primary"], expand=True))

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=4)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Back[/]")
        console.print(Panel(nav_table, border_style=theme["border_info"], expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilih opsi:[/{theme['text_sub']}] ").strip()
        if choice == "00":
            in_circle_bonus_menu = False
        else:
            if not choice.isdigit():
                print_panel("⚠️ Error", "Invalid bonus number.")
                pause()
                continue

            bonus_number = int(choice)
            if bonus_number < 1 or bonus_number > len(bonus_list):
                print_panel("⚠️ Error", "Invalid bonus number.")
                pause()
                continue

            selected_bonus = bonus_list[bonus_number - 1]
            action_type = selected_bonus.get("action_type", "N/A")
            action_param = selected_bonus.get("action_param", "N/A")

            if action_type == "PLP":
                get_packages_by_family(action_param)
                pause()
            elif action_type == "PDP":
                show_package_details(api_key, tokens, action_param, False)
                pause()
            else:
                detail_text = Text()
                detail_text.append("Unhandled Action Type\n", style="bold")
                detail_text.append(f"Action type: {action_type}\nParam: {action_param}", style=theme["text_body"])
                console.print(Panel(detail_text, border_style=theme["border_info"], expand=True))
                pause()


def show_circle_info(api_key: str, tokens: dict):
    theme = get_theme()
    in_circle_menu = True
    user: dict = AuthInstance.get_active_user()
    my_msisdn = user.get("number", "")

    while in_circle_menu:
        clear_screen()
        with live_loading("🔄 Fetching circle data...", theme):
            group_res = get_group_data(api_key, tokens)

        if group_res.get("status") != "SUCCESS":
            print_panel("❌ Error", "Failed to fetch circle data.")
            pause()
            return "BACK"

        group_data = group_res.get("data", {})
        group_id = group_data.get("group_id", "")

        if group_id == "":
            console.print(Panel(
                Align.center("🚫 You are not part of any Circle.", vertical="middle"),
                border_style=theme["border_info"],
                padding=(1, 2),
                expand=True
            ))
            create_new = console.input(f"[{theme['text_sub']}]Create a new Circle? (y/n):[/{theme['text_sub']}] ").strip().lower()
            if create_new == "y":
                show_circle_creation(api_key, tokens)
                continue
            else:
                pause()
                return "BACK"

        if group_data.get("group_status") == "BLOCKED":
            print_panel("⚠️ Info", "This Circle is currently blocked.")
            pause()
            return "BACK"

        group_name = group_data.get("group_name", "N/A")
        owner_name = group_data.get("owner_name", "N/A")

        with live_loading("🔄 Fetching members...", theme):
            members_res = get_group_members(api_key, tokens, group_id)

        if members_res.get("status") != "SUCCESS":
            print_panel("❌ Error", "Failed to fetch circle members.")
            pause()
            return "BACK"

        members_data = members_res.get("data", {})
        members = members_data.get("members", [])
        if not members:
            print_panel("ℹ️ Info", "No members found in the Circle.")
            pause()
            return "BACK"

        parent_member_id = ""
        parent_subs_id = ""
        parrent_msisdn = ""
        for member in members:
            if member.get("member_role") == "PARENT":
                parent_member_id = member.get("member_id", "")
                parent_subs_id = member.get("subscriber_number", "")
                parrent_msisdn = decrypt_circle_msisdn(api_key, member.get("msisdn", ""))

        package = members_data.get("package", {})
        package_name = package.get("name", "N/A")
        benefit = package.get("benefit", {})
        allocation_byte = benefit.get("allocation", 0)
        remaining_byte = benefit.get("remaining", 0)

        formatted_allocation = format_quota_byte(allocation_byte)
        formatted_remaining = format_quota_byte(remaining_byte)

        with live_loading("🔄 Fetching spending tracker...", theme):
            spending_res = spending_tracker(api_key, tokens, parent_subs_id, group_id)

        if spending_res.get("status") != "SUCCESS":
            print_panel("❌ Error", "Failed to fetch spending tracker data.")
            pause()
            return "BACK"

        spending_data = spending_res.get("data", {})
        spend = spending_data.get("spend", 0)
        target = spending_data.get("target", 0)

        # Header Circle
        header_text = Text()
        header_text.append(f"Circle: {group_name}\n", style="bold")
        header_text.append(f"Owner: {owner_name} {parrent_msisdn}\n", style=theme["text_body"])
        header_text.append(f"Package: {package_name} | {formatted_remaining} / {formatted_allocation}\n", style=theme["text_body"])
        header_text.append(f"Spending: {get_rupiah(spend)} / {get_rupiah(target)}\n", style=theme["text_money"])

        console.print(Panel(header_text, border_style=theme["border_primary"], expand=True))

        # Tabel Members (vertikal agar muat di layar kecil)
        for idx, m in enumerate(members, start=1):
            msisdn = decrypt_circle_msisdn(api_key, m.get("msisdn", "")) or "<No Number>"
            me_mark = " (You)" if str(msisdn) == str(my_msisdn) else ""
            role = "Parent" if m.get("member_role") == "PARENT" else "Member"
            joined_str = datetime.fromtimestamp(m.get("join_date", 0)).strftime('%Y-%m-%d') if m.get("join_date") else "N/A"
            alloc = format_quota_byte(m.get("allocation", 0))
            used = format_quota_byte(max(m.get("allocation", 0) - m.get("remaining", 0), 0))
            usage_str = f"{used} / {alloc}"

            member_text = Text()
            member_text.append(f"{idx}. {m.get('member_name','N/A')} {me_mark}\n", style="bold")
            member_text.append(f"MSISDN: {msisdn}\n", style=theme["border_warning"])
            member_text.append(f"Role: {role}\n", style=theme["text_body"])
            member_text.append(f"Joined: {joined_str}\n", style=theme["border_info"])
            member_text.append(f"Slot: {m.get('slot_type','N/A')}\n", style=theme["text_body"])
            member_text.append(f"Status: {m.get('status','N/A')}\n", style=theme["text_sub"])
            member_text.append(f"Usage: {usage_str}\n", style=theme["text_body"])

            console.print(Panel(member_text, border_style=theme["border_info"], expand=True))

        # Navigasi
        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("1", "Invite Member to Circle")
        nav_table.add_row("del <num>", f"[{theme['text_err']}]Remove Member[/]")
        nav_table.add_row("acc <num>", "Accept Invitation")
        nav_table.add_row("2", "View Circle Bonus List")
        nav_table.add_row("00", f"[{theme['text_sub']}]Back to main menu[/]")

        console.print(Panel(nav_table, border_style=theme["border_primary"], expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilihan:[/{theme['text_sub']}] ").strip()
        if choice == "00":
            return "BACK"

        elif choice == "1":
            msisdn_to_invite = console.input(f"[{theme['text_sub']}]Enter MSISDN to invite:[/{theme['text_sub']}] ").strip()
            validate_res = validate_circle_member(api_key, tokens, msisdn_to_invite)
            if validate_res.get("status") == "SUCCESS":
                if validate_res.get("data", {}).get("response_code", "") != "200-2001":
                    print_panel("⚠️ Info", f"Cannot invite {msisdn_to_invite}: {validate_res.get('data', {}).get('message', 'Unknown error')}")
                    pause()
                    continue
            member_name = console.input(f"[{theme['text_sub']}]Enter member name:[/{theme['text_sub']}] ").strip()
            with live_loading("🔄 Sending invitation...", theme):
                invite_res = invite_circle_member(api_key, tokens, msisdn_to_invite, member_name, group_id, parent_member_id)
            if invite_res.get("status") == "SUCCESS" and invite_res.get("data", {}).get("response_code") == "200-00":
                print_panel("✅ Success", f"Invitation sent to {msisdn_to_invite}.")
            else:
                print_panel("❌ Error", f"Failed to invite {msisdn_to_invite}.")
            pause()

        elif choice.startswith("del "):
            try:
                member_number = int(choice.split(" ")[1])
                if member_number < 1 or member_number > len(members):
                    print_panel("❌ Error", "Invalid member number.")
                    pause()
                    continue
                member_to_remove = members[member_number - 1]
                if member_to_remove.get("member_role") == "PARENT":
                    print_panel("⚠️ Info", "Cannot remove the parent member.")
                    pause()
                    continue
                is_last_member = len(members) == 2
                if is_last_member:
                    print_panel("⚠️ Info", "Cannot remove the last member from the Circle.")
                    pause()
                    continue
                msisdn_to_remove = decrypt_circle_msisdn(api_key, member_to_remove.get("msisdn", ""))
                confirm = console.input(f"[{theme['text_sub']}]Remove {msisdn_to_remove}? (y/n):[/{theme['text_sub']}] ").strip().lower()
                if confirm != "y":
                    print_panel("ℹ️ Info", "Removal cancelled.")
                    pause()
                    continue
                with live_loading("🔄 Removing member...", theme):
                    remove_res = remove_circle_member(api_key, tokens, member_to_remove.get("member_id", ""), group_id, parent_member_id, is_last_member)
                if remove_res.get("status") == "SUCCESS":
                    res_text = Text()
                    res_text.append(f"{msisdn_to_remove} removed.\n", style="bold")
                    res_text.append(json.dumps(remove_res, indent=2), style=theme["text_body"])
                    console.print(Panel(res_text, border_style=theme["border_info"], expand=True))
                else:
                    print_panel("❌ Error", f"Error: {remove_res}")
            except ValueError:
                print_panel("⚠️ Error", "Invalid input format for deletion.")
            pause()

        elif choice.startswith("acc "):
            try:
                member_number = int(choice.split(" ")[1])
                if member_number < 1 or member_number > len(members):
                    print_panel("❌ Error", "Invalid member number.")
                    pause()
                    continue
                member_to_accept = members[member_number - 1]
                if member_to_accept.get("status") != "INVITED":
                    print_panel("⚠️ Info", "This member is not in an invited state.")
                    pause()
                    continue
                msisdn_to_accept = decrypt_circle_msisdn(api_key, member_to_accept.get("msisdn", ""))
                confirm = console.input(f"[{theme['text_sub']}]Accept invitation for {msisdn_to_accept}? (y/n):[/{theme['text_sub']}] ").strip().lower()
                if confirm != "y":
                    print_panel("ℹ️ Info", "Acceptance cancelled.")
                    pause()
                    continue
                with live_loading("🔄 Accepting invitation...", theme):
                    accept_res = accept_circle_invitation(api_key, tokens, group_id, member_to_accept.get("member_id", ""))
                if accept_res.get("status") == "SUCCESS":
                    res_text = Text()
                    res_text.append(f"Invitation for {msisdn_to_accept} accepted.\n", style="bold")
                    res_text.append(json.dumps(accept_res, indent=2), style=theme["text_body"])
                    console.print(Panel(res_text, border_style=theme["border_info"], expand=True))
                else:
                    print_panel("❌ Error", f"Error: {accept_res}")
            except ValueError:
                print_panel("⚠️ Error", "Invalid input format for acceptance.")
            pause()

        elif choice == "2":
            show_bonus_list(api_key, tokens, parent_subs_id, group_id)

