"""ASCII art and word art for CODEX — topic banners and decorative elements."""

CODEX_BANNER_WIDE = r"""
   ██████╗ ██████╗ ██████╗ ███████╗██╗  ██╗
  ██╔════╝██╔═══██╗██╔══██╗██╔════╝╚██╗██╔╝
  ██║     ██║   ██║██║  ██║█████╗   ╚███╔╝
  ██║     ██║   ██║██║  ██║██╔══╝   ██╔██╗
  ╚██████╗╚██████╔╝██████╔╝███████╗██╔╝ ██╗
   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
"""

CODEX_BANNER_COMPACT = r"""
  ╔═╗╔═╗╔╦╗╔═╗═╗ ╦
  ║  ║ ║ ║║║╣ ╔╩╦╝
  ╚═╝╚═╝═╩╝╚═╝╩ ╚═
"""

CODEX_TAGLINE = "Interactive Terminal Learning Reference"

TOPIC_ART = {
    "physics": r"""
  +---------+
  | ~~~     |     PHYSICS
  | e- e- e-|     Voltage . Current . Resistance
  |    ⚡    |     From the spark to the signal
  +---------+
""",
    "electronics": r"""
  ──┤├──┤├──      ELECTRONICS
    [===]          Semiconductors . Logic . Fiber
     |||           Where physics meets silicon
""",
    "assembly": r"""
  MOV AX, 0x1337  ASSEMBLY
  PUSH AX          Registers . Memory . CPU
  INT 0x80         The language of the machine
""",
    "linux": r"""
  $ sudo su -      LINUX
  # whoami          Kernels . Shells . Flavors
  root              From boot to userspace
""",
    "languages": r"""
  fn main() {      LANGUAGES
    println!(..)    Python . Go . Rust . C . JS
  }                 Code as thought, made precise
""",
    "default": r"""
  > CODEX          KNOWLEDGE
  > LOADING...     Reference . Learning . Mastery
  > READY          Built for the curious mind
""",
}

DIFFICULTY_ART = {
    "beginner":     "[  BEGINNER  ]",
    "intermediate": "[ INTERMED.  ]",
    "advanced":     "[  ADVANCED  ]",
    "expert":       "[  EXPERT    ]",
}

SECTION_DIVIDERS = [
    "  · · · · · · · · · · · · · · · · · · · · ·",
    "  ─────────────────────────────────────────",
    "  ═════════════════════════════════════════",
    "  ╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌",
]

SPARK_ART = r"""
         *
        /|\
       / | \         "From the physics of spark
      /  |  \         to the fiber that carries light —
    //   |   \\       this is the foundation."
   //    |    \\
  //_____|_____\\
"""

COMPLETION_ART = r"""
  +-----------+
  |  * * * *  |   Lesson Complete
  |  * * * *  |
  |  * * * *  |   Knowledge acquired.
  +-----------+   Keep going.
"""


def get_banner(wide: bool = True) -> str:
    return CODEX_BANNER_WIDE if wide else CODEX_BANNER_COMPACT


def get_topic_art(topic_id: str) -> str:
    return TOPIC_ART.get(topic_id, TOPIC_ART["default"])


def get_difficulty_badge(level: str) -> str:
    return DIFFICULTY_ART.get(level, f"[  {level.upper()[:8]}  ]")


def section_divider(style: int = 0) -> str:
    return SECTION_DIVIDERS[style % len(SECTION_DIVIDERS)]
