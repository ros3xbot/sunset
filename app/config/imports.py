# Rich
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

# Utilitas internal
from app.menus.package import get_packages_by_family, show_package_details
from app.config.theme_config import get_theme
from app.menus.util import (
    clear_screen,
    pause,
    print_panel,
    get_rupiah,
    display_html,
    simple_number,
    format_quota_byte,
    nav_range
)

# Service / type yang sering dipakai
from app.service.auth import AuthInstance
from app.service.decoy import DecoyInstance
from app.service.bookmark import BookmarkInstance
from app.client.engsel import get_family, get_package, get_package_details
from app.type_dict import PaymentItem

# Inisialisasi console global
console = Console()

# __all__ untuk kontrol import *
__all__ = [
    "get_theme",
    "console",
    "Group",
    "Panel",
    "Table",
    "Text",
    "Align",
    "MINIMAL_DOUBLE_HEAD",
    "clear_screen",
    "pause",
    "print_panel",
    "get_rupiah",
    "display_html",
    "simple_number",
    "format_quota_byte",
    "nav_range",
    "AuthInstance",
    "DecoyInstance",
    "BookmarkInstance",
    "get_family",
    "get_package",
    "get_package_details",
    "PaymentItem",
    "get_packages_by_family",
    "show_package_details",
]
