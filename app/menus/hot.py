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



class PaymentItem(TypedDict):
    item_code: str
    product_type: str
    item_price: int
    item_name: str
    tax: int
    token_confirmation: str

def show_hot_menu2():
    theme = get_theme()
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()

    in_hot_menu = True
    while in_hot_menu:
        clear_screen()
        console.print(Panel(
            Align.center("🔥 Paket Hot 2 🔥", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))
        simple_number()

        try:
            with open("hot_data/hot2.json", "r", encoding="utf-8") as f:
                hot_packages = json.load(f)
        except Exception as e:
            print_panel("❌ Error", f"Gagal memuat hot2.json: {e}")
            pause()
            return

        # Tabel daftar paket
        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", style=theme["text_key"], width=4, justify="right")
        table.add_column("Nama Paket", style=theme["text_body"])
        table.add_column("Harga", style=theme["text_money"], justify="right")

        for idx, p in enumerate(hot_packages, start=1):
            table.add_row(str(idx), p["name"], get_rupiah(p["price"]))

        console.print(Panel(table, border_style=theme["border_info"], expand=True))

        # Navigasi awal
        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")

        console.print(Panel(nav_table, border_style=theme["border_primary"], expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilih paket (nomor):[/{theme['text_sub']}] ").strip()
        if choice == "00":
            in_hot_menu = False
            return None

        if not (choice.isdigit() and 1 <= int(choice) <= len(hot_packages)):
            print_panel("⚠️ Error", "Input tidak valid. Silahkan coba lagi.")
            pause()
            continue

        selected_package = hot_packages[int(choice) - 1]
        packages = selected_package.get("packages", [])
        if not packages:
            print_panel("ℹ️ Info", "Paket tidak tersedia.")
            pause()
            continue

        package_detail = get_package_details(
            api_key,
            tokens,
            packages[0]["family_code"],
            packages[0]["variant_code"],
            packages[0]["order"],
            packages[0]["is_enterprise"],
            packages[0]["migration_type"],
        )
        if not package_detail:
            print_panel("⚠️ Error", "Gagal memuat detail paket.")
            pause()
            continue

        option = package_detail.get("package_option", {})
        family = package_detail.get("package_family", {})
        variant = package_detail.get("package_detail_variant", {})

        # Harga fallback
        price_api = option.get("price", 0)
        price = price_api if (price_api and price_api > 0) else selected_package.get("price", 0)
        formatted_price = get_rupiah(price)

        # PaymentItem dict-style
        payment_items: list[PaymentItem] = [
            {
                "item_code": option.get("package_option_code", ""),
                "product_type": "",
                "item_price": price,
                "item_name": f"{variant.get('name','')} {option.get('name','')}".strip(),
                "tax": 0,
                "token_confirmation": package_detail.get("token_confirmation", ""),
            }
        ]

        # Panel Info Paket
        info_table = Table.grid(padding=(0, 1))
        info_table.add_column(justify="left", style=theme["border_info"])
        info_table.add_column(justify="left")
        info_table.add_row("Nama", f": [bold {theme['text_body']}]{selected_package['name']}[/]")
        info_table.add_row("Harga", f": Rp [{theme['text_money']}]{formatted_price}[/]")
        info_table.add_row("Payment For", f": [{theme['text_body']}]{family.get('payment_for','BUY_PACKAGE')}[/]")

        console.print(Panel(info_table, title=f"[{theme['text_title']}]📦 Detail Paket[/]",
                            border_style=theme["border_info"], expand=True))

        # Navigasi Pembelian
        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("1", "💰 Beli dengan Pulsa")
        nav_table.add_row("2", "💳 E-Wallet")
        nav_table.add_row("3", "📱 QRIS")
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke daftar paket[/]")

        console.print(Panel(nav_table, title=f"[{theme['text_title']}]🛒 Opsi Pembelian[/]",
                            border_style=theme["border_primary"], expand=True))

        # Input pilihan
        choice = console.input(f"[{theme['text_sub']}]Pilihan:[/{theme['text_sub']}] ").strip()
        last_price = payment_items[-1]["item_price"]

        # Fallback overwrite_amount
        overwrite_amount = selected_package.get("overwrite_amount", -1)
        if overwrite_amount == -1 or overwrite_amount <= 0:
            overwrite_amount = last_price

        if choice == "1":
            print_panel("⚠️ Warning", f"Pastikan sisa balance KURANG DARI Rp{get_rupiah(last_price)}!!!")
            balance_answer = console.input("Apakah anda yakin ingin melanjutkan pembelian? (y/n): ").strip().lower()
            if balance_answer != "y":
                print_panel("ℹ️ Info", "Pembelian dibatalkan oleh user.")
                pause()
                continue

            settlement_balance(
                api_key,
                tokens,
                payment_items,
                family.get("payment_for","BUY_PACKAGE"),
                ask_overwrite=False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=0,
                amount_idx=-1
            )
            pause()
            in_hot_menu = False

        elif choice == "2":
            show_multipayment(
                api_key,
                tokens,
                payment_items,
                family.get("payment_for","BUY_PACKAGE"),
                ask_overwrite=False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=0,
                amount_idx=-1
            )
            pause()
            in_hot_menu = False

        elif choice == "3":
            show_qris_payment(
                api_key,
                tokens,
                payment_items,
                family.get("payment_for","BUY_PACKAGE"),
                ask_overwrite=False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=0,
                amount_idx=-1
            )
            pause()
            in_hot_menu = False

        elif choice == "00":
            continue

        else:
            print_panel("⚠️ Error", "Pilihan tidak valid. Silahkan coba lagi.")
            pause()
            continue

