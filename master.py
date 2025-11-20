from dotenv import load_dotenv

from app.service.git import check_for_updates, ensure_git
load_dotenv()

import sys, json
from datetime import datetime
from app.menus.util import clear_screen, pause
from app.client.engsel import get_balance, get_tiering_info, get_quota, dashboard_segments
from app.client.famplan import validate_msisdn
from app.client.registration import dukcapil
from app.service.auth import AuthInstance
from app.service.sentry import enter_sentry_mode
from app.menus.payment import show_transaction_history
from app.menus.bookmark import show_bookmark_menu
from app.menus.account import show_account_menu
from app.menus.package import fetch_my_packages, get_packages_by_family, show_package_details
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.menus.purchase import purchase_by_family
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.menus.notification import show_notification_menu
from app.menus.store.segments import show_store_segments_menu
from app.menus.store.search import show_family_list_menu, show_store_packages_menu
from app.menus.store.redemables import show_redeemables_menu
from app.menus.info import show_info_menu
from app.menus.family_grup import show_family_grup_menu
from app.menus.theme import show_theme_menu

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD
from datetime import datetime
import random

console = Console()

def show_main_menu(profile, display_quota, dashboard_segments):
    console.clear()

    expired_at_dt = datetime.fromtimestamp(profile["balance_expired_at"]).strftime("%Y-%m-%d %H:%M:%S")
    pulsa_str = f"{profile['balance']:,}"

    # Panel informasi akun
    info_table = Table.grid(padding=(0, 1))
    info_table.add_column(justify="left", style="cyan")
    info_table.add_column(justify="left", style="white")

    info_table.add_row("📞 Nomor", f": [bold]{profile['number']}[/]")
    info_table.add_row("🧾 Type", f": {profile['subscription_type']} ({profile['subscriber_id']})")
    info_table.add_row("💰 Pulsa", f": Rp [green]{pulsa_str}[/]")
    info_table.add_row("📊 Kuota", f": [yellow]{display_quota}[/]")
    info_table.add_row("🏅 Tiering", f": {profile['point_info']}")
    info_table.add_row("⏳ Masa Aktif", f": {expired_at_dt}")

    console.print(
        Panel(
            info_table,
            title="[bold magenta]✨ Informasi Akun ✨[/]",
            title_align="center",
            border_style="bright_blue",
            padding=(1, 2),
            expand=True
        )
    )

    # Paket spesial preview
    special_packages = segments.get("special_packages", [])
    if special_packages:
        best = random.choice(special_packages)
        name = best.get("name", "-")
        diskon_percent = best.get("diskon_percent", 0)
        diskon_price = best.get("diskon_price", 0)
        original_price = best.get("original_price", 0)
        kuota_gb = best.get("kuota_gb", 0)

        special_text = (
            f"[bold red]🔥🔥🔥 Paket Spesial Untukmu 🔥🔥🔥[/]\n\n"
            f"[cyan]{name}[/] ({kuota_gb} GB)\n"
            f"Diskon {diskon_percent}% 💸 "
            f"[strike]Rp {original_price:,}[/strike] ➡️ [green]Rp {diskon_price:,}[/]"
        )

        console.print(
            Panel(
                Align.center(special_text),
                border_style="red",
                padding=(1, 2),
                expand=True
            )
        )

    # Menu utama dengan MINIMAL_DOUBLE_HEAD
    menu_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
    menu_table.add_column("Kode", justify="right", style="bold cyan", width=6)
    menu_table.add_column("Aksi", style="white")

    menu_table.add_row("1", "🔐 Login/Ganti akun")
    menu_table.add_row("2", "📑 Lihat Paket Saya")
    menu_table.add_row("3", "🔥 Beli Paket HOT")
    menu_table.add_row("4", "🔥 Beli Paket HOT-2")
    menu_table.add_row("5", "🔍 Beli Paket Berdasarkan Option Code")
    menu_table.add_row("6", "🔍 Beli Paket Berdasarkan Family Code")
    menu_table.add_row("7", "🛒 Beli Semua Paket di Family Code")
    menu_table.add_row("8", "📜 Riwayat Transaksi")
    menu_table.add_row("9", "⭐ Family Plan/Akrab Organizer")
    menu_table.add_row("10", "👥 Circle")
    menu_table.add_row("11", "🎁 Paket Spesial For You")  # shortcut resmi
    menu_table.add_row("12", "🏬 Store Segments")
    menu_table.add_row("13", "📂 Store Family List")
    menu_table.add_row("14", "📦 Store Packages")
    menu_table.add_row("15", "🎁 Redeemables")
    menu_table.add_row("00", "⭐ Bookmark Paket")
    menu_table.add_row("66", "💾 Simpan/Kelola Family Code")
    menu_table.add_row("77", "📢 Info Unlock Code")
    menu_table.add_row("88", "🎨 Ganti Tema CLI")
    menu_table.add_row("99", "⛔ Tutup aplikasi")

    console.print(
        Panel(
            menu_table,
            title="[bold magenta]✨ Menu Utama ✨[/]",
            title_align="center",
            border_style="bright_blue",
            padding=(0, 1),
            expand=True
        )
    )

show_menu = True
def main():
    ensure_git()
    while True:
        active_user = AuthInstance.get_active_user()

        # Logged in
        if active_user is not None:
            balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
            balance_remaining = balance.get("remaining")
            balance_expired_at = balance.get("expired_at")
            
            point_info = "Points: N/A | Tier: N/A"
            
            if active_user["subscription_type"] == "PREPAID":
                tiering_data = get_tiering_info(AuthInstance.api_key, active_user["tokens"])
                tier = tiering_data.get("tier", 0)
                current_point = tiering_data.get("current_point", 0)
                point_info = f"Points: {current_point} | Tier: {tier}"
            
            profile = {
                "number": active_user["number"],
                "subscriber_id": active_user["subscriber_id"],
                "subscription_type": active_user["subscription_type"],
                "balance": balance_remaining,
                "balance_expired_at": balance_expired_at,
                "point_info": point_info
            }

            show_main_menu(profile)

            choice = input("Pilih menu: ")
            # Testing shortcuts
            if choice.lower() == "t":
                pause()
            elif choice == "1":
                selected_user_number = show_account_menu()
                if selected_user_number:
                    AuthInstance.set_active_user(selected_user_number)
                else:
                    print("No user selected or failed to load user.")
                continue
            elif choice == "2":
                fetch_my_packages()
                continue
            elif choice == "3":
                show_hot_menu()
            elif choice == "4":
                show_hot_menu2()
            elif choice == "5":
                option_code = input("Enter option code (or '99' to cancel): ")
                if option_code == "99":
                    continue
                show_package_details(
                    AuthInstance.api_key,
                    active_user["tokens"],
                    option_code,
                    False
                )
            elif choice == "6":
                family_code = input("Enter family code (or '99' to cancel): ")
                if family_code == "99":
                    continue
                get_packages_by_family(family_code)
            elif choice == "7":
                family_code = input("Enter family code (or '99' to cancel): ")
                if family_code == "99":
                    continue

                start_from_option = input("Start purchasing from option number (default 1): ")
                try:
                    start_from_option = int(start_from_option)
                except ValueError:
                    start_from_option = 1

                use_decoy = input("Use decoy package? (y/n): ").lower() == 'y'
                pause_on_success = input("Pause on each successful purchase? (y/n): ").lower() == 'y'
                delay_seconds = input("Delay seconds between purchases (0 for no delay): ")
                try:
                    delay_seconds = int(delay_seconds)
                except ValueError:
                    delay_seconds = 0
                purchase_by_family(
                    family_code,
                    use_decoy,
                    pause_on_success,
                    delay_seconds,
                    start_from_option
                )
            elif choice == "8":
                show_transaction_history(AuthInstance.api_key, active_user["tokens"])
            elif choice == "9":
                show_family_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "10":
                show_circle_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "11":
                input_11 = input("Is enterprise store? (y/n): ").lower()
                is_enterprise = input_11 == 'y'
                show_store_segments_menu(is_enterprise)
            elif choice == "12":
                input_12_1 = input("Is enterprise? (y/n): ").lower()
                is_enterprise = input_12_1 == 'y'
                show_family_list_menu(profile['subscription_type'], is_enterprise)
            elif choice == "13":
                input_13_1 = input("Is enterprise? (y/n): ").lower()
                is_enterprise = input_13_1 == 'y'
                
                show_store_packages_menu(profile['subscription_type'], is_enterprise)
            elif choice == "14":
                input_14_1 = input("Is enterprise? (y/n): ").lower()
                is_enterprise = input_14_1 == 'y'
                
                show_redeemables_menu(is_enterprise)
            elif choice == "00":
                show_bookmark_menu()
            elif choice == "66":
                show_family_grup_menu()
            elif choice == "77":
                show_info_menu()
            elif choice == "88":
                show_theme_menu()
            elif choice == "99":
                print("Exiting the application.")
                sys.exit(0)
            elif choice.lower() == "r":
                msisdn = input("Enter msisdn (628xxxx): ")
                nik = input("Enter NIK: ")
                kk = input("Enter KK: ")
                
                res = dukcapil(
                    AuthInstance.api_key,
                    msisdn,
                    kk,
                    nik,
                )
                print(json.dumps(res, indent=2))
                pause()
            elif choice.lower() == "v":
                msisdn = input("Enter the msisdn to validate (628xxxx): ")
                res = validate_msisdn(
                    AuthInstance.api_key,
                    active_user["tokens"],
                    msisdn,
                )
                print(json.dumps(res, indent=2))
                pause()
            elif choice.lower() == "n":
                show_notification_menu()
            elif choice == "s":
                enter_sentry_mode()
            else:
                print("Invalid choice. Please try again.")
                pause()
        else:
            # Not logged in
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
            else:
                print("No user selected or failed to load user.")

if __name__ == "__main__":
    try:
        print("Checking for updates...")
        need_update = check_for_updates()
        if need_update:
            pause()

        main()
    except KeyboardInterrupt:
        print("\nExiting the application.")
    # except Exception as e:
    #     print(f"An error occurred: {e}")
