from html.parser import HTMLParser
import os
import re
import textwrap
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich import box
from app.config.theme_config import get_theme, get_theme_style

console = Console()


def print_banner():
    theme = get_theme()
    banner_text = Align.center(
        "[bold]myXL CLI v8.9.1 sunset[/]",
        vertical="middle"
    )
    console.print(Panel(
        banner_text,
        border_style=theme["border_primary"],
        style=theme["text_title"],
        padding=(1, 2),
        expand=True,
        box=box.DOUBLE
    ))

def simple_number():
    from app.service.auth import AuthInstance
    theme = get_theme()
    active_user = AuthInstance.get_active_user()

    if not active_user:
        text = f"[bold {get_theme_style('text_err')}]Tidak ada akun aktif saat ini.[/]"
    else:
        number = active_user.get("number", "-")
        text = f"[bold {get_theme_style('text_body')}]Akun (nomor) aktif ✨ {number} ✨[/]"

    console.print(Panel(
        Align.center(text),
        border_style=get_theme_style("border_warning"),
        padding=(0, 0),
        expand=True
    ))

def clear_screen():
    print("Clearing screen...")
    os.system('cls' if os.name == 'nt' else 'clear')
    ascii_art = r"""
            _____                    _____          
           /\    \                  /\    \         
          /::\____\                /::\    \        
         /::::|   |               /::::\    \       
        /:::::|   |              /::::::\    \      
       /::::::|   |             /:::/\:::\    \     
      /:::/|::|   |            /:::/__\:::\    \    
     /:::/ |::|   |           /::::\   \:::\    \   
    /:::/  |::|___|______    /::::::\   \:::\    \  
   /:::/   |::::::::\    \  /:::/\:::\   \:::\    \ 
  /:::/    |:::::::::\____\/:::/__\:::\   \:::\____\
  \::/    / ~~~~~/:::/    /\:::\   \:::\   \::/    /
   \/____/      /:::/    /  \:::\   \:::\   \/____/ 
               /:::/    /    \:::\   \:::\    \     
              /:::/    /      \:::\   \:::\____\    
             /:::/    /        \:::\   \::/    /    
            /:::/    /          \:::\   \/____/     
           /:::/    /            \:::\    \         
          /:::/    /              \:::\____\        
          \::/    /                \::/    /        
           \/____/                  \/____/         
"""

    print(ascii_art)
    print_banner()
    simple_number()

def clear_sc():
    print("Clearing screen...")
    os.system('cls' if os.name == 'nt' else 'clear')
    ascii_art = r"""
            _____                    _____          
           /\    \                  /\    \         
          /::\____\                /::\    \        
         /::::|   |               /::::\    \       
        /:::::|   |              /::::::\    \      
       /::::::|   |             /:::/\:::\    \     
      /:::/|::|   |            /:::/__\:::\    \    
     /:::/ |::|   |           /::::\   \:::\    \   
    /:::/  |::|___|______    /::::::\   \:::\    \  
   /:::/   |::::::::\    \  /:::/\:::\   \:::\    \ 
  /:::/    |:::::::::\____\/:::/__\:::\   \:::\____\
  \::/    / ~~~~~/:::/    /\:::\   \:::\   \::/    /
   \/____/      /:::/    /  \:::\   \:::\   \/____/ 
               /:::/    /    \:::\   \:::\    \     
              /:::/    /      \:::\   \:::\____\    
             /:::/    /        \:::\   \::/    /    
            /:::/    /          \:::\   \/____/     
           /:::/    /            \:::\    \         
          /:::/    /              \:::\____\        
          \::/    /                \::/    /        
           \/____/                  \/____/         
"""

    print(ascii_art)
    print_banner()

def pause():
    input("\nPress enter to continue...")

class HTMLToText(HTMLParser):
    def __init__(self, width=80):
        super().__init__()
        self.width = width
        self.result = []
        self.in_li = False

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.in_li = True
        elif tag == "br":
            self.result.append("\n")

    def handle_endtag(self, tag):
        if tag == "li":
            self.in_li = False
            self.result.append("\n")

    def handle_data(self, data):
        text = data.strip()
        if text:
            if self.in_li:
                self.result.append(f"- {text}")
            else:
                self.result.append(text)

    def get_text(self):
        # Join and clean multiple newlines
        text = "".join(self.result)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        # Wrap lines nicely
        return "\n".join(textwrap.wrap(text, width=self.width, replace_whitespace=False))

def display_html(html_text, width=80):
    parser = HTMLToText(width=width)
    parser.feed(html_text)
    return parser.get_text()

def format_quota_byte(quota_byte: int) -> str:
    GB = 1024 ** 3 
    MB = 1024 ** 2
    KB = 1024

    if quota_byte >= GB:
        return f"{quota_byte / GB:.2f} GB"
    elif quota_byte >= MB:
        return f"{quota_byte / MB:.2f} MB"
    elif quota_byte >= KB:
        return f"{quota_byte / KB:.2f} KB"
    else:
        return f"{quota_byte} B"

def get_rupiah(value) -> str:
    value_str = str(value).strip()
    value_str = re.sub(r"^Rp\s?", "", value_str)
    match = re.match(r"([\d,]+)(.*)", value_str)
    if not match:
        return value_str

    raw_number = match.group(1).replace(",", "")
    suffix = match.group(2).strip()

    try:
        number = int(raw_number)
    except ValueError:
        return value_str

    formatted_number = f"{number:,}".replace(",", ".")
    formatted = f"{formatted_number},-"
    return f"{formatted} {suffix}" if suffix else formatted

def nav_range(label: str, count: int) -> str:
    if count <= 0:
        return f"{label} (tidak tersedia)"
    if count == 1:
        return f"{label} (1)"
    return f"{label} (1–{count})"

def live_loading(text: str, theme: dict):
    return console.status(f"[{theme['text_sub']}]{text}[/{theme['text_sub']}]", spinner="dots")

def print_panel(title, content, border_style=None):
    style = border_style or get_theme_style("border_info")
    console.print(Panel(content, title=title, title_align="left", border_style=style))

def print_success(title, content):
    console.print(Panel(content, title=title, title_align="left", border_style=get_theme_style("border_success")))

def print_error(title, content):
    console.print(Panel(content, title=title, title_align="left", border_style=get_theme_style("border_error")))

def print_warning(title, content):
    console.print(Panel(content, title=title, title_align="left", border_style=get_theme_style("border_warning")))

def print_title(text):
    console.print(Panel(
        Align.center(f"[bold {get_theme_style('text_title')}]{text}[/{get_theme_style('text_title')}]"),
        border_style=get_theme_style("border_primary"),
        padding=(0, 1),
        expand=True
    ))

def print_key_value(label, value):
    console.print(f"[{get_theme_style('text_key')}]{label}:[/] [{get_theme_style('text_value')}]{value}[/{get_theme_style('text_value')}]")

def print_info(label, value):
    console.print(f"[{get_theme_style('text_sub')}]{label}:[/{get_theme_style('text_sub')}] [{get_theme_style('text_body')}]{value}[/{get_theme_style('text_body')}]")

def print_menu(title, options):
    table = Table(title=title, box=box.SIMPLE, show_header=False)
    for key, label in options.items():
        table.add_row(f"[{get_theme_style('text_key')}]{key}[/{get_theme_style('text_key')}]", f"[{get_theme_style('text_value')}]{label}[/{get_theme_style('text_value')}]")
    console.print(table)
