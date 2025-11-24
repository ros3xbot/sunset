import requests, time
from random import randint
from app.client.engsel import get_family, get_package_details, get_package
from app.service.auth import AuthInstance
from app.service.decoy import DecoyInstance
from app.type_dict import PaymentItem
from app.client.purchase.balance import settlement_balance
from app.menus.util import (
    clear_screen,
    pause,
    print_panel,
    get_rupiah,
    display_html,
    simple_number,
    format_quota_byte
)


def purchase_loop(
    family_code: str,
    order: int,
    use_decoy: bool,
    delay: int,
    pause_on_success: bool = False,
):
    theme = get_theme()
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}

    # 1. Cari variant & option sesuai order
    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print_panel("❌ Error", f"Gagal mengambil data family untuk kode: {family_code}.")
        pause()
        return False

    target_variant = None
    target_option = None
    for variant in family_data["package_variants"]:
        for option in variant["package_options"]:
            if option["order"] == order:
                target_variant = variant
                target_option = option
                break
        if target_option:
            break

    if not target_option or not target_variant:
        print_panel("❌ Error", f"Option order {order} tidak ditemukan di family {family_code}.")
        pause()
        return False

    option_name = target_option["name"]
    option_price = target_option["price"]
    variant_code = target_variant["package_variant_code"]

    console.print("-"*55)
    console.print(f"[{theme['text_title']}]Mencoba beli: {target_variant['name']} - {order}. {option_name} - Rp{option_price}[/]")

    # 2. Decoy logic
    decoy_package_detail = None
    if use_decoy:
        decoy = DecoyInstance.get_decoy("balance")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            print_panel("❌ Error", "Gagal memuat detail paket decoy.")
            pause()
            return False

    # 3. Ambil detail package target
    try:
        target_package_detail = get_package_details(
            api_key,
            tokens,
            family_code,
            variant_code,
            order,
            None,
            None,
        )
    except Exception as e:
        print_panel("❌ Error", f"Exception saat mengambil detail paket: {e}")
        time.sleep(delay)
        return True  # lanjut loop

    # 4. Susun payment items
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

    # 5. Settlement
    overwrite_amount = target_package_detail["package_option"]["price"]
    if use_decoy and decoy_package_detail:
        overwrite_amount += decoy_package_detail["package_option"]["price"]

    try:
        res = settlement_balance(
            api_key,
            tokens,
            payment_items,
            "BUY_PACKAGE",
            False,
            overwrite_amount,
        )

        if res and res.get("status", "") != "SUCCESS":
            error_msg = res.get("message", "Unknown error")
            print_panel("❌ Error", f"Purchase failed: {error_msg}")
            if "Bizz-err.Amount.Total" in error_msg:
                error_msg_arr = error_msg.split("=")
                valid_amount = int(error_msg_arr[1].strip())
                print_panel("ℹ️ Info", f"Adjusted total amount to: {valid_amount}")
                res = settlement_balance(
                    api_key,
                    tokens,
                    payment_items,
                    "BUY_PACKAGE",
                    False,
                    valid_amount,
                )

        if res and res.get("status", "") == "SUCCESS":
            print_panel("✅ Success", "Purchase berhasil!")
            if pause_on_success:
                choice = console.input("Lanjut Dor? (y/n): ").strip().lower()
                if choice == 'n':
                    return False
        else:
            print_panel("❌ Error", "Purchase tidak berhasil. Cek pesan di atas.")

    except Exception as e:
        print_panel("❌ Error", f"Exception saat membuat order: {e}")

    # 6. Delay loop
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
    active_user = AuthInstance.get_active_user()
    subscription_type = active_user.get("subscription_type", "")
    
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}
    
    # Jika pakai decoy
    if use_decoy:
        decoy = DecoyInstance.get_decoy("balance")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            print_panel("❌ Error", "Gagal memuat detail paket decoy.")
            pause()
            return False
        
        balance_threshold = decoy_package_detail["package_option"]["price"]
        console.print(f"[{theme['text_warning']}]Pastikan sisa balance KURANG DARI Rp{balance_threshold}![/]")
        balance_answer = console.input("Apakah anda yakin ingin melanjutkan pembelian? (y/n): ").strip().lower()
        if balance_answer != "y":
            print_panel("ℹ️ Info", "Pembelian dibatalkan oleh user.")
            pause()
            return None
    
    # Ambil data family
    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print_panel("❌ Error", f"Gagal mengambil data family untuk kode: {family_code}.")
        pause()
        return None
    
    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]
    
    console.print("-"*55)
    successful_purchases = []
    packages_count = sum(len(v["package_options"]) for v in variants)
    
    purchase_count = 0
    start_buying = start_from_option <= 1

    for variant in variants:
        variant_name = variant["name"]
        for option in variant["package_options"]:
            tokens = AuthInstance.get_active_tokens()
            option_order = option["order"]
            if not start_buying and option_order == start_from_option:
                start_buying = True
            if not start_buying:
                console.print(f"[{theme['text_sub']}]Skipping option {option_order}. {option['name']}[/]")
                continue
            
            option_name = option["name"]
            option_price = option["price"]
            
            purchase_count += 1
            console.print(f"[{theme['text_title']}]Purchase {purchase_count} dari {packages_count}...[/]")
            console.print(f"Mencoba beli: {variant_name} - {option_order}. {option_name} - Rp{option_price}")
            
            payment_items = []
            
            try:
                if use_decoy:                
                    decoy = DecoyInstance.get_decoy("balance")
                    decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
                    if not decoy_package_detail:
                        print_panel("❌ Error", "Gagal memuat detail paket decoy.")
                        pause()
                        return False
                
                target_package_detail = get_package_details(
                    api_key,
                    tokens,
                    family_code,
                    variant["package_variant_code"],
                    option["order"],
                    None,
                    None,
                )
            except Exception as e:
                print_panel("❌ Error", f"Exception saat mengambil detail paket: {e}")
                console.print(f"Gagal ambil detail untuk {variant_name} - {option_name}. Melewati.")
                continue
            
            # Tambahkan item utama
            payment_items.append(
                PaymentItem(
                    item_code=target_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=target_package_detail["package_option"]["price"],
                    item_name=f"{randint(1000, 9999)} {target_package_detail['package_option']['name']}",
                    tax=0,
                    token_confirmation=target_package_detail["token_confirmation"],
                )
            )
            
            # Tambahkan decoy jika perlu
            if use_decoy:
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
            if use_decoy or overwrite_amount == 0:
                overwrite_amount += decoy_package_detail["package_option"]["price"]
                
            error_msg = ""

            try:
                res = settlement_balance(
                    api_key,
                    tokens,
                    payment_items,
                    "🤑",
                    False,
                    overwrite_amount=overwrite_amount,
                    token_confirmation_idx=1
                )
                
                if res and res.get("status", "") != "SUCCESS":
                    error_msg = res.get("message", "")
                    if "Bizz-err.Amount.Total" in error_msg:
                        error_msg_arr = error_msg.split("=")
                        valid_amount = int(error_msg_arr[1].strip())
                        print_panel("ℹ️ Info", f"Adjusted total amount to: {valid_amount}")
                        res = settlement_balance(
                            api_key,
                            tokens,
                            payment_items,
                            "SHARE_PACKAGE",
                            False,
                            overwrite_amount=valid_amount,
                            token_confirmation_idx=-1
                        )
                        if res and res.get("status", "") == "SUCCESS":
                            error_msg = ""
                            successful_purchases.append(f"{variant_name}|{option_order}. {option_name} - Rp{option_price}")
                            print_panel("✅ Success", "Purchase berhasil!")
                            if pause_on_success:
                                pause()
                        else:
                            error_msg = res.get("message", "")
                else:
                    successful_purchases.append(f"{variant_name}|{option_order}. {option_name} - Rp{option_price}")
                    print_panel("✅ Success", "Purchase berhasil!")
                    if pause_on_success:
                        pause()

            except Exception as e:
                print_panel("❌ Error", f"Exception saat membuat order: {e}")
            
            console.print("-"*55)
            should_delay = error_msg == "" or "Failed call ipaas purchase" in error_msg
            if delay_seconds > 0 and should_delay:
                console.print(f"[{theme['text_sub']}]Menunggu {delay_seconds} detik sebelum pembelian berikutnya...[/]")
                time.sleep(delay_seconds)
                
    # Ringkasan hasil
    console.print(f"[{theme['text_title']}]Family: {family_name}[/]")
    console.print(f"Successful: {len(successful_purchases)}")
    if successful_purchases:
        console.print("-"*55)
        console.print("Successful purchases:")
        for purchase in successful_purchases:
            console.print(f"- {purchase}")
    console.print("-"*55)
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
    active_user = AuthInstance.get_active_user()
    subscription_type = active_user.get("subscription_type", "")
    
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}
    
    # Jika pakai decoy
    if use_decoy:
        decoy = DecoyInstance.get_decoy("balance")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            print_panel("❌ Error", "Gagal memuat detail paket decoy.")
            pause()
            return False
        
        balance_threshold = decoy_package_detail["package_option"]["price"]
        console.print(f"[{theme['text_warning']}]Pastikan sisa balance KURANG DARI Rp{balance_threshold}![/]")
        balance_answer = console.input("Apakah anda yakin ingin melanjutkan pembelian? (y/n): ").strip().lower()
        if balance_answer != "y":
            print_panel("ℹ️ Info", "Pembelian dibatalkan oleh user.")
            pause()
            return None
    
    # Ambil data family
    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print_panel("❌ Error", f"Gagal mengambil data family untuk kode: {family_code}.")
        pause()
        return None
    
    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]
    target_variant = next((v for v in variants if v["package_variant_code"] == variant_code), None)
    if not target_variant:
        print_panel("❌ Error", f"Variant code {variant_code} tidak ditemukan di family {family_name}.")
        pause()
        return None
    
    target_option = next((o for o in target_variant["package_options"] if o["order"] == option_order), None)
    if not target_option:
        print_panel("❌ Error", f"Option order {option_order} tidak ditemukan di variant {target_variant['name']}.")
        pause()
        return None
    
    option_name = target_option["name"]
    option_price = target_option["price"]
    console.print("-"*55)
    successful_purchases = []
    
    for i in range(n):
        console.print(f"[{theme['text_title']}]Purchase {i + 1} dari {n}...[/]")
        console.print(f"Mencoba beli: {target_variant['name']} - {option_order}. {option_name} - Rp{option_price}")
        
        api_key = AuthInstance.api_key
        tokens: dict = AuthInstance.get_active_tokens() or {}
        payment_items = []
        
        try:
            if use_decoy:
                decoy = DecoyInstance.get_decoy("balance")
                decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
                if not decoy_package_detail:
                    print_panel("❌ Error", "Gagal memuat detail paket decoy.")
                    pause()
                    return False
            
            target_package_detail = get_package_details(
                api_key,
                tokens,
                family_code,
                target_variant["package_variant_code"],
                target_option["order"],
                None,
                None,
            )
        except Exception as e:
            print_panel("❌ Error", f"Exception saat mengambil detail paket: {e}")
            console.print(f"Gagal ambil detail untuk {target_variant['name']} - {option_name}. Melewati.")
            continue
        
        # Tambahkan item utama
        payment_items.append(
            PaymentItem(
                item_code=target_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=target_package_detail["package_option"]["price"],
                item_name=f"{randint(1000, 9999)} {target_package_detail['package_option']['name']}",
                tax=0,
                token_confirmation=target_package_detail["token_confirmation"],
            )
        )
        
        # Tambahkan decoy jika perlu
        if use_decoy:
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
        if use_decoy:
            overwrite_amount += decoy_package_detail["package_option"]["price"]

        try:
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=token_confirmation_idx
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    print_panel("ℹ️ Info", f"Adjusted total amount to: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=token_confirmation_idx
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        successful_purchases.append(f"{target_variant['name']}|{option_order}. {option_name} - Rp{option_price}")
                        print_panel("✅ Success", "Purchase berhasil!")
                        if pause_on_success:
                            pause()
            else:
                successful_purchases.append(f"{target_variant['name']}|{option_order}. {option_name} - Rp{option_price}")
                print_panel("✅ Success", "Purchase berhasil!")
                if pause_on_success:
                    pause()
        except Exception as e:
            print_panel("❌ Error", f"Exception saat membuat order: {e}")
        
        console.print("-"*55)

        if delay_seconds > 0 and i < n - 1:
            console.print(f"[{theme['text_sub']}]Menunggu {delay_seconds} detik sebelum pembelian berikutnya...[/]")
            time.sleep(delay_seconds)

    # Ringkasan hasil
    console.print(f"[{theme['text_title']}]Total pembelian sukses {len(successful_purchases)}/{n}[/]")
    console.print(f"Family: {family_name}\nVariant: {target_variant['name']}\nOption: {option_order}. {option_name} - Rp{option_price}")
    if successful_purchases:
        console.print("-"*55)
        console.print("Successful purchases:")
        for idx, purchase in enumerate(successful_purchases, start=1):
            console.print(f"{idx}. {purchase}")
    console.print("-"*55)
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
    active_user = AuthInstance.get_active_user()
    subscription_type = active_user.get("subscription_type", "")
    
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}
    
    # Jika pakai decoy, cek dulu
    if use_decoy:
        decoy = DecoyInstance.get_decoy("balance")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            print_panel("❌ Error", "Gagal memuat detail paket decoy.")
            pause()
            return False
        
        balance_threshold = decoy_package_detail["package_option"]["price"]
        console.print(f"[{theme['text_warning']}]Pastikan sisa balance KURANG DARI Rp{balance_threshold}![/]")
        balance_answer = console.input("Apakah anda yakin ingin melanjutkan pembelian? (y/n): ").strip().lower()
        if balance_answer != "y":
            print_panel("ℹ️ Info", "Pembelian dibatalkan oleh user.")
            pause()
            return None
    
    console.print("-"*55)
    successful_purchases = []
    
    for i in range(n):
        console.print(f"[{theme['text_title']}]Purchase {i + 1} dari {n}...[/]")
        
        api_key = AuthInstance.api_key
        tokens: dict = AuthInstance.get_active_tokens() or {}
        payment_items = []
        
        try:
            if use_decoy:
                decoy = DecoyInstance.get_decoy("balance")
                decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
                if not decoy_package_detail:
                    print_panel("❌ Error", "Gagal memuat detail paket decoy.")
                    pause()
                    return False
            
            target_package_detail = get_package(api_key, tokens, option_code)
        except Exception as e:
            print_panel("❌ Error", f"Exception saat mengambil detail paket: {e}")
            continue
        
        # Tambahkan item utama
        payment_items.append(
            PaymentItem(
                item_code=target_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=target_package_detail["package_option"]["price"],
                item_name=f"{randint(1000, 9999)} {target_package_detail['package_option']['name']}",
                tax=0,
                token_confirmation=target_package_detail["token_confirmation"],
            )
        )
        
        # Tambahkan decoy jika perlu
        if use_decoy:
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
        if use_decoy:
            overwrite_amount += decoy_package_detail["package_option"]["price"]

        try:
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=token_confirmation_idx
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    print_panel("ℹ️ Info", f"Adjusted total amount to: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=token_confirmation_idx
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        successful_purchases.append(f"Purchase {i + 1}")
                        print_panel("✅ Success", "Purchase berhasil!")
                        if pause_on_success:
                            pause()
            else:
                successful_purchases.append(f"Purchase {i + 1}")
                print_panel("✅ Success", "Purchase berhasil!")
                if pause_on_success:
                    pause()
        except Exception as e:
            print_panel("❌ Error", f"Exception saat membuat order: {e}")
        
        console.print("-"*55)

        if delay_seconds > 0 and i < n - 1:
            console.print(f"[{theme['text_sub']}]Menunggu {delay_seconds} detik sebelum pembelian berikutnya...[/]")
            time.sleep(delay_seconds)

    # Ringkasan hasil
    console.print(f"[{theme['text_title']}]Total pembelian sukses {len(successful_purchases)}/{n}[/]")
    if successful_purchases:
        console.print("-"*55)
        console.print("Successful purchases:")
        for idx, purchase in enumerate(successful_purchases, start=1):
            console.print(f"{idx}. {purchase}")
    console.print("-"*55)
    pause()
    return True
