from dotenv import load_dotenv
load_dotenv()

import sys, json, random
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

from app.service.git import check_for_updates, ensure_git
from app.menus.util import (
    clear_screen,
    clear_sc,
    pause,
    print_panel,
    print_error,
    print_warning,
    print_success,
    get_rupiah,
    live_loading,
)
from app.client.engsel import (
    get_balance,
    get_tiering_info,
    get_quota,
    dashboard_segments,
)
from app.client.famplan import validate_msisdn
from app.client.registration import dukcapil
from app.service.auth import AuthInstance
from app.service.sentry import enter_sentry_mode
from app.menus.payment import show_transaction_history
from app.menus.bookmark import show_bookmark_menu
from app.menus.account import show_account_menu
from app.menus.package import (
    fetch_my_packages,
    get_packages_by_family,
    show_package_details,
)
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
from app.config.theme_config import get_theme, get_theme_style

console = Console()


def show_main_menu(profile, display_quota, segments):
    clear_sc()
    theme = get_theme()

    expired_at_dt = datetime.fromtimestamp(profile["balance_expired_at"]).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    pulsa_str = get_rupiah(profile["balance"])

    # Panel informasi akun ✨
    info_table = Table.grid(padding=(0, 1))
    info_table.add_column(justify="left", style=get_theme_style("text_body"))
    info_table.add_column(justify="left", style=get_theme_style("text_body"))

    info_table.add_row(" Nomor", f": 📞 [bold {theme['text_body']}]{profile['number']}[/]")
    info_table.add_row(" Type", f": 🧾 [{theme['text_body']}]{profile['subscription_type']} ({profile['subscriber_id']})[/]")
    info_table.add_row(" Pulsa", f": 💰 Rp [{theme['text_money']}]{pulsa_str}[/]")
    info_table.add_row(" Kuota", f": 📊 [{theme['text_date']}]{display_quota}[/]")
    info_table.add_row(" Tiering", f": 🏅 [{theme['text_date']}]{profile['point_info']}[/]")
    info_table.add_row(" Masa Aktif", f": ⏳ [{theme['text_date']}]{expired_at_dt}[/]")

    console.print(
        Panel(
            info_table,
            title=f"[{get_theme_style('text_title')}]✨ Informasi Akun ✨[/]",
            title_align="center",
            border_style=get_theme_style("border_info"),
            padding=(1, 2),
            expand=True,
        )
    )

    # Paket spesial preview 🔥
    special_packages = segments.get("special_packages", [])
    if special_packages:
        best = random.choice(special_packages)
        name = best.get("name", "-")
        diskon_percent = best.get("diskon_percent", 0)
        diskon_price = best.get("diskon_price", 0)
        original_price = best.get("original_price", 0)
        emoji_diskon = "💸" if diskon_percent >= 50 else ""
        emoji_kuota = "🔥" if best.get("kuota_gb", 0) >= 100 else ""

        special_text = (
            f"[bold {theme['text_title']}]🔥🔥🔥 Paket Special Untukmu! 🔥🔥🔥[/{theme['text_title']}]\n\n"
            f"[{theme['text_body']}]{emoji_kuota} {name}[/{theme['text_body']}]\n"
            f"Diskon {diskon_percent}% {emoji_diskon} "
            f"Rp[{theme['text_err']}][strike]{get_rupiah(original_price)}[/strike][/{theme['text_err']}] ➡️ "
            f"Rp[{theme['text_money']}]{get_rupiah(diskon_price)}[/{theme['text_money']}]"
        )

        console.print(
            Panel(
                Align.center(special_text),
                border_style=theme["border_warning"],
                padding=(0, 2),
                width=console.size.width,
            )
        )
        console.print(Align.center(f"[{theme['text_sub']}]Pilih [11] untuk lihat semua paket spesial[/{theme['text_sub']}]"))

    # Menu utama ⭐
    menu_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
    menu_table.add_column("Kode", justify="right", style=get_theme_style("text_key"), width=6)
    menu_table.add_column("Aksi", style=get_theme_style("text_body"))

    menu_table.add_row("1", "🔐 Login/Ganti akun")
    menu_table.add_row("2", "📑 Lihat Paket Saya")
    menu_table.add_row("3", "🔥 Beli Paket Hot Promo")
    menu_table.add_row("4", "🔥 Beli Paket Hot Promo-2")
    menu_table.add_row("5", "🔍 Beli Paket Berdasarkan Option Code")
    menu_table.add_row("6", "🧩 Beli Paket Berdasarkan Family Code")
    menu_table.add_row("7", "🛒 Beli Semua Paket di Family Code")
    menu_table.add_row("8", "📜 Riwayat Transaksi")
    menu_table.add_row("9", "👨‍👩‍👧‍👦 Family Plan/Akrab Organizer")
    menu_table.add_row("10", "👥 Circle")
    menu_table.add_row("12", "📂 Store Family List")
    menu_table.add_row("13", "📦 Store Packages")
    menu_table.add_row("14", "🎁 Redeemables")
    menu_table.add_row("R", "📝 Register")
    menu_table.add_row("N", "🔔 Notifikasi")
    menu_table.add_row("V", "✅ Validate MSISDN")
    menu_table.add_row("00", "⭐ Bookmark Paket")
    menu_table.add_row("66", "💾 Simpan/Kelola Family Code")
    menu_table.add_row("77", "📢 Info Unlock Code")
    menu_table.add_row("88", "🎨 Ganti Tema CLI")
    menu_table.add_row("99", "⛔ Tutup aplikasi")

    console.print(
        Panel(
            menu_table,
            title=f"[{get_theme_style('text_title')}]✨ Menu Utama ✨[/]",
            title_align="center",
            border_style=get_theme_style("border_primary"),
            padding=(0, 1),
            expand=True,
        )
    )


# ============================
# Main loop
# ============================
def main():
    ensure_git()
    theme = get_theme()
    while True:
        active_user = AuthInstance.get_active_user()
        if active_user is not None:
            with live_loading("🔄 Memuat data akun...", get_theme()):
                balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
                quota = get_quota(AuthInstance.api_key, active_user["tokens"]["id_token"]) or {}
                segments = dashboard_segments(AuthInstance.api_key, active_user["tokens"]["id_token"], active_user["tokens"]["access_token"]) or {}

            # Format quota
            remaining = quota.get("remaining", 0)
            total = quota.get("total", 0)
            has_unlimited = quota.get("has_unlimited", False)
            if total > 0 or has_unlimited:
                display_quota = f"{remaining/1e9:.2f}/{total/1e9:.2f} GB" + (" (Unlimited)" if has_unlimited else "")
            else:
                display_quota = "-"

            # Tiering
            point_info = "Points: N/A | Tier: N/A"
            if active_user["subscription_type"] == "PREPAID":
                tiering_data = get_tiering_info(AuthInstance.api_key, active_user["tokens"])
                point_info = f"Points: {tiering_data.get('current_point',0)} | Tier: {tiering_data.get('tier',0)}"

            profile = {
                "number": active_user["number"],
                "subscriber_id": active_user["subscriber_id"],
                "subscription_type": active_user["subscription_type"],
                "balance": balance.get("remaining"),
                "balance_expired_at": balance.get("expired_at"),
                "point_info": point_info,
            }

            # tampilkan menu utama
            show_main_menu(profile, display_quota, segments)

            #choice = input("👉 Pilih menu: ")
            choice = console.input(f"[{theme['text_sub']}]👉 Pilih menu: [/{theme['text_sub']}] ").strip()

            # Shortcuts & navigasi
            if choice.lower() == "t":
                pause()
            elif choice == "1":
                selected_user_number = show_account_menu()
                if selected_user_number:
                    AuthInstance.set_active_user(selected_user_number)
                    print_success("🔐", f"Akun aktif diganti ke {selected_user_number}")
                else:
                    print_error("❌", "Tidak ada user terpilih atau gagal memuat user.")
                continue
            elif choice == "2":
                fetch_my_packages()
                continue
            elif choice == "3":
                show_hot_menu()
            elif choice == "4":
                show_hot_menu2()
            elif choice == "5":
                option_code = input("🔍 Masukkan option code: ")
                if option_code == "99":
                    continue
                show_package_details(AuthInstance.api_key, active_user["tokens"], option_code, False)
            elif choice == "6":
                family_code = input("🧩 Masukkan family code: ")
                if family_code == "99":
                    continue
                get_packages_by_family(family_code)
            elif choice == "7":
                family_code = input("🛒 Masukkan family code: ")
                if family_code == "99":
                    continue
                start_from_option = input("Mulai dari option number (default 1): ")
                try:
                    start_from_option = int(start_from_option)
                except ValueError:
                    start_from_option = 1
                use_decoy = input("Gunakan decoy package? (y/n): ").lower() == "y"
                pause_on_success = input("Pause tiap sukses? (y/n): ").lower() == "y"
                delay_seconds = input("Delay antar pembelian (0 = tanpa delay): ")
                try:
                    delay_seconds = int(delay_seconds)
                except ValueError:
                    delay_seconds = 0
                purchase_by_family(family_code, use_decoy, pause_on_success, delay_seconds, start_from_option)
            elif choice == "8":
                show_transaction_history(AuthInstance.api_key, active_user["tokens"])
            elif choice == "9":
                show_family_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "10":
                show_circle_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "11":
                is_enterprise = input("🏬 Enterprise store? (y/n): ").lower() == "y"
                show_store_segments_menu(is_enterprise)
            elif choice == "12":
                is_enterprise = input("📂 Enterprise? (y/n): ").lower() == "y"
                show_family_list_menu(profile["subscription_type"], is_enterprise)
            elif choice == "13":
                is_enterprise = input("📦 Enterprise? (y/n): ").lower() == "y"
                show_store_packages_menu(profile["subscription_type"], is_enterprise)
            elif choice == "14":
                is_enterprise = input("🎁 Enterprise? (y/n): ").lower() == "y"
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
                print_success("👋 Sampai jumpa!", "Aplikasi ditutup dengan aman.")
                sys.exit(0)
            elif choice.lower() == "r":
                msisdn = input("📝 Masukkan msisdn (628xxxx): ")
                nik = input("Masukkan NIK: ")
                kk = input("Masukkan KK: ")
                res = dukcapil(AuthInstance.api_key, msisdn, kk, nik)
                print_panel("📑 Hasil Registrasi", json.dumps(res, indent=2))
                pause()
            elif choice.lower() == "v":
                msisdn = input("✅ Masukkan msisdn untuk validasi (628xxxx): ")
                res = validate_msisdn(AuthInstance.api_key, active_user["tokens"], msisdn)
                print_panel("📑 Hasil Validasi", json.dumps(res, indent=2))
                pause()
            elif choice.lower() == "n":
                show_notification_menu()
            elif choice.lower() == "s":
                enter_sentry_mode()
            else:
                print_warning("⚠️ Menu", "Pilihan tidak valid. Silakan coba lagi.")
                pause()
        else:
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
                print_success("🔐", f"Akun aktif diganti ke {selected_user_number}")
            else:
                print_error("❌", "Tidak ada user terpilih atau gagal memuat user.")


if __name__ == "__main__":
    try:
        with live_loading("🔄 Checking for updates...", get_theme()):
            need_update = check_for_updates()
        if need_update:
            print_warning("⬆️", "Versi baru tersedia, silakan update sebelum melanjutkan.")
            pause()
        main()
    except KeyboardInterrupt:
        print_error("👋 Keluar", "Aplikasi dihentikan oleh pengguna.")
