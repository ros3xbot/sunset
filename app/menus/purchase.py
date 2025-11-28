import requests, time
from random import randint

from app.config.imports import *
from app.client.purchase.balance import settlement_balance
from app.type_dict import PaymentItem
from app.menus.util import (
    clear_screen,
    pause,
    print_panel,
    get_rupiah,
    display_html,
    simple_number,
    format_quota_byte
)

console = Console()


def purchase_loop(
    family_code: str,
    order: int,
    use_decoy: bool,
    delay: int,
    pause_on_success: bool = False,
):
    theme = get_theme()
    ensure_git()
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}

    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print_panel("❌ Error", f"Gagal mengambil data family untuk kode: {family_code}.")
        pause()
        return False

    target_variant, target_option = None, None
    for variant in family_data["package_variants"]:
        for option in variant["package_options"]:
            if option["order"] == order:
                target_variant, target_option = variant, option
                break
        if target_option:
            break

    if not target_option:
        print_panel("❌ Error", f"Option order {order} tidak ditemukan di family {family_code}.")
        pause()
        return False

    console.rule(f"[{theme['text_title']}]Mencoba beli paket[/]")
    console.print(
        f"[{theme['text_title']}]{target_variant['name']} - {order}. "
        f"{target_option['name']} - {get_rupiah(target_option['price'])}[/]"
    )

    decoy_package_detail = None
    if use_decoy:
        decoy = DecoyInstance.get_decoy("balance")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            print_panel("❌ Error", "Gagal memuat detail paket decoy.")
            pause()
            return False

    try:
        target_package_detail = get_package_details(
            api_key, tokens, family_code,
            target_variant["package_variant_code"], order, None, None
        )
    except Exception as e:
        print_panel("❌ Error", f"Exception saat mengambil detail paket: {e}")
        time.sleep(delay)
        return True

    payment_items = [
        PaymentItem(
            item_code=target_package_detail["package_option"]["package_option_code"],
            product_type="",
            item_price=target_package_detail["package_option"]["price"],
            item_name=f"{randint(1000, 9999)} {target_package_detail['package_option']['name']}",
            tax=0,
            token_confirmation=target_package_detail["token_confirmation"],
        )
    ]
    if use_decoy and decoy_package_detail:
        payment_items.append(
            PaymentItem(
                item_code=decoy_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=decoy_package_detail["package_option"]["price"],
                item_name=f"{randint(1000, 9999)} {decoy_package_detail['package_option']['name']}",
                tax=0,
                token_confirmation=decoy_package_detail["token_confirmation"],
            )
        )

    overwrite_amount = target_package_detail["package_option"]["price"]
    if use_decoy and decoy_package_detail:
        overwrite_amount += decoy_package_detail["package_option"]["price"]

    try:
        res = settlement_balance(api_key, tokens, payment_items, "BUY_PACKAGE", False, overwrite_amount)
        if res and res.get("status", "") != "SUCCESS":
            error_msg = res.get("message", "Unknown error")
            if "Bizz-err.Amount.Total" in error_msg:
                valid_amount = int(error_msg.split("=")[1].strip())
                print_panel("ℹ️ Info", f"Menyesuaikan total amount ke: {valid_amount}")
                res = settlement_balance(api_key, tokens, payment_items, "BUY_PACKAGE", False, valid_amount)

        if res and res.get("status", "") == "SUCCESS":
            print_panel("✅ Success", "Pembelian berhasil!")
            if pause_on_success:
                choice = console.input("Lanjutkan pembelian berikutnya? (y/n): ").strip().lower()
                if choice == 'n':
                    return False
    except Exception as e:
        print_panel("❌ Error", f"Exception saat membuat order: {e}")

    if delay > 0:
        for i in range(delay, 0, -1):
            console.print(f"[{theme['text_sub']}]Menunggu {i} detik...[/]", end="\r")
            time.sleep(1)
        console.print()

    return True


def purchase_by_family(
    family_code: str,
    use_decoy: bool,
    pause_on_success: bool = True,
    delay_seconds: int = 0,
    start_from_option: int = 1,
):
    theme = get_theme()
    ensure_git()
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}

    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print_panel("❌ Error", f"Gagal mengambil data family untuk kode: {family_code}.")
        pause()
        return None

    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]

    console.rule(f"[{theme['text_title']}]Pembelian Family {family_name}[/]")
    successful_purchases = []
    start_buying = start_from_option <= 1

    for variant in variants:
        for option in variant["package_options"]:
            option_order = option["order"]
            if not start_buying and option_order == start_from_option:
                start_buying = True
            if not start_buying:
                console.print(f"[{theme['text_sub']}]Melewati option {option_order}. {option['name']}[/]")
                continue

            console.print(
                f"[{theme['text_title']}]{variant['name']} - {option_order}. "
                f"{option['name']} - {get_rupiah(option['price'])}[/]"
            )

            try:
                target_package_detail = get_package_details(
                    api_key, tokens, family_code,
                    variant["package_variant_code"], option_order, None, None
                )
            except Exception as e:
                print_panel("❌ Error", f"Exception saat mengambil detail paket: {e}")
                continue

            payment_items = [
                PaymentItem(
                    item_code=target_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=target_package_detail["package_option"]["price"],
                    item_name=f"{randint(1000, 9999)} {target_package_detail['package_option']['name']}",
                    tax=0,
                    token_confirmation=target_package_detail["token_confirmation"],
                )
            ]

            overwrite_amount = target_package_detail["package_option"]["price"]

            try:
                res = settlement_balance(api_key, tokens, payment_items, "BUY_PACKAGE", False, overwrite_amount)
                if res and res.get("status", "") == "SUCCESS":
                    successful_purchases.append(f"{variant['name']} - {option['name']}")
                    print_panel("✅ Success", "Pembelian berhasil!")
                    if pause_on_success:
                        pause()
            except Exception as e:
                print_panel("❌ Error", f"Exception saat membuat order: {e}")

            if delay_seconds > 0:
                console.print(f"[{theme['text_sub']}]Menunggu {delay_seconds} detik sebelum pembelian berikutnya...[/]")
                time.sleep(delay_seconds)

    console.rule(f"[{theme['text_title']}]Ringkasan Pembelian[/]")
    console.print(f"Family: {family_name}")
    console.print(f"Total sukses: {len(successful_purchases)}")
    for purchase in successful_purchases:
        console.print(f"- {purchase}")
    pause()


def purchase_n_times(
    n: int,
    family_code: str,
    variant_code: str,
    option_order: int,
    use_decoy: bool,
    delay_seconds: int = 0,
    pause_on_success: bool = False,
    token_confirmation_idx: int = 0,
):
    theme = get_theme()
    ensure_git()
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}

    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print_panel("❌ Error", f"Gagal mengambil data family untuk kode: {family_code}.")
        pause()
        return None

    target_variant = next((v for v in family_data["package_variants"] if v["package_variant_code"] == variant_code), None)
    if not target_variant:
        print_panel("❌ Error", f"Variant code {variant_code} tidak ditemukan.")
        pause()
        return None

    target_option = next((o for o in target_variant["package_options"] if o["order"] == option_order), None)
    if not target_option:
        print_panel("❌ Error", f"Option order {option_order} tidak ditemukan.")
        pause()
        return None

    console.rule(f"[{theme['text_title']}]Pembelian {n} kali[/]")
    successful_purchases = []

    for i in range(n):
        console.print(
            f"[{theme['text_title']}]{i+1}/{n}: {target_variant['name']} - "
            f"{option_order}. {target_option['name']} - {get_rupiah(target_option['price'])}[/]"
        )

        try:
            target_package_detail = get_package_details(
                api_key, tokens, family_code,
                target_variant["package_variant_code"], option_order, None, None
            )
        except Exception as e:
            print_panel("❌ Error", f"Exception saat mengambil detail paket: {e}")
            continue

        payment_items = [
            PaymentItem(
                item_code=target_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=target_package_detail["package_option"]["price"],
                item_name=f"{randint(1000, 9999)} {target_package_detail['package_option']['name']}",
                tax=0,
                token_confirmation=target_package_detail["token_confirmation"],
            )
        ]

        overwrite_amount = target_package_detail["package_option"]["price"]

        try:
            res = settlement_balance(
                api_key, tokens, payment_items,
                "BUY_PACKAGE", False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=token_confirmation_idx
            )
            if res and res.get("status", "") == "SUCCESS":
                successful_purchases.append(f"{target_variant['name']} - {target_option['name']}")
                print_panel("✅ Success", "Pembelian berhasil!")
                if pause_on_success:
                    pause()
            else:
                error_msg = res.get("message", "Unknown error") if res else "Unknown error"
                print_panel("❌ Error", f"Pembelian gagal: {error_msg}")
        except Exception as e:
            print_panel("❌ Error", f"Exception saat membuat order: {e}")

        if delay_seconds > 0 and i < n - 1:
            console.print(f"[{theme['text_sub']}]Menunggu {delay_seconds} detik sebelum pembelian berikutnya...[/]")
            time.sleep(delay_seconds)

    console.rule(f"[{theme['text_title']}]Ringkasan Pembelian[/]")
    console.print(f"Family: {family_data['package_family']['name']}")
    console.print(f"Variant: {target_variant['name']}")
    console.print(f"Option: {option_order}. {target_option['name']} - {get_rupiah(target_option['price'])}")
    console.print(f"Total sukses: {len(successful_purchases)}/{n}")
    for idx, purchase in enumerate(successful_purchases, start=1):
        console.print(f"{idx}. {purchase}")
    pause()
    return True


def purchase_n_times_by_option_code(
    n: int,
    option_code: str,
    use_decoy: bool,
    delay_seconds: int = 0,
    pause_on_success: bool = False,
    token_confirmation_idx: int = 0,
):
    theme = get_theme()
    ensure_git()
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}

    console.rule(f"[{theme['text_title']}]Pembelian {n} kali berdasarkan Option Code[/]")
    successful_purchases = []

    for i in range(n):
        console.print(f"[{theme['text_title']}]{i+1}/{n}: Mencoba beli option {option_code}[/]")

        try:
            target_package_detail = get_package(api_key, tokens, option_code)
        except Exception as e:
            print_panel("❌ Error", f"Exception saat mengambil detail paket: {e}")
            continue

        payment_items = [
            PaymentItem(
                item_code=target_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=target_package_detail["package_option"]["price"],
                item_name=f"{randint(1000, 9999)} {target_package_detail['package_option']['name']}",
                tax=0,
                token_confirmation=target_package_detail["token_confirmation"],
            )
        ]

        overwrite_amount = target_package_detail["package_option"]["price"]

        try:
            res = settlement_balance(
                api_key, tokens, payment_items,
                "BUY_PACKAGE", False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=token_confirmation_idx
            )
            if res and res.get("status", "") == "SUCCESS":
                successful_purchases.append(f"Purchase {i+1}")
                print_panel("✅ Success", "Pembelian berhasil!")
                if pause_on_success:
                    pause()
            else:
                error_msg = res.get("message", "Unknown error") if res else "Unknown error"
                print_panel("❌ Error", f"Pembelian gagal: {error_msg}")
        except Exception as e:
            print_panel("❌ Error", f"Exception saat membuat order: {e}")

        if delay_seconds > 0 and i < n - 1:
            console.print(f"[{theme['text_sub']}]Menunggu {delay_seconds} detik sebelum pembelian berikutnya...[/]")
            time.sleep(delay_seconds)

    console.rule(f"[{theme['text_title']}]Ringkasan Pembelian[/]")
    console.print(f"Option Code: {option_code}")
    console.print(f"Total sukses: {len(successful_purchases)}/{n}")
    for idx, purchase in enumerate(successful_purchases, start=1):
        console.print(f"{idx}. {purchase}")
    pause()
    return True

