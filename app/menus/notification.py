from app.menus.util import clear_screen, pause, print_panel
from app.client.engsel import get_notification_detail, dashboard_segments
from app.service.auth import AuthInstance
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def show_notification_menu():
    in_notification_menu = True
    while in_notification_menu:
        clear_screen()
        console.print(Panel("📩 Fetching notifications...", border_style="yellow"))

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

        console.rule("[bold blue]📢 Notifications[/]")

        unread_count = 0
        for idx, notification in enumerate(notifications, start=1):
            is_read = notification.get("is_read", False)
            full_message = notification.get("full_message", "")
            brief_message = notification.get("brief_message", "")
            time = notification.get("timestamp", "")

            status = "READ" if is_read else "UNREAD"
            if not is_read:
                unread_count += 1

            # Panel per notifikasi
            notif_text = Text()
            notif_text.append(f"🔔 Notification {idx}\n", style="bold")
            notif_text.append("Status: ", style="magenta")
            notif_text.append(f"{status}\n", style="cyan" if status == "UNREAD" else "green")
            notif_text.append("Pesan Singkat: ", style="yellow")
            notif_text.append(f"{brief_message}\n", style="white")
            notif_text.append("Waktu: ", style="green")
            notif_text.append(f"{time}\n", style="white")
            notif_text.append("Pesan Lengkap:\n", style="yellow")
            notif_text.append(f"{full_message}\n", style="white")

            console.print(Panel(notif_text, border_style="blue", expand=True))

        console.print(f"Total: {len(notifications)} | Unread: {unread_count}")

        # Navigasi
        console.rule("[bold green]🔧 Menu[/]")
        nav_text = (
            "1. 📖 Read All Unread Notifications\n"
            "2. 📌 Mark Single Notification as Read (masukkan nomor)\n"
            "00. ↩️ Back to Main Menu"
        )
        console.print(Panel(nav_text, border_style="green", expand=True))

        choice = console.input("Enter your choice: ").strip()
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
            nomor = console.input("Masukkan nomor notifikasi yang ingin ditandai READ: ").strip()
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
