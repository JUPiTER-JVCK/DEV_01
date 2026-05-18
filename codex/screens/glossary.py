"""Glossary screen — quick term lookup and definitions."""

from rich.text import Text

from ..renderer import Renderer
from ..config import Config
from ..content.loader import ContentLoader
from ..widgets.menu import prompt_input, prompt_choice


GLOSSARY: dict[str, str] = {
    "voltage":        "Electric potential difference (V). The 'pressure' that drives current.",
    "current":        "Flow of electric charge (I). Measured in Amperes (A).",
    "resistance":     "Opposition to current flow (R). Measured in Ohms (Ω).",
    "ohm":            "Unit of electrical resistance. Symbol: Ω.",
    "watt":           "Unit of power (P = V × I). Named after James Watt.",
    "capacitor":      "Electronic component that stores charge. Unit: Farad (F).",
    "inductor":       "Component that stores energy in a magnetic field. Unit: Henry (H).",
    "transistor":     "Semiconductor device used for switching and amplifying signals.",
    "diode":          "One-way valve for current. Allows flow in one direction only.",
    "register":       "Small, fast storage location inside the CPU. e.g., RAX, RBX.",
    "assembly":       "Low-level programming language directly representing CPU instructions.",
    "opcode":         "Operation code — the numeric identifier of a CPU instruction.",
    "stack":          "LIFO memory structure. Grows downward in x86. Used for function calls.",
    "heap":           "Dynamically allocated memory region. Managed by malloc/free or GC.",
    "pointer":        "Variable holding a memory address.",
    "kernel":         "Core of an OS. Manages hardware, processes, and memory.",
    "syscall":        "Request from user space to the kernel to perform a privileged action.",
    "interrupt":      "Signal that pauses CPU execution to handle an event.",
    "fiber":          "Optical fiber — transmits data as pulses of light.",
    "ethernet":       "Wired networking standard. Defined by IEEE 802.3.",
    "tcp":            "Transmission Control Protocol — reliable, ordered data delivery.",
    "ip":             "Internet Protocol — addressing and routing of packets.",
    "dns":            "Domain Name System — translates names to IP addresses.",
    "bit":            "Binary digit — 0 or 1. The smallest unit of digital information.",
    "byte":           "8 bits. Can represent 256 values (0–255).",
    "ascii":          "American Standard Code for Information Interchange. 7-bit char encoding.",
    "utf-8":          "Variable-width Unicode encoding. Backward-compatible with ASCII.",
    "recursion":      "Function that calls itself. Requires a base case to terminate.",
    "closure":        "Function that captures variables from its enclosing scope.",
    "mutex":          "Mutual exclusion lock — prevents concurrent access to shared data.",
    "semaphore":      "Signaling mechanism for concurrent programming.",
    "big-o":          "Asymptotic notation describing algorithm time/space complexity.",
    "linux":          "Open-source Unix-like operating system kernel by Linus Torvalds.",
    "bash":           "Bourne Again Shell — default shell on most Linux distributions.",
    "git":            "Distributed version control system created by Linus Torvalds.",
    "open source":    "Software with freely available, modifiable source code.",
    "esd":            "Electrostatic Discharge — can destroy sensitive electronics.",
    "arc flash":      "Dangerous electrical explosion from high-current arcing.",
}


def show(r: Renderer, cfg: Config, loader: ContentLoader) -> dict:
    while True:
        result = _glossary_loop(r, cfg, loader)
        if result.get("screen") != "glossary":
            return result


def _glossary_loop(r: Renderer, cfg: Config, loader: ContentLoader) -> dict:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    if cfg.show_breadcrumbs:
        r.breadcrumb(["CODEX", "Reference"], mode)
        r.blank()

    r.rule("  REFERENCE GLOSSARY  ")
    r.blank()

    sub = Text("  Quick definitions for key terms", style=t.s("subtitle"))
    r.pad_print(sub, mode)
    r.blank()

    line = Text()
    line.append("  [a]", style=t.s("menu_key"))
    line.append(" browse all  ", style=t.s("menu_hint"))
    line.append("[s]", style=t.s("menu_key"))
    line.append(" search term  ", style=t.s("menu_hint"))
    line.append("[q]", style=t.s("menu_key"))
    line.append(" back", style=t.s("menu_hint"))
    r.pad_print(line, mode)
    r.blank()

    choice = prompt_choice(r, ["a", "s", "q"])

    if choice == "q":
        return {"screen": "home", "args": {}}

    if choice == "a":
        return _browse_all(r, cfg)

    if choice == "s":
        query = prompt_input(r, "Term to look up")
        if query:
            return _show_term(r, cfg, query.lower())

    return {"screen": "glossary", "args": {}}


def _browse_all(r: Renderer, cfg: Config) -> dict:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    r.rule("  ALL TERMS  ")
    r.blank()

    sorted_terms = sorted(GLOSSARY.items())
    for i, (term, defn) in enumerate(sorted_terms, 1):
        line = Text()
        line.append(f"  [{i:2d}]", style=t.s("menu_number"))
        line.append(f"  {term:<20}", style=t.s("accent"))
        trunc = defn[:60] + "..." if len(defn) > 60 else defn
        line.append(trunc, style=t.s("dim"))
        r.pad_print(line, mode)
        if not cfg.compact_menus:
            r.blank()

    r.blank()
    r.rule()
    r.blank()

    hint = Text()
    hint.append("  Number for full definition  ", style=t.s("menu_hint"))
    hint.append("[q]", style=t.s("menu_key"))
    hint.append(" back", style=t.s("menu_hint"))
    r.pad_print(hint, mode)

    valid = [str(i) for i in range(1, len(sorted_terms) + 1)] + ["q"]
    choice = prompt_choice(r, valid)

    if choice == "q":
        return {"screen": "glossary", "args": {}}

    try:
        term, defn = sorted_terms[int(choice) - 1]
        return _show_term(r, cfg, term)
    except (ValueError, IndexError):
        return {"screen": "glossary", "args": {}}


def _show_term(r: Renderer, cfg: Config, query: str) -> dict:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    # Find matching terms
    matches = {k: v for k, v in GLOSSARY.items()
               if query.lower() in k.lower() or query.lower() in v.lower()}

    if not matches:
        r.blank()
        r.pad_print(Text(f"  No definition found for \"{query}\"", style=t.s("warning")), mode)
    else:
        r.rule("  DEFINITION  ")
        r.blank()
        for term, defn in matches.items():
            term_line = Text(f"  {term}", style=t.s("title"))
            r.pad_print(term_line, mode)
            defn_line = Text(f"  {defn}", style=t.s("menu_item"), overflow="fold")
            r.pad_print(defn_line, mode)
            r.blank()

    r.rule()
    r.blank()
    r.pad_print(Text("  [q] Back to Glossary", style=t.s("menu_hint")), mode)
    prompt_choice(r, ["q"])
    return {"screen": "glossary", "args": {}}
