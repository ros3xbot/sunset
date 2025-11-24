from app.menus.util import clear_screen, pause, print_panel, get_theme
from app.client.engsel import get_notification_detail, dashboard_segments
from app.service.auth import AuthInstance
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

console = Console()

def show_notification_menu():
    theme = get_theme()
    in_notification_menu = True
    while in_notification_menu:
        clear_screen()
        console.print(Panel(
            Align.center("📩 Fetching notifications...", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()

        notifications_res = dashboard_segments(api_key, tokens)
        if not notifications_res:
            print_panel("ℹ️ Info", "No notifications found.")
            pause()
            return

        notifications = notifications_res.get("data", {}).get("notification", {}).get("data", [])
        if not notifications:
            print_panel("ℹ️ Info", "No notifications available.")
            pause()
            return

        console.rule(f"[{theme['text_title']}]📢 Notifications[/]")

        unread_count = 0
        for idx, notification in enumerate(notifications, start=1):
            is_read = notification.get("is_read", False)
            full_message = notification.get("full_message", "")
            brief_message = notification.get("brief_message", "")
            time = notification.get("timestamp", "")

            status = "READ" if is_read else "UNREAD"
            if not is_read:
                unread_count += 1

            notif_text = Text()
            notif_text.append(f"🔔 Notification {idx}\n", style="bold")
            notif_text.append("Status: ", style=theme["text_key"])
            notif_text.append(f"{status}\n", style=theme["text_err"] if status == "UNREAD" else theme["text_ok"])
            notif_text.append("Pesan Singkat: ", style=theme["text_key"])
            notif_text.append(f"{brief_message}\n", style=theme["text_body"])
            notif_text.append("Waktu: ", style=theme["text_key"])
            notif_text.append(f"{time}\n", style=theme["text_sub"])
            notif_text.append("Pesan Lengkap:\n", style=theme["text_key"])
            notif_text.append(f"{full_message}\n", style=theme["text_body"])

            console.print(Panel(
                notif_text,
                border_style=theme["border_info"],
                padding=(0, 1),
                expand=True
            ))

        console.print(f"[{theme['text_title']}]Total: {len(notifications)} | Unread: {unread_count}[/]")

        # Navigasi konsisten
        console.rule(f"[{theme['text_title']}]🔧 Menu[/]")
        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("1", "📖 Read All Unread Notifications")
        nav_table.add_row("2", "📌 Mark Single Notification as Read (masukkan nomor)")
        nav_table.add_row("00", f"[{theme['text_sub']}]↩️ Back to Main Menu[/]")

        console.print(Panel(
            nav_table,
            border_style=theme["border_primary"],
            padding=(0, 1),
            expand=True
        ))

        choice = console.input(f"[{theme['text_sub']}]Pilihan:[/{theme['text_sub']}] ").strip()
        if choice == "1":
            for notification in notifications:
                if notification.get("is_read", False):
                    continue
                notification_id = notification.get("notification_id")
                detail = get_notification_detail(api_key, tokens, notification_id)
                if detail:
                    print_panel("✅ Info", f"Mark as READ notification ID: {notification_id}")
            pause()

        elif choice == "2":
            nomor = console.input(f"[{theme['text_sub']}]Masukkan nomor notifikasi:[/{theme['text_sub']}] ").strip()
            if not nomor.isdigit():
                print_panel("❌ Error", "Nomor tidak valid.")
                pause()
                continue
            nomor = int(nomor)
            selected = next((n for i, n in enumerate(notifications, start=1) if i == nomor), None)
            if not selected:
                print_panel("❌ Error", "Nomor notifikasi tidak ditemukan.")
                pause()
                continue
            if selected.get("is_read", False):
                print_panel("ℹ️ Info", "Notifikasi sudah ditandai READ.")
                pause()
                continue
            notification_id = selected.get("notification_id")
            detail = get_notification_detail(api_key, tokens, notification_id)
            if detail:
                print_panel("✅ Info", f"Mark as READ notification ID: {notification_id}")
            pause()

        elif choice == "00":
            in_notification_menu = False

        else:
            print_panel("⚠️ Error", "Invalid choice. Please try again.")
            pause()
