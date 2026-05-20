"""Utilities Panel — developer tools: converters, calculators, reference charts."""

import base64
import binascii
import colorsys
import html
import ipaddress
import json
import re
import subprocess
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from functools import lru_cache

from rich.text import Text
from rich.table import Table
from rich import box as rich_box

from ..renderer import Renderer
from ..config import Config
from ..widgets.menu import MenuItem, render_menu, render_key_hints, prompt_choice


_TOOLS = [
    ("1", "ASCII Lookup",       "char ↔ decimal, hex, binary, octal, unicode"),
    ("2", "Base Converter",     "dec ↔ hex ↔ bin ↔ oct"),
    ("3", "HTML Entities",      "encode / decode HTML special characters"),
    ("4", "Color Converter",    "hex ↔ RGB ↔ HSL ↔ HSV"),
    ("5", "IP Address Info",    "parse, classify, and break down an IP address"),
    ("6", "Subnet Calculator",  "CIDR to host range, mask, broadcast, type"),
    ("7", "IPv4 / IPv6 Charts", "address classes, private ranges, and special IPs"),
    ("8", "Base64",             "encode / decode text or bytes"),
    ("9", "URL Encoder",        "percent-encode / decode a URL or query string"),
    ("0", "Timestamp",          "Unix epoch ↔ human-readable date/time (UTC)"),
    ("t", "Traceroute Globe",   "trace a route and map hops on an ASCII world map"),
]


def show(r: Renderer, cfg: Config) -> dict:
    while True:
        r.clear()
        mode = r.layout_mode(cfg.layout)
        t = r.theme

        if cfg.show_breadcrumbs:
            r.breadcrumb(["CODEX", "Utilities"], mode)
            r.blank()

        r.rule("UTILITIES PANEL")
        r.blank()

        sub = Text("  Developer tools — converters, calculators, and reference charts.",
                   style=t.s("subtitle"))
        r.pad_print(sub, mode)
        r.blank()

        items = [MenuItem(key, label, hint=hint) for key, label, hint in _TOOLS]
        items.append(MenuItem("q", "Back", hint="return to previous screen"))
        render_menu(r, items, compact=(mode == "compact"), mode=mode)
        r.blank()
        r.rule()
        r.blank()

        valid = [key for key, _, _ in _TOOLS] + ["q"]
        choice = prompt_choice(r, valid)

        if choice == "q":
            return {"screen": "home", "args": {}}

        dispatch = {
            "1": _show_ascii,
            "2": _show_baseconv,
            "3": _show_html,
            "4": _show_color,
            "5": _show_ip,
            "6": _show_subnet,
            "7": _show_ip_charts,
            "8": _show_base64,
            "9": _show_url,
            "0": _show_timestamp,
            "t": _show_traceroute,
        }
        if choice in dispatch:
            dispatch[choice](r, cfg)


# ── Helpers ────────────────────────────────────────────────────────────────


def _header(r: Renderer, cfg: Config, title: str) -> str:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme
    if cfg.show_breadcrumbs:
        r.breadcrumb(["CODEX", "Utilities", title], mode)
        r.blank()
    r.rule(title.upper())
    r.blank()
    return mode


def _result_table(r: Renderer, cfg: Config, rows: list[tuple[str, str]], mode: str) -> None:
    t = r.theme
    tbl = Table(box=rich_box.SIMPLE, show_header=False, padding=(0, 2),
                border_style=t.s("panel_border"))
    tbl.add_column("field", style=t.s("label"), no_wrap=True)
    tbl.add_column("value", style=t.s("value"), overflow="fold")
    for label, value in rows:
        tbl.add_row(label, value)
    r.blank()
    r.pad_print(tbl, mode)
    r.blank()


def _ask(r: Renderer, prompt_text: str, mode: str) -> str:
    """Prompt for input; return stripped string."""
    t = r.theme
    line = Text(f"  {prompt_text}: ", style=t.s("subtitle"))
    r.pad_print(line, mode)
    hints = Text("  ", style="")
    r.pad_print(hints, mode)
    try:
        raw = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        raw = ""
    return raw


def _nav_hint(r: Renderer, mode: str) -> str:
    render_key_hints(r, [("enter", "convert another"), ("q", "back")], mode)
    r.blank()
    try:
        return input("  > ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return "q"


# ── Tool 1: ASCII Lookup ───────────────────────────────────────────────────


def _show_ascii(r: Renderer, cfg: Config) -> None:
    while True:
        mode = _header(r, cfg, "ASCII Lookup")
        t = r.theme

        desc = Text("  Enter a character, decimal (65), hex (0x41), or binary (01000001):",
                    style=t.s("subtitle"))
        r.pad_print(desc, mode)
        r.blank()

        raw = _ask(r, "", mode)
        if not raw or raw == "q":
            return

        codepoint = _parse_ascii_input(raw)
        if codepoint is None:
            r.error("  Could not parse input. Try: A  or  65  or  0x41  or  01000001")
            r.blank()
            render_key_hints(r, [("enter", "try again"), ("q", "back")], mode)
            r.blank()
            choice = input("  > ").strip().lower()
            if choice == "q":
                return
            continue

        char = chr(codepoint)
        try:
            uname = unicodedata.name(char)
        except ValueError:
            uname = "(control character)"

        html_named = _html_entity(char)

        rows = [
            ("Character", repr(char)[1:-1]),
            ("Decimal",   str(codepoint)),
            ("Hex",       f"0x{codepoint:02X}"),
            ("Octal",     f"0o{codepoint:o}"),
            ("Binary",    f"0b{codepoint:08b}"),
            ("Unicode",   f"U+{codepoint:04X}  {uname}"),
            ("HTML entity", html_named),
        ]
        _result_table(r, cfg, rows, mode)

        choice = _nav_hint(r, mode)
        if choice == "q":
            return


def _parse_ascii_input(raw: str) -> int | None:
    raw = raw.strip()
    try:
        if raw.startswith("0x") or raw.startswith("0X"):
            return int(raw, 16)
        if raw.startswith("0b") or raw.startswith("0B"):
            return int(raw, 2)
        if raw.startswith("0o") or raw.startswith("0O"):
            return int(raw, 8)
        if raw.isdigit():
            return int(raw)
        if len(raw) == 1:
            return ord(raw)
        if all(c in "01" for c in raw) and len(raw) in (7, 8):
            return int(raw, 2)
    except (ValueError, OverflowError):
        pass
    return None


def _html_entity(char: str) -> str:
    named = html.escape(char, quote=True)
    if named != char:
        return f"{named}  (or &#x{ord(char):X};)"
    cp = ord(char)
    if cp < 32 or cp > 126:
        return f"&#x{cp:X};"
    return f"&#x{cp:X};"


# ── Tool 2: Base Converter ─────────────────────────────────────────────────


def _show_baseconv(r: Renderer, cfg: Config) -> None:
    while True:
        mode = _header(r, cfg, "Base Converter")
        t = r.theme

        desc = Text("  Enter a number in any base: decimal (255), hex (0xff), binary (0b11111111), octal (0o377):",
                    style=t.s("subtitle"))
        r.pad_print(desc, mode)
        r.blank()

        raw = _ask(r, "", mode)
        if not raw or raw == "q":
            return

        try:
            n = _parse_number(raw)
        except ValueError as e:
            r.error(f"  {e}")
            r.blank()
            choice = _nav_hint(r, mode)
            if choice == "q":
                return
            continue

        rows = [
            ("Decimal", str(n)),
            ("Hex",     f"0x{n:X}  ({n:x})"),
            ("Binary",  f"0b{n:b}  ({n:08b} padded)"),
            ("Octal",   f"0o{n:o}"),
        ]
        if n <= 0x10FFFF:
            try:
                rows.append(("Unicode char", chr(n) + f"  U+{n:04X}"))
            except (ValueError, OverflowError):
                pass

        _result_table(r, cfg, rows, mode)

        choice = _nav_hint(r, mode)
        if choice == "q":
            return


def _parse_number(raw: str) -> int:
    raw = raw.strip().lower().replace(" ", "").replace("_", "")
    try:
        if raw.startswith("0x"):
            return int(raw, 16)
        if raw.startswith("0b"):
            return int(raw, 2)
        if raw.startswith("0o"):
            return int(raw, 8)
        return int(raw, 0)
    except ValueError:
        raise ValueError(f"Cannot parse '{raw}' — use decimal, 0x hex, 0b binary, or 0o octal")


# ── Tool 3: HTML Entities ──────────────────────────────────────────────────


def _show_html(r: Renderer, cfg: Config) -> None:
    while True:
        mode = _header(r, cfg, "HTML Entities")
        t = r.theme

        desc = Text("  Enter text to encode, or HTML like &lt;tag&gt; to decode:",
                    style=t.s("subtitle"))
        r.pad_print(desc, mode)
        r.blank()

        raw = _ask(r, "", mode)
        if not raw or raw == "q":
            return

        encoded = html.escape(raw, quote=True)
        decoded = html.unescape(raw)

        rows = [
            ("Input",   raw),
            ("Encoded", encoded),
            ("Decoded", decoded),
        ]
        _result_table(r, cfg, rows, mode)

        choice = _nav_hint(r, mode)
        if choice == "q":
            return


# ── Tool 4: Color Converter ────────────────────────────────────────────────


def _show_color(r: Renderer, cfg: Config) -> None:
    while True:
        mode = _header(r, cfg, "Color Converter")
        t = r.theme

        desc = Text("  Enter a color — #hex, rgb(r,g,b), or hsl(h,s%,l%):",
                    style=t.s("subtitle"))
        r.pad_print(desc, mode)
        r.blank()

        raw = _ask(r, "", mode)
        if not raw or raw == "q":
            return

        try:
            r8, g8, b8 = _parse_color(raw)
        except ValueError as e:
            r.error(f"  {e}")
            r.blank()
            choice = _nav_hint(r, mode)
            if choice == "q":
                return
            continue

        rf, gf, bf = r8 / 255.0, g8 / 255.0, b8 / 255.0
        h, l, s = colorsys.rgb_to_hls(rf, gf, bf)
        hv, sv, v = colorsys.rgb_to_hsv(rf, gf, bf)

        ansi_idx = _nearest_ansi256(r8, g8, b8)

        rows = [
            ("HEX",      f"#{r8:02X}{g8:02X}{b8:02X}"),
            ("RGB",      f"rgb({r8}, {g8}, {b8})"),
            ("HSL",      f"hsl({round(h * 360)}°, {round(s * 100)}%, {round(l * 100)}%)"),
            ("HSV",      f"hsv({round(hv * 360)}°, {round(sv * 100)}%, {round(v * 100)}%)"),
            ("ANSI 256", f"{ansi_idx}  (nearest terminal color)"),
        ]
        _result_table(r, cfg, rows, mode)

        choice = _nav_hint(r, mode)
        if choice == "q":
            return


def _parse_color(raw: str) -> tuple[int, int, int]:
    import re
    raw = raw.strip()

    if raw.startswith("#"):
        h = raw[1:]
        if len(h) == 3:
            h = h[0]*2 + h[1]*2 + h[2]*2
        if len(h) != 6:
            raise ValueError(f"Invalid hex color: {raw}")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    m = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', raw, re.I)
    if m:
        r8, g8, b8 = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if any(x > 255 for x in (r8, g8, b8)):
            raise ValueError("RGB values must be 0-255")
        return r8, g8, b8

    m = re.match(r'hsl\s*\(\s*(\d+)\s*,\s*(\d+)%?\s*,\s*(\d+)%?\s*\)', raw, re.I)
    if m:
        h_deg, s_pct, l_pct = int(m.group(1)), int(m.group(2)), int(m.group(3))
        rf, gf, bf = colorsys.hls_to_rgb(h_deg / 360.0, l_pct / 100.0, s_pct / 100.0)
        return round(rf * 255), round(gf * 255), round(bf * 255)

    raise ValueError(f"Cannot parse color '{raw}' — use #hex, rgb(r,g,b), or hsl(h,s%,l%)")


def _nearest_ansi256(r8: int, g8: int, b8: int) -> int:
    best, best_d = 0, float("inf")
    for i in range(16, 232):
        idx = i - 16
        bv = (idx % 6) * 40 + 55 if (idx % 6) else 0
        gv = ((idx // 6) % 6) * 40 + 55 if ((idx // 6) % 6) else 0
        rv = (idx // 36) * 40 + 55 if (idx // 36) else 0
        d = (r8 - rv)**2 + (g8 - gv)**2 + (b8 - bv)**2
        if d < best_d:
            best_d, best = d, i
    return best


# ── Tool 5: IP Address Info ────────────────────────────────────────────────


def _show_ip(r: Renderer, cfg: Config) -> None:
    while True:
        mode = _header(r, cfg, "IP Address Info")
        t = r.theme

        desc = Text("  Enter an IPv4 or IPv6 address (e.g. 192.168.1.1 or fe80::1):",
                    style=t.s("subtitle"))
        r.pad_print(desc, mode)
        r.blank()

        raw = _ask(r, "", mode)
        if not raw or raw == "q":
            return

        try:
            addr = ipaddress.ip_address(raw.strip())
        except ValueError:
            r.error(f"  Not a valid IP address: {raw}")
            r.blank()
            choice = _nav_hint(r, mode)
            if choice == "q":
                return
            continue

        rows = _ip_info_rows(addr)
        _result_table(r, cfg, rows, mode)

        choice = _nav_hint(r, mode)
        if choice == "q":
            return


def _ip_info_rows(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = [("Address", str(addr))]

    if isinstance(addr, ipaddress.IPv4Address):
        rows.append(("Version", "IPv4"))
        packed = addr.packed
        rows.append(("Binary",  ".".join(f"{b:08b}" for b in packed)))
        rows.append(("Decimal", str(int(addr))))
        rows.append(("Hex",     "0x" + addr.packed.hex().upper()))

        # Classification
        if addr.is_private:
            rows.append(("Type", "Private (RFC 1918)"))
        elif addr.is_loopback:
            rows.append(("Type", "Loopback"))
        elif addr.is_link_local:
            rows.append(("Type", "Link-local (APIPA)"))
        elif addr.is_multicast:
            rows.append(("Type", "Multicast (Class D)"))
        elif addr.is_reserved:
            rows.append(("Type", "Reserved"))
        else:
            rows.append(("Type", "Public / Global unicast"))

        # Class
        first = int(addr) >> 24
        if first < 128:
            cls = "Class A  (0.0.0.0 – 127.255.255.255)"
        elif first < 192:
            cls = "Class B  (128.0.0.0 – 191.255.255.255)"
        elif first < 224:
            cls = "Class C  (192.0.0.0 – 223.255.255.255)"
        elif first < 240:
            cls = "Class D — multicast"
        else:
            cls = "Class E — reserved"
        rows.append(("IP class", cls))

        rows.append(("Reverse DNS", ".".join(reversed(str(addr).split("."))) + ".in-addr.arpa"))

    else:
        rows.append(("Version",    "IPv6"))
        rows.append(("Expanded",   addr.exploded))
        rows.append(("Compressed", addr.compressed))
        rows.append(("Hex",        "0x" + addr.packed.hex().upper()))

        if addr.is_loopback:
            rows.append(("Type", "Loopback (::1)"))
        elif addr.is_link_local:
            rows.append(("Type", "Link-local (fe80::/10)"))
        elif addr.is_private:
            rows.append(("Type", "Unique local (fc00::/7)"))
        elif addr.is_multicast:
            rows.append(("Type", "Multicast (ff00::/8)"))
        elif addr.is_global:
            rows.append(("Type", "Global unicast"))
        else:
            rows.append(("Type", "Unspecified / other"))

        if addr.ipv4_mapped:
            rows.append(("IPv4-mapped", str(addr.ipv4_mapped)))

        rows.append(("Reverse DNS", addr.reverse_pointer))

    return rows


# ── Tool 6: Subnet Calculator ──────────────────────────────────────────────


def _show_subnet(r: Renderer, cfg: Config) -> None:
    while True:
        mode = _header(r, cfg, "Subnet Calculator")
        t = r.theme

        desc = Text("  Enter CIDR notation (e.g. 192.168.1.0/24 or 10.0.0.0/8):",
                    style=t.s("subtitle"))
        r.pad_print(desc, mode)
        r.blank()

        raw = _ask(r, "", mode)
        if not raw or raw == "q":
            return

        try:
            net = ipaddress.ip_network(raw.strip(), strict=False)
        except ValueError:
            r.error(f"  Not a valid CIDR network: {raw}")
            r.blank()
            choice = _nav_hint(r, mode)
            if choice == "q":
                return
            continue

        rows = _subnet_rows(net)
        _result_table(r, cfg, rows, mode)

        choice = _nav_hint(r, mode)
        if choice == "q":
            return


def _subnet_rows(net: ipaddress.IPv4Network | ipaddress.IPv6Network) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = [("Network", str(net))]

    if isinstance(net, ipaddress.IPv4Network):
        rows.append(("Subnet mask",   str(net.netmask)))
        rows.append(("Wildcard mask", str(net.hostmask)))
        rows.append(("Network addr",  str(net.network_address)))
        rows.append(("Broadcast",     str(net.broadcast_address)))

        num_hosts = net.num_addresses
        usable = max(0, num_hosts - 2) if net.prefixlen < 31 else num_hosts
        rows.append(("Total hosts",  f"{num_hosts:,}  ({usable:,} usable)"))

        hosts = list(net.hosts())
        if hosts:
            rows.append(("Host range", f"{hosts[0]}  –  {hosts[-1]}"))

        first = int(net.network_address) >> 24
        if first < 128:
            cls = "Class A"
        elif first < 192:
            cls = "Class B"
        elif first < 224:
            cls = "Class C"
        elif first < 240:
            cls = "Class D — multicast"
        else:
            cls = "Class E — reserved"
        rows.append(("IP class", cls))

        if net.is_private:
            rows.append(("Type", "Private (RFC 1918)"))
        elif net.is_loopback:
            rows.append(("Type", "Loopback"))
        elif net.is_link_local:
            rows.append(("Type", "Link-local"))
        elif net.is_multicast:
            rows.append(("Type", "Multicast"))
        else:
            rows.append(("Type", "Public"))

    else:
        rows.append(("Prefix length",   f"/{net.prefixlen}"))
        rows.append(("Network address", str(net.network_address)))
        rows.append(("Total addresses", f"{net.num_addresses:,}"))
        rows.append(("Type", "IPv6"))

    return rows


# ── Tool 7: IPv4 / IPv6 Charts ─────────────────────────────────────────────


def _show_ip_charts(r: Renderer, cfg: Config) -> None:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    if cfg.show_breadcrumbs:
        r.breadcrumb(["CODEX", "Utilities", "IPv4 / IPv6 Charts"], mode)
        r.blank()

    r.rule("IPv4 / IPv6 REFERENCE CHARTS")
    r.blank()

    _print_section(r, cfg, mode, "IPv4 Address Classes", [
        ("Class A",  "0.0.0.0    –  127.255.255.255",  "/8",   "16,777,214 hosts/network"),
        ("Class B",  "128.0.0.0  –  191.255.255.255",  "/16",  "65,534 hosts/network"),
        ("Class C",  "192.0.0.0  –  223.255.255.255",  "/24",  "254 hosts/network"),
        ("Class D",  "224.0.0.0  –  239.255.255.255",  "—",    "Multicast"),
        ("Class E",  "240.0.0.0  –  255.255.255.255",  "—",    "Reserved / experimental"),
    ])

    r.blank()
    _print_section(r, cfg, mode, "Private Ranges (RFC 1918)", [
        ("10.0.0.0/8",      "10.0.0.0    –  10.255.255.255",    "/8-/32",  "~16.7M hosts"),
        ("172.16.0.0/12",   "172.16.0.0  –  172.31.255.255",    "/12-/32", "~1M hosts"),
        ("192.168.0.0/16",  "192.168.0.0 –  192.168.255.255",   "/16-/32", "~65K hosts"),
    ])

    r.blank()
    _print_section(r, cfg, mode, "Special IPv4 Addresses", [
        ("0.0.0.0",          "Default route / unspecified",       "",  ""),
        ("127.0.0.1",        "Loopback",                          "",  "equiv. to localhost"),
        ("169.254.0.0/16",   "Link-local (APIPA)",                "",  "no DHCP server found"),
        ("255.255.255.255",  "Limited broadcast",                 "",  "all hosts on segment"),
    ])

    r.blank()
    _print_section(r, cfg, mode, "IPv6 Address Types", [
        ("::1",          "Loopback",               "",         "equiv. to 127.0.0.1"),
        ("::",           "Unspecified",             "",         "equiv. to 0.0.0.0"),
        ("fe80::/10",    "Link-local",              "auto",     "assigned on every interface"),
        ("fc00::/7",     "Unique local (ULA)",      "private",  "equiv. to RFC 1918"),
        ("2000::/3",     "Global unicast",          "public",   "routable on the internet"),
        ("ff00::/8",     "Multicast",               "",         "replaces IPv4 broadcast"),
        ("::ffff:0:0/96","IPv4-mapped IPv6",         "",         "embed IPv4 in IPv6"),
    ])

    r.blank()
    _print_section(r, cfg, mode, "Common CIDR Quick Reference", [
        ("/8",   "255.0.0.0",       "16,777,214", "hosts"),
        ("/16",  "255.255.0.0",     "65,534",     "hosts"),
        ("/24",  "255.255.255.0",   "254",        "hosts"),
        ("/25",  "255.255.255.128", "126",        "hosts"),
        ("/26",  "255.255.255.192", "62",         "hosts"),
        ("/27",  "255.255.255.224", "30",         "hosts"),
        ("/28",  "255.255.255.240", "14",         "hosts"),
        ("/29",  "255.255.255.248", "6",          "hosts"),
        ("/30",  "255.255.255.252", "2",          "hosts (point-to-point)"),
        ("/32",  "255.255.255.255", "1",          "host (single address)"),
    ])

    r.blank()
    r.rule()
    r.blank()
    render_key_hints(r, [("q", "back")], mode)
    r.blank()

    try:
        input("  > ")
    except (EOFError, KeyboardInterrupt):
        pass


def _print_section(r: Renderer, cfg: Config, mode: str,
                   title: str, rows: list[tuple]) -> None:
    t = r.theme
    heading = Text(f"  {title}", style=t.s("label"))
    r.pad_print(heading, mode)

    line = Text("  " + "─" * 65, style=t.s("muted"))
    r.pad_print(line, mode)

    for row in rows:
        cells = Text("  ")
        cells.append(f"{row[0]:<22}", style=t.s("value"))
        cells.append(f"{row[1]:<28}", style=t.s("subtitle"))
        if len(row) > 2:
            cells.append(f"{row[2]:<8}", style=t.s("accent"))
        if len(row) > 3 and row[3]:
            cells.append(f"  {row[3]}", style=t.s("muted"))
        r.pad_print(cells, mode)


# ── Tool 8: Base64 ─────────────────────────────────────────────────────────


def _show_base64(r: Renderer, cfg: Config) -> None:
    while True:
        mode = _header(r, cfg, "Base64")
        t = r.theme

        desc = Text("  Enter text to encode, or base64 string to decode:",
                    style=t.s("subtitle"))
        r.pad_print(desc, mode)
        r.blank()

        raw = _ask(r, "", mode)
        if not raw or raw == "q":
            return

        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")

        try:
            decoded_bytes = base64.b64decode(raw + "==")
            decoded = decoded_bytes.decode("utf-8", errors="replace")
        except Exception:
            decoded = "(invalid base64)"

        rows = [
            ("Input",          raw),
            ("Encoded",        encoded),
            ("Decoded",        decoded),
            ("URL-safe enc.",  base64.urlsafe_b64encode(raw.encode()).decode()),
        ]
        _result_table(r, cfg, rows, mode)

        choice = _nav_hint(r, mode)
        if choice == "q":
            return


# ── Tool 9: URL Encoder ────────────────────────────────────────────────────


def _show_url(r: Renderer, cfg: Config) -> None:
    while True:
        mode = _header(r, cfg, "URL Encoder")
        t = r.theme

        desc = Text("  Enter a URL or string to percent-encode / decode:",
                    style=t.s("subtitle"))
        r.pad_print(desc, mode)
        r.blank()

        raw = _ask(r, "", mode)
        if not raw or raw == "q":
            return

        encoded_full = urllib.parse.quote(raw, safe="")
        encoded_path = urllib.parse.quote(raw, safe="/:@!$&'()*+,;=")
        decoded = urllib.parse.unquote(raw)

        rows = [
            ("Input",          raw),
            ("Encoded (full)", encoded_full),
            ("Encoded (path)", encoded_path),
            ("Decoded",        decoded),
        ]
        _result_table(r, cfg, rows, mode)

        choice = _nav_hint(r, mode)
        if choice == "q":
            return


# ── Tool 0: Timestamp ──────────────────────────────────────────────────────


def _show_timestamp(r: Renderer, cfg: Config) -> None:
    while True:
        mode = _header(r, cfg, "Timestamp Converter")
        t = r.theme

        now_ts = int(datetime.now(tz=timezone.utc).timestamp())
        desc = Text(f"  Enter a Unix timestamp (seconds since epoch) or leave blank for now ({now_ts}):",
                    style=t.s("subtitle"))
        r.pad_print(desc, mode)
        r.blank()

        raw = _ask(r, "", mode)
        if raw == "q":
            return

        raw = raw.strip()
        if not raw:
            raw = str(now_ts)

        try:
            ts = int(raw)
        except ValueError:
            r.error(f"  Not a valid integer timestamp: {raw}")
            r.blank()
            choice = _nav_hint(r, mode)
            if choice == "q":
                return
            continue

        try:
            dt_utc = datetime.fromtimestamp(ts, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            r.error(f"  Timestamp out of range: {ts}")
            r.blank()
            choice = _nav_hint(r, mode)
            if choice == "q":
                return
            continue

        rows = [
            ("Unix timestamp", str(ts)),
            ("UTC",            dt_utc.strftime("%Y-%m-%d %H:%M:%S UTC")),
            ("ISO 8601",       dt_utc.isoformat()),
            ("RFC 2822",       dt_utc.strftime("%a, %d %b %Y %H:%M:%S +0000")),
            ("Day of week",    dt_utc.strftime("%A")),
            ("Day of year",    dt_utc.strftime("Day %j of %Y")),
            ("Milliseconds",   str(ts * 1000)),
        ]
        _result_table(r, cfg, rows, mode)

        choice = _nav_hint(r, mode)
        if choice == "q":
            return


# ── Tool t: Traceroute Globe ───────────────────────────────────────────────────

# Geographic rectangles (lat_min, lat_max, lon_min, lon_max) for world map
_LAND_REGIONS: list[tuple[int, int, int, int]] = [
    (50,  73, -140,  -55),   # Canada
    (58,  72, -165, -140),   # Alaska
    (24,  50, -125,  -65),   # Continental USA
    (10,  30, -118,  -77),   # Mexico / Central America
    (60,  84,  -55,  -17),   # Greenland
    (-5,  12,  -82,  -48),   # Northern South America
    (-56,  -5, -82,  -35),   # Southern South America
    (36,  72,  -12,   32),   # Europe
    (64,  68,  -24,  -14),   # Iceland
    (50,  73,   28,   68),   # Russia West
    (50,  73,   68,  145),   # Russia Siberia
    (66,  82,   28,  145),   # Arctic Russia
    (20,  38,  -18,   38),   # North Africa
    (-12, 20,  -18,   50),   # Sub-Saharan Africa
    (-35,-12,   14,   40),   # Southern Africa
    (-26,-11,   43,   51),   # Madagascar
    (12,  38,   32,   62),   # Middle East / Arabia
    (25,  40,   44,   64),   # Iran / Afghanistan
    ( 8,  35,   67,   88),   # India / Pakistan
    (-8,  28,   94,  142),   # Southeast Asia
    (18,  56,   99,  142),   # East Asia / China
    (30,  46,  130,  146),   # Japan
    (-38,-10,  113,  154),   # Australia
    (-47,-33,  166,  178),   # New Zealand
    (-90,-66, -180,  180),   # Antarctica
]


@lru_cache(maxsize=1)
def _build_world_map() -> list[str]:
    """Generate 72x23 ASCII world map from geographic land regions."""
    W, H = 72, 23
    grid = [[" "] * W for _ in range(H)]
    for lat_min, lat_max, lon_min, lon_max in _LAND_REGIONS:
        lat = float(lat_min)
        while lat <= lat_max:
            lon = float(lon_min)
            while lon <= lon_max:
                x = min(W - 1, max(0, int((lon + 180) / 360 * W)))
                y = min(H - 1, max(0, int((90 - lat) / 180 * H)))
                grid[y][x] = "\xb7"  # middle dot for land
                lon += 4.0
            lat += 3.0
    return ["".join(row) for row in grid]


def _show_traceroute(r: Renderer, cfg: Config) -> None:
    while True:
        mode = _header(r, cfg, "Traceroute Globe")
        t = r.theme

        r.pad_print(Text("  Enter a hostname or IP address to trace the route:",
                         style=t.s("subtitle")), mode)
        r.pad_print(Text("  Geolocation uses ip-api.com (free, requires network).",
                         style=t.s("muted")), mode)
        r.blank()

        raw = _ask(r, "", mode)
        if not raw or raw == "q":
            return

        r.clear()
        if cfg.show_breadcrumbs:
            r.breadcrumb(["CODEX", "Utilities", "Traceroute Globe"], mode)
            r.blank()
        r.rule(f"  TRACING: {raw}  ")
        r.blank()

        hops = _run_traceroute(r, raw, t, mode)

        if not hops:
            r.pad_print(Text("  No route data. Check hostname and network connectivity.",
                             style=t.s("warning")), mode)
        else:
            r.blank()
            r.pad_print(Text("  Looking up hop locations...", style=t.s("muted")), mode)
            hops = _geolocate_hops(hops)
            r.clear()
            if cfg.show_breadcrumbs:
                r.breadcrumb(["CODEX", "Utilities", "Traceroute Globe"], mode)
                r.blank()
            r.rule(f"  ROUTE MAP: {raw}  ")
            _render_hop_table(r, hops, mode)
            _render_world_map_with_hops(r, hops, mode)

        r.blank()
        r.rule()
        r.blank()
        choice = _nav_hint(r, mode)
        if choice == "q":
            return


def _run_traceroute(r: Renderer, host: str, t, mode: str) -> list[dict]:
    for cmd in (
        ["traceroute", "-n", "-m", "20", "-w", "2", host],
        ["tracert", "-d", "-h", "20", host],
    ):
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
        except FileNotFoundError:
            continue
        hops: list[dict] = []
        assert proc.stdout is not None
        for line in proc.stdout:
            stripped = line.rstrip()
            if stripped:
                r.pad_print(Text(f"  {stripped}", style=t.s("muted")), mode)
                hop = _parse_hop_line(stripped)
                if hop:
                    hops.append(hop)
        proc.wait()
        return hops
    r.pad_print(Text("  traceroute / tracert not found on this system.", style=t.s("error")), mode)
    return []


def _parse_hop_line(line: str) -> dict | None:
    m = re.match(r"^\s*(\d+)\s+(?:(\d+\.\d+\.\d+\.\d+)|\*)\s*(.*)", line)
    if not m:
        return None
    ip = m.group(2) or "*"
    rtt_m = re.search(r"(\d+\.?\d*)\s*ms", m.group(3))
    return {"hop": int(m.group(1)), "ip": ip, "rtt": f"{rtt_m.group(1)} ms" if rtt_m else "*"}


def _geolocate_hops(hops: list[dict]) -> list[dict]:
    ips = [h["ip"] for h in hops if h["ip"] != "*"]
    if not ips:
        return hops
    try:
        payload = json.dumps([
            {"query": ip, "fields": "status,lat,lon,city,country,org"} for ip in ips
        ]).encode()
        req = urllib.request.Request(
            "http://ip-api.com/batch", data=payload,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            results = json.loads(resp.read())
        geo_map = {ips[i]: g for i, g in enumerate(results) if g.get("status") == "success"}
        for hop in hops:
            if hop["ip"] in geo_map:
                g = geo_map[hop["ip"]]
                hop.update({
                    "lat": g.get("lat"), "lon": g.get("lon"),
                    "city": g.get("city", ""), "country": g.get("country", ""),
                    "org": g.get("org", ""),
                })
    except Exception:
        pass  # offline or rate-limited — map still renders without geo data
    return hops


def _render_hop_table(r: Renderer, hops: list[dict], mode: str) -> None:
    t = r.theme
    tbl = Table(box=rich_box.SIMPLE, padding=(0, 1), show_header=True, expand=False)
    tbl.add_column("Hop",      style=t.s("accent"),    width=5)
    tbl.add_column("IP",       style=t.s("value"),     width=18)
    tbl.add_column("RTT",      style=t.s("muted"),     width=10)
    tbl.add_column("Location", style=t.s("menu_hint"), width=28)
    tbl.add_column("Org",      style=t.s("dim"),       width=22)
    for hop in hops:
        city    = hop.get("city", "")
        country = hop.get("country", "")
        loc = f"{city}, {country}".strip(", ") if (city or country) else "—"
        tbl.add_row(str(hop["hop"]), hop["ip"], hop["rtt"], loc, hop.get("org", "")[:22])
    r.blank()
    r.pad_print(tbl, mode)


def _render_world_map_with_hops(r: Renderer, hops: list[dict], mode: str) -> None:
    t = r.theme
    W, H = 72, 23
    base = [list(row) for row in _build_world_map()]
    for hop in hops:
        lat, lon = hop.get("lat"), hop.get("lon")
        if lat is None or lon is None:
            continue
        x = min(W - 1, max(0, int((lon + 180) / 360 * W)))
        y = min(H - 1, max(0, int((90 - lat) / 180 * H)))
        base[y][x] = str(hop["hop"]) if hop["hop"] < 10 else "+"

    lat_labels = {0: "90N", 5: "45N", 11: " 0 ", 17: "45S", 22: "90S"}
    top = "  ┌" + "─" * W + "┐"
    bot = "  └" + "─" * W + "┘"

    r.blank()
    r.pad_print(Text("  World Map  (\xb7 land  numbers = route hops)", style=t.s("label")), mode)
    r.blank()
    r.pad_print(Text(top, style=t.s("panel_border")), mode)
    for y, row_chars in enumerate(base):
        lbl = lat_labels.get(y, "   ")
        line = Text()
        line.append(f" {lbl} │", style=t.s("panel_border"))
        for ch in row_chars:
            if ch == "\xb7":
                line.append(ch, style=t.s("muted"))
            elif ch == " ":
                line.append(ch)
            else:
                line.append(ch, style=t.s("accent"))
        line.append("│", style=t.s("panel_border"))
        r.pad_print(line, mode)
    r.pad_print(Text(bot, style=t.s("panel_border")), mode)
    r.blank()
    r.pad_print(
        Text("      180W          90W           0\xb0          90E         180E",
             style=t.s("dim")), mode)
