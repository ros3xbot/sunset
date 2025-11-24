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

def show_hot_menu2():
    theme = get_theme()
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()

    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        main_package_detail = {}

        # Header
        console.print(Panel(
            Align.center("🔥 Paket Hot 2 🔥", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))
        simple_number()

        # Load data paket
        hot_packages = []
        try:
            with open("hot_data/hot2.json", "r", encoding="utf-8") as f:
                hot_packages = json.load(f)
        except Exception as e:
            print_panel("❌ Error", f"Gagal memuat hot2.json: {e}")
            pause()
            return None

        if not hot_packages:
            print_panel("⚠️ Error", "Tidak ada data paket tersedia.")
            pause()
            return None

        # Tabel daftar paket
        pkg_table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        pkg_table.add_column("No", justify="right", style=theme["text_key"], width=6)
        pkg_table.add_column("Nama Paket", style=theme["text_body"])
        pkg_table.add_column("Harga", justify="right", style=theme["text_money"], width=16)

        for idx, p in enumerate(hot_packages, start=1):
            formatted_price = get_rupiah(p["price"])
            pkg_table.add_row(str(idx), p["name"], f"{formatted_price}")     
        
        console.print(Panel(pkg_table, border_style=theme["border_info"], padding=(0, 0), expand=True))

        # Navigasi kembali
        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=4)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")
        console.print(Panel(nav_table, border_style=theme["border_primary"], padding=(0, 1), expand=True))

        # Input pilihan paket
        choice = console.input(f"[{theme['text_sub']}]Pilih paket:[/{theme['text_sub']}] ").strip()
        if choice == "00":
            in_bookmark_menu = False
            return None

        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_package = hot_packages[int(choice) - 1]
            packages = selected_package.get("packages", [])
            if len(packages) == 0:
                print_panel("⚠️ Error", "Paket tidak tersedia.")
                pause()
                continue

            # Ambil detail paket untuk semua sub-package, simpan main_package_detail dari paket pertama
            payment_items = []
            for pkg_idx, package in enumerate(packages):
                detail = get_package_details(
                    api_key,
                    tokens,
                    package["family_code"],
                    package["variant_code"],
                    package["order"],
                    package["is_enterprise"],
                    package["migration_type"],  # dipertahankan sesuai file ke-2
                )

                if pkg_idx == 0:
                    main_package_detail = detail

                # Force failed when one of the package detail is None
                if not detail:
                    print_panel("❌ Error", f"Gagal mengambil detail paket untuk {package['family_code']}.")
                    return None

                payment_items.append(PaymentItem(
                    item_code=detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=detail["package_option"]["price"],
                    item_name=detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=detail["token_confirmation"],
                ))

            # Panel ringkas detail paket terpilih (name/price/detail)
            clear_screen()
            console.print(Panel(
                Align.center(f"📦 {selected_package['name']}", vertical="middle"),
                border_style=theme["border_info"],
                padding=(1, 2),
                expand=True
            ))
            simple_number()

            info_text = Text()
            info_text.append(f"{selected_package['name']}\n", style="bold")

            harga_selected_str = get_rupiah(selected_package["price"]) if isinstance(selected_package.get("price"), (int, float)) else str(selected_package["price"])
            info_text.append(f"Harga: Rp {harga_selected_str}\n", style=theme["text_money"])

            info_text.append("Detail:\n", style=theme["text_body"])
            for line in str(selected_package.get("detail", "")).split("\n"):
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

            # Panel Main Package Details (mempertahankan semua field dari file ke-2)
            # Extract field sama persis seperti file ke-2
            price = main_package_detail["package_option"]["price"]
            validity = main_package_detail["package_option"]["validity"]
            detail_tnc = display_html(main_package_detail["package_option"]["tnc"])

            option_name = main_package_detail.get("package_option", {}).get("name", "")
            family_name = main_package_detail.get("package_family", {}).get("name", "")
            # catatan: file ke-2 memakai get("package_detail_variant", "") lalu .get("name","")
            # aman: pastikan dict
            variant_name = (main_package_detail.get("package_detail_variant") or {}).get("name", "")

            title = f"{family_name} - {variant_name} - {option_name}".strip()

            family_code = main_package_detail.get("package_family", {}).get("package_family_code", "")
            parent_code = main_package_detail.get("package_addon", {}).get("parent_code", "") or "N/A"

            payment_for_from_detail = main_package_detail["package_family"]["payment_for"]

            
            # Ambil parameter pembayaran dari selected_package (dipertahankan)
            payment_for = selected_package.get("payment_for", "BUY_PACKAGE")
            ask_overwrite = selected_package.get("ask_overwrite", False)
            overwrite_amount = selected_package.get("overwrite_amount", -1)
            token_confirmation_idx = selected_package.get("token_confirmation_idx", 0)
            amount_idx = selected_package.get("amount_idx", -1)

            # Menu pembayaran (dengan opsi yang sama persis)
            in_payment_menu = True
            while in_payment_menu:
                method_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
                method_table.add_column(justify="right", style=theme["text_key"], width=6)
                method_table.add_column(style=theme["text_body"])
                method_table.add_row("1", "Balance")
                method_table.add_row("2", "E-Wallet")
                method_table.add_row("3", "QRIS")
                method_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu sebelumnya[/]")

                console.print(Panel(
                    method_table,
                    title=f"[{theme['text_title']}]💳 Pilih Metode Pembelian[/]",
                    border_style=theme["border_primary"],
                    padding=(0, 1),
                    expand=True
                ))

                input_method = console.input(f"[{theme['text_sub']}]Pilih metode:[/{theme['text_sub']}] ").strip()

                if input_method == "1":
                    if overwrite_amount == -1:
                        # Menjaga teks peringatan khas dari file ke-2
                        last_price = payment_items[-1].item_price if hasattr(payment_items[-1], "item_price") else payment_items[-1]["item_price"]
                        warn_price_str = get_rupiah(last_price) if isinstance(last_price, (int, float)) else str(last_price)
                        console.print(f"[{theme['text_warn']}]Pastikan sisa balance KURANG DARI Rp{warn_price_str}!!![/]")

                        balance_answer = console.input(f"[{theme['text_sub']}]Apakah anda yakin ingin melanjutkan pembelian? (y/n):[/{theme['text_sub']}] ").strip()
                        if balance_answer.lower() != "y":
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
                    console.input(f"[{theme['text_sub']}]Tekan enter untuk kembali...[/{theme['text_sub']}] ")
                    in_payment_menu = False
                    in_bookmark_menu = False

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
                    console.input(f"[{theme['text_sub']}]Tekan enter untuk kembali...[/{theme['text_sub']}] ")
                    in_payment_menu = False
                    in_bookmark_menu = False

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
                    console.input(f"[{theme['text_sub']}]Tekan enter untuk kembali...[/{theme['text_sub']}] ")
                    in_payment_menu = False
                    in_bookmark_menu = False

                elif input_method == "00":
                    in_payment_menu = False
                    continue

                else:
                    print_panel("⚠️ Error", "Metode tidak valid. Silahkan coba lagi.")
                    pause()
                    continue

        else:
            print_panel("⚠️ Error", "Input tidak valid. Silahkan coba lagi.")
            pause()
            continue
