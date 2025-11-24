from app.menus.util import clear_screen, pause, print_panel
from app.client.engsel import get_notification_detail, dashboard_segments
from app.service.auth import AuthInstance
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.box import MINIMAL_DOUBLE_HEAD

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

        # Header otomatis sesuai lebar CLI
        console.rule("[bold blue]📢 Notifications[/]")

        # Tabel notifikasi
        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", style="cyan", width=4)
        table.add_column("Status", style="magenta", width=8)
        table.add_column("Pesan Singkat", style="white")
        table.add_column("Waktu", style="green")
        table.add_column("Pesan Lengkap", style="yellow")

        unread_count = 0
        for idx, notification in enumerate(notifications, start=1):
            is_read = notification.get("is_read", False)
            full_message = notification.get("full_message", "")
            brief_message = notification.get("brief_message", "")
            time = notification.get("timestamp", "")

            status = "READ" if is_read else "UNREAD"
            if not is_read:
                unread_count += 1

            table.add_row(str(idx), status, brief_message, time, full_message)

        console.print(table)
        console.print(f"Total: {len(notifications)} | Unread: {unread_count}")

        # Navigasi
        console.rule("[bold green]🔧 Menu[/]")
        nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav.add_column(justify="right", style="cyan", width=6)
        nav.add_column(style="white")
        nav.add_row("1", "📖 Read All Unread Notifications")
        nav.add_row("00", "↩️ Back to Main Menu")

        console.print(nav)

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
        elif choice == "00":
            in_notification_menu = False
        else:
            print_panel("⚠️ Error", "Invalid choice. Please try again.")
            pause()
