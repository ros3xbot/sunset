import json
from app.client.engsel import get_package_details, get_family
from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause, print_panel, format_quota_byte, display_html, simple_number, get_rupiah
from app.client.purchase.ewallet import show_multipayment
from app.client.purchase.qris import show_qris_payment
from app.client.purchase.balance import settlement_balance
from app.type_dict import PaymentItem
from app.config.theme_config import get_theme
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

console = Console()


def show_hot_menu():
    theme = get_theme()
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_hot_menu = True
    while in_hot_menu:
        clear_screen()
        console.print(Panel(
            Align.center("🔥 Paket Hot 🔥", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))
        simple_number()

        # Load hot packages
        try:
            with open("hot_data/hot.json", "r", encoding="utf-8") as f:
                hot_packages = json.load(f)
        except Exception as e:
            print_panel("❌ Error", f"Gagal memuat hot.json: {e}")
            pause()
            return

        # Tabel daftar paket hot
        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", style=theme["text_key"], width=4, justify="right")
        table.add_column("Family", style=theme["text_body"])
        table.add_column("Variant", style=theme["text_body"])
        table.add_column("Option", style=theme["text_body"])

        for idx, p in enumerate(hot_packages, start=1):
            table.add_row(str(idx), p["family_name"], p["variant_name"], p["option_name"])

        console.print(Panel(
            table,
            #title=f"[{theme['text_title']}]🔥 Daftar Paket Hot[/]",
            border_style=theme["border_info"],
            padding=(0, 0),
            expand=True
        ))

        # Navigasi
        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")

        console.print(Panel(
            nav_table,
            border_style=theme["border_primary"],
            padding=(0, 1),
            expand=True
        ))

        choice = console.input(f"[{theme['text_sub']}]Pilih paket (nomor):[/{theme['text_sub']}] ").strip()
        if choice == "00":
            in_hot_menu = False
            return None

        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_bm = hot_packages[int(choice) - 1]
            family_code = selected_bm["family_code"]
            is_enterprise = selected_bm.get("is_enterprise", False)
            
            family_data = get_family(api_key, tokens, family_code, is_enterprise)
            if not family_data:
                print_panel("❌ Error", "Gagal mengambil data family.")
                pause()
                continue
            
            package_variants = family_data["package_variants"]
            option_code = None
            for variant in package_variants:
                if variant["name"] == selected_bm["variant_name"]:
                    for option in variant["package_options"]:
                        if option["order"] == selected_bm["order"]:
                            option_code = option["package_option_code"]
                            break
            
            if option_code:
                show_package_details(api_key, tokens, option_code, is_enterprise)
            else:
                print_panel("❌ Error", "Option code tidak ditemukan.")
                pause()
        else:
            print_panel("⚠️ Error", "Input tidak valid. Silahkan coba lagi.")
            pause()
            continue


WIDTH = 55
def validate_package_detail(detail):
    return (
        detail and
        isinstance(detail, dict) and
        "package_option" in detail and
        "token_confirmation" in detail and
        isinstance(detail["package_option"], dict) and
        "package_option_code" in detail["package_option"] and
        "price" in detail["package_option"] and
        "name" in detail["package_option"]
    )


def show_hot_menu2():
    theme = get_theme()
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()

    while True:
        clear_screen()
        console.print(Panel(
            Align.center("🔥 Paket Hot Promo-2 🔥", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        try:
            with open("hot_data/hot2.json", "r", encoding="utf-8") as f:
                hot_packages = json.load(f)
        except Exception as e:
            print_panel("❌ Error", f"Gagal memuat hot2.json: {e}")
            pause()
            return

        if not hot_packages:
            print_panel("⚠️ Error", "Tidak ada data paket tersedia.")
            pause()
            return

        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", justify="right", style=theme["text_key"], width=6)
        table.add_column("Nama Paket", style=theme["text_body"])
        table.add_column("Harga", justify="right", style=theme["text_money"], width=10)

        for idx, p in enumerate(hot_packages):
            table.add_row(str(idx + 1), p["name"], get_rupiah(p["price"]))

        console.print(Panel(table, border_style=theme["border_primary"], padding=(0, 0), expand=True))

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=4)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")

        console.print(Panel(nav_table, border_style=theme["border_info"], padding=(0, 1), expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilih paket:[/{theme['text_sub']}] ").strip()
        if choice == "00":
            return

        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_package = hot_packages[int(choice) - 1]
            packages = selected_package.get("packages", [])
            if not packages:
                print_panel("⚠️ Error", "Paket tidak tersedia.")
                pause()
                continue

            payment_items = []
            for package in packages:
                detail = get_package_details(
                    api_key,
                    tokens,
                    package["family_code"],
                    package["variant_code"],
                    package["order"],
                    package["is_enterprise"],
                )
                if validate_package_detail(detail):
                    payment_items.append(PaymentItem(
                        item_code=detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=detail["package_option"]["price"],
                        item_name=detail["package_option"]["name"],
                        tax=0,
                        token_confirmation=detail["token_confirmation"],
                    ))

            if not payment_items:
                print_panel("⚠️ Error", "Gagal memuat data pembayaran. Silakan coba lagi nanti.")
                pause()
                continue

            clear_screen()
            info_text = Text()
            info_text.append(f"{selected_package['name']}\n", style="bold")
            info_text.append(f"Harga: Rp {get_rupiah(selected_package['price'])}\n", style=theme["text_money"])
            info_text.append("Detail:\n", style=theme["text_body"])
            for line in selected_package.get("detail", "").split("\n"):
                cleaned = line.strip()
                if cleaned:
                    info_text.append(f"- {cleaned}\n", style=theme["text_body"])

            console.print(Panel(
                info_text,
                title=f"[{theme['text_title']}]📦 Detail Paket[/]",
                border_style=theme["border_info"],
                padding=(1, 2),
                expand=True
            ))

            while True:
                method_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
                method_table.add_column(justify="right", style=theme["text_key"], width=6)
                method_table.add_column(style=theme["text_body"])
                method_table.add_row("1", "Balance")
                method_table.add_row("2", "E-Wallet")
                method_table.add_row("3", "QRIS")
                method_table.add_row("00", f"[{theme['text_sub']}]Kembali ke daftar paket[/]")

                console.print(Panel(
                    method_table,
                    title=f"[{theme['text_title']}]💳 Pilih Metode Pembayaran[/]",
                    border_style=theme["border_primary"],
                    padding=(0, 1),
                    expand=True
                ))

                method = console.input(f"[{theme['text_sub']}]Pilih metode:[/{theme['text_sub']}] ").strip()
                if method == "1":
                    confirm = console.input(f"[{theme['text_sub']}]Pastikan balance cukup. Lanjutkan pembelian? (y/n):[/{theme['text_sub']}] ").strip().lower()
                    if confirm != "y":
                        print_panel("ℹ️ Info", "Pembelian dibatalkan oleh pengguna.")
                        pause()
                        break
                    settlement_balance(api_key, tokens, payment_items, "BUY_PACKAGE", True)
                    console.input(f"[{theme['text_sub']}]Tekan enter untuk kembali...[/{theme['text_sub']}] ")
                    return
                elif method == "2":
                    show_multipayment(api_key, tokens, payment_items, "BUY_PACKAGE", True)
                    console.input(f"[{theme['text_sub']}]Tekan enter untuk kembali...[/{theme['text_sub']}] ")
                    return
                elif method == "3":
                    show_qris_payment(api_key, tokens, payment_items, "BUY_PACKAGE", True)
                    console.input(f"[{theme['text_sub']}]Tekan enter untuk kembali...[/{theme['text_sub']}] ")
                    return
                elif method == "00":
                    break
                else:
                    print_panel("⚠️ Error", "Metode tidak valid. Silahkan coba lagi.")
                    pause()
        else:
            print_panel("⚠️ Error", "Input tidak valid. Silahkan coba lagi.")
            pause()
