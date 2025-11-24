import json
from app.client.engsel import get_package_details, get_family
from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause, print_panel, format_quota_byte, display_html, simple_number
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

        # Tabel daftar paket hot2
        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", style=theme["text_key"], width=4, justify="right")
        table.add_column("Nama Paket", style=theme["text_body"])
        table.add_column("Harga", style=theme["text_money"], justify="right")

        for idx, p in enumerate(hot_packages, start=1):
            table.add_row(str(idx), p["name"], f"Rp {p['price']}")

        console.print(Panel(
            table,
            #title=f"[{theme['text_title']}]🔥 Daftar Paket Hot 2[/]",
            border_style=theme["border_info"],
            expand=True
        ))

        # Navigasi
        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")

        console.print(Panel(
            nav_table,
            #title=f"[{theme['text_title']}]🔧 Menu[/]",
            border_style=theme["border_primary"],
            expand=True
        ))

        choice = console.input(f"[{theme['text_sub']}]Pilih paket (nomor):[/{theme['text_sub']}] ").strip()
        if choice == "00":
            in_hot_menu = False
            return None

        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_package = hot_packages[int(choice) - 1]
            packages = selected_package.get("packages", [])
            if not packages:
                print_panel("ℹ️ Info", "Paket tidak tersedia.")
                pause()
                continue

            # Ambil detail paket utama
            package = get_package_details(
                api_key,
                tokens,
                packages[0]["family_code"],
                packages[0]["variant_code"],
                packages[0]["order"],
                packages[0]["is_enterprise"],
                packages[0]["migration_type"],
            )
            if not package:
                print_panel("⚠️ Error", "Gagal memuat detail paket.")
                pause()
                continue

            # Ekstrak field utama
            option = package.get("package_option", {})
            family = package.get("package_family", {})
            variant = package.get("package_detail_variant", {})

            price = option.get("price", 0)
            validity = option.get("validity", "-")
            point = option.get("point", "-")
            plan_type = family.get("plan_type", "-")
            payment_for = family.get("payment_for", "") or "BUY_PACKAGE"
            detail = display_html(option.get("tnc", ""))

            option_name = option.get("name", "")
            family_name = family.get("name", "")
            variant_name = variant.get("name", "")
            title = f"{family_name} - {variant_name} - {option_name}".strip()

            family_code = family.get("package_family_code", "")
            parent_code = package.get("package_addon", {}).get("parent_code", "") or "N/A"

            # Base payment item
            payment_items = [
                PaymentItem(
                    item_code=option.get("package_option_code", ""),
                    product_type="",
                    item_price=price,
                    item_name=f"{variant_name} {option_name}".strip(),
                    tax=0,
                    token_confirmation=package.get("token_confirmation", ""),
                )
            ]

            clear_screen()
            console.print(Panel(
                #Align.center(f"📦 {family_name}", vertical="middle"),
                Align.center(f"📦{selected_package['name']} - Rp {selected_package['price']}", vertical="middle"),
                border_style=theme["border_info"],
                padding=(1, 2),
                expand=True
            ))
            simple_number()

            # Panel Info Paket
            info_table = Table.grid(padding=(0, 1))
            info_table.add_column(justify="left", style=theme["text_body"])
            info_table.add_column(justify="left")
            info_table.add_row("Nama", f": [bold {theme['text_body']}]{title}[/]")
            info_table.add_row("Harga", f": Rp [{theme['text_money']}]{price}[/]")
            info_table.add_row("Masa Aktif", f": [{theme['text_date']}]{validity}[/]")
            info_table.add_row("Point", f": [{theme['text_body']}]{point}[/]")
            info_table.add_row("Plan Type", f": [{theme['text_body']}]{plan_type}[/]")
            info_table.add_row("Payment For", f": [{theme['text_body']}]{payment_for}[/]")
            info_table.add_row("Family Code", f": [{theme['border_warning']}]{family_code}[/]")
            info_table.add_row("Parent Code", f": [{theme['text_sub']}]{parent_code}[/]")

            console.print(Panel(
                info_table,
                title=f"[{theme['text_title']}]📦 Detail Paket[/]",
                border_style=theme["border_info"],
                expand=True
            ))

            # Benefit Paket
            benefits = option.get("benefits", [])
            if benefits:
                benefit_table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
                benefit_table.add_column("Nama", style=theme["text_body"])
                benefit_table.add_column("Jenis", style=theme["text_body"])
                benefit_table.add_column("Unli", style=theme["border_info"], justify="center")
                benefit_table.add_column("Total", style=theme["text_body"], justify="right")

                for b in benefits:
                    dt = b["data_type"]
                    total = b["total"]
                    is_unli = b["is_unlimited"]

                    if is_unli:
                        total_str = {"VOICE": "menit", "TEXT": "SMS", "DATA": "kuota"}.get(dt, dt)
                    else:
                        if dt == "VOICE":
                            total_str = f"{total / 60:.0f} menit"
                        elif dt == "TEXT":
                            total_str = f"{total} SMS"
                        elif dt == "DATA":
                            total_str = format_quota_byte(total)
                        else:
                            total_str = f"{total} ({dt})"

                    benefit_table.add_row(b["name"], dt, "YES" if is_unli else "-", total_str)

                console.print(Panel(
                    benefit_table,
                    title=f"[{theme['text_title']}]🎁 Benefit Paket[/]",
                    border_style=theme["border_success"],
                    expand=True
                ))

            # Syarat & Ketentuan
            console.print(Panel(
                detail,
                title=f"[{theme['text_title']}]📜 Syarat & Ketentuan[/]",
                border_style=theme["border_warning"],
                expand=True
            ))

            # Navigasi Pembelian
            nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
            nav_table.add_column(justify="right", style=theme["text_key"], width=6)
            nav_table.add_column(style=theme["text_body"])
            nav_table.add_row("1", "💰 Beli dengan Pulsa")
            nav_table.add_row("2", "💳 E-Wallet")
            nav_table.add_row("3", "📱 QRIS")
            nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke daftar paket[/]")

            console.print(Panel(
                nav_table,
                title=f"[{theme['text_title']}]🛒 Opsi Pembelian[/]",
                border_style=theme["border_primary"],
                expand=True
            ))

            # Input pilihan
            choice = console.input(f"[{theme['text_sub']}]Pilihan:[/{theme['text_sub']}] ").strip()
            if choice == "1":
                settlement_balance(
                    api_key,
                    tokens,
                    payment_items,
                    payment_for,
                    ask_overwrite=False,
                    overwrite_amount=-1,
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
                    payment_for,
                    ask_overwrite=False,
                    overwrite_amount=-1,
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
                    payment_for,
                    ask_overwrite=False,
                    overwrite_amount=-1,
                    token_confirmation_idx=0,
                    amount_idx=-1
                )
                pause()
                in_hot_menu = False

            elif choice == "00":
                # kembali ke daftar paket
                continue

            else:
                print_panel("⚠️ Error", "Pilihan tidak valid. Silahkan coba lagi.")
                pause()
                continue

