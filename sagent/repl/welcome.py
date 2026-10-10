"""Local startup identity and orientation for the interactive CLI."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from rich.console import Console
    from rich.text import Text
else:
    from wrapt import lazy_import

    Console = lazy_import("rich.console", "Console")
    Text = lazy_import("rich.text", "Text")


# Text cells only: no image protocol, extra font, or background color required.
# The blue is slightly darker than the logo reference to work on light terminals.
_BLUE = "#4a90c4"
_GREEN = "#93c47d"
_RED = "#e06666"
_BANNER = (
    "██████████    ██████      ████████  ██████████  ██      ██  ██████████",
    "██          ████  ████  ████        ██          ████    ██      ██    ",
    "██████████  ██      ██  ██          ████████    ██  ██  ██      ██    ",
    "        ██  ██████████  ██  ██████  ██          ██    ████      ██    ",
    "        ██  ██      ██  ██      ██  ██          ██      ██      ██    ",
    "██████████  ██      ██    ████████  ██████████  ██      ██      ██    ",
)


def print_welcome(
    *,
    model: str,
    provider: str,
    folder: Path,
    resumed: bool = False,
) -> None:
    """Print startup before prompt-toolkit owns the terminal."""
    render_welcome(
        Console(stderr=True),
        model=model,
        provider=provider,
        folder=folder,
        resumed=resumed,
    )


def render_welcome(
    console: Console,
    *,
    model: str,
    provider: str,
    folder: Path,
    resumed: bool = False,
) -> None:
    """Render a width-aware welcome without performing any model request.

    Redirected stderr retains the old plain model line. Small, dumb, and
    non-Unicode terminals use a compact text heading. Resumes keep their
    transcript prominent instead of repeating the large fresh-session banner.
    Rich honors NO_COLOR; body text inherits the terminal foreground.
    """
    if not console.is_terminal:
        console.print(Text(f"[{provider}] {model}"))
        return
    unicode_ok = _supports_blocks(console.encoding)
    large = (
        not resumed
        and not console.is_dumb_terminal
        and unicode_ok
        and console.width >= 72
        and console.height >= 22
    )
    console.print()
    if large:
        for row in _BANNER:
            console.print(Text("  " + row.rstrip(), style=_BLUE))
        motif = Text("  ")
        for color in (_BLUE, _GREEN, _RED):
            motif.append("██████  ", style=color)
        motif.append("↵", style="dim")
        console.print(motif)
        console.print()
    else:
        console.print(Text("  SAGENT", style=f"bold {_BLUE}"))
    console.print(
        Text(
            "  Resuming your session."
            if resumed
            else "  Turn questions into experiments.",
        ),
    )
    console.print()
    home = Path.home()  # noqa: TID251 -- Display abbreviation only, not a per-user storage location.
    display_folder = str(folder)
    if folder.is_relative_to(home):
        display_folder = str(Path("~") / folder.relative_to(home))
    for label, value in (
        ("model", model),
        ("provider", provider),
        ("folder", display_folder),
    ):
        row = Text(f"  {label:<10}", style="dim")
        row.append(value, style="not dim")
        console.print(row, overflow="fold")
    console.print()
    if not resumed:
        console.print(Text("  What would you like to investigate?"))
    console.print(Text("  /help for commands. /quit to exit.", style="dim"))
    console.print()


def _supports_blocks(encoding: str) -> bool:
    try:
        _ = "█↵".encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return False
    return True
