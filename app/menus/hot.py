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

        console.print(table)

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
        table.add_column("Harga", style=theme["text_body"], justify="right")

        for idx, p in enumerate(hot_packages, start=1):
            table.add_row(str(idx), p["name"], f"Rp {p['price']}")

        console.print(table)

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
            selected_package = hot_packages[int(choice) - 1]
            packages = selected_package.get("packages", [])
            if not packages:
                print_panel("ℹ️ Info", "Paket tidak tersedia.")
                pause()
                continue
            
            payment_items = []
            main_package_detail = {}
            for package in packages:
                package_detail = get_package_details(
                    api_key,
                    tokens,
                    package["family_code"],
                    package["variant_code"],
                    package["order"],
                    package["is_enterprise"],
                    package["migration_type"],
                )
                if package == packages[0]:
                    main_package_detail = package_detail
                if not package_detail:
                    print_panel("❌ Error", f"Gagal mengambil detail paket untuk {package['family_code']}.")
                    return None
                payment_items.append(
                    PaymentItem(
                        item_code=package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=package_detail["package_option"]["price"],
                        item_name=package_detail["package_option"]["name"],
                        tax=0,
                        token_confirmation=package_detail["token_confirmation"],
                    )
                )
            
            clear_screen()
            console.print(Panel(
                Align.center(f"{selected_package['name']} - Rp {selected_package['price']}", vertical="middle"),
                border_style=theme["border_info"],
                padding=(1, 2),
                expand=True
            ))

            # Detail paket utama
            price = main_package_detail["package_option"]["price"]
            validity = main_package_detail["package_option"]["validity"]
            detail_html = display_html(main_package_detail["package_option"]["tnc"])
            option_name = main_package_detail.get("package_option", {}).get("name","")
            family_name = main_package_detail.get("package_family", {}).get("name","")
            variant_name = main_package_detail.get("package_detail_variant", {}).get("name","")
            title = f"{family_name} - {variant_name} - {option_name}".strip()

            info_text = Text()
            info_text.append(f"Nama: {title}\n", style="bold")
            info_text.append(f"Harga: Rp {price}\n", style=theme["text_body"])
            info_text.append(f"Masa Aktif: {validity}\n", style=theme["text_body"])
            info_text.append(f"Plan Type: {main_package_detail['package_family']['plan_type']}\n", style=theme["text_body"])
            info_text.append(f"Point: {main_package_detail['package_option']['point']}\n", style=theme["text_body"])

            console.print(Panel(info_text, border_style=theme["border_info"], expand=True))

            # Benefits table
            benefits = main_package_detail["package_option"]["benefits"]
            if benefits and isinstance(benefits, list):
                b_table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
                b_table.add_column("Nama", style=theme["text_body"])
                b_table.add_column("Jenis", style=theme["text_body"])
                b_table.add_column("Total", style=theme["text_body"], justify="right")
                for b in benefits:
                    dt = b["data_type"]
                    total = b["total"]
                    if dt == "VOICE" and total > 0:
                        total_str = f"{total/60:.0f} menit"
                    elif dt == "TEXT" and total > 0:
                        total_str = f"{total} SMS"
                    elif dt == "DATA" and total > 0:
                        total_str = format_quota_byte(total)
                    else:
                        total_str = str(total)
                    if b["is_unlimited"]:
                        total_str += " (Unlimited)"
                    b_table.add_row(b["name"], dt, total_str)
                console.print(Panel(b_table, title="Benefits", border_style=theme["border_info"], expand=True))

            console.print(Panel(f"SnK MyXL:\n{detail_html}", border_style=theme["border_warning"], expand=True))

            # Menu pembayaran
            pay_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
            pay_table.add_column(justify="right", style=theme["text_key"], width=6)
            pay_table.add_column(style=theme["text_body"])
            pay_table.add_row("1", "Balance")
            pay_table.add_row("2", "E-Wallet")
            pay_table.add_row("3", "QRIS")
            pay_table.add_row("00", f"[{theme['text_sub']}]Kembali[/]")

            console.print(Panel(pay_table, border_style=theme["border_primary"], expand=True))

            payment_for = selected_package.get("payment_for", "BUY_PACKAGE")
            ask_overwrite = selected_package.get("ask_overwrite", False)
            overwrite_amount = selected_package.get("overwrite_amount", -1)
            token_confirmation_idx = selected_package.get("token_confirmation_idx", 0)
            amount_idx = selected_package.get("amount_idx", -1)

            in_payment_menu = True
            while in_payment_menu:
                input_method = console.input(f"[{theme['text_sub']}]Pilih metode:[/{theme['text_sub']}] ").strip()
                if input_method == "1":
                    if overwrite_amount == -1:
                        print_panel("⚠️ Warning", f"Pastikan sisa balance KURANG DARI Rp{payment_items[-1].item_price}!!!")
                        balance_answer = console.input("Apakah anda yakin ingin melanjutkan pembelian? (y/n): ").strip().lower()
                        if balance_answer != "y":
                            print_panel("ℹ️ Info", "Pembelian dibatalkan oleh user.")
                            pause()
                            in_payment_menu = False
                            continue
                    settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount=overwrite_amount,
                        token_confirmation_idx=token_confirmation_idx,
                        amount_idx=amount_idx,
                    )
                    pause()
                    in_payment_menu = False
                    in_hot_menu = False

                elif input_method == "2":
                    show_multipayment(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount,
                        token_confirmation_idx,
                        amount_idx,
                    )
                    pause()
                    in_payment_menu = False
                    in_hot_menu = False

                elif input_method == "3":
                    show_qris_payment(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount,
                        token_confirmation_idx,
                        amount_idx,
                    )
                    pause()
                    in_payment_menu = False
                    in_hot_menu = False

                elif input_method == "00":
                    in_payment_menu = False
                    continue

                else:
                    print_panel("⚠️ Error", "Metode tidak valid. Silahkan coba lagi.")
                    pause()
                    continue
