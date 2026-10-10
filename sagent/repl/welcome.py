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
    "███████╗ █████╗  ██████╗ ███████╗███╗   ██╗████████╗",
    "██╔════╝██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝",
    "███████╗███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║",
    "╚════██║██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║",
    "███████║██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║",
    "╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝",
)
_BANNER_WIDTH = max(len(row) for row in _BANNER)
_OUTLINE = frozenset("╔╗╚╝═║")


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
        and console.width >= _BANNER_WIDTH + 4
        and console.height >= 22
    )
    console.print()
    if large:
        for row in _BANNER:
            lettering = Text("  ")
            for char in row:
                lettering.append(
                    char, style=f"dim {_BLUE}" if char in _OUTLINE else _BLUE
                )
            console.print(lettering)
        motif = Text("  ")
        for color in (_BLUE, _GREEN, _RED):
            motif.append("━━ ", style=color)
        motif.append(" rekursiv.ai", style="dim")
        console.print(motif)
        console.print()
    else:
        heading = Text("  SAGENT", style=f"bold {_BLUE}")
        heading.append("  rekursiv.ai", style="dim")
        console.print(heading)
    console.print(
        Text(
            "  Resuming your session."
            if resumed
            else "  Turn questions into experiments.",
        ),
    )
    console.print()
    home = Path.home()  # noqa: TID251 -- Display abbreviation only, not a per-user storage location.
    # Keep metadata within the wordmark's measure on spacious terminals.
    # Never crop a model ID; long IDs/providers fold normally. Folder paths
    # explicitly mark omitted ancestors, preserving the project suffix.
    value_width = max(1, min(console.width - 12, _BANNER_WIDTH - 10))
    display_folder = _folder_label(
        folder, home=home, width=value_width, unicode_ok=unicode_ok
    )
    display_provider = {
        "OpenAISubscription": "OpenAI Subscription",
        "AnthropicCLI": "Anthropic CLI",
        "LlamaCpp": "Llama.cpp",
    }.get(provider, provider)
    metadata = [("model", model), ("provider", display_provider)]
    separator = " · " if unicode_ok else " / "
    combined = model + separator + display_provider
    if Text(combined).cell_len <= value_width:
        metadata = [("model", combined)]
    metadata.append(("folder", display_folder))
    for label, value in metadata:
        row = Text(f"  {label:<10}", style="dim")
        row.append(value, style="not dim")
        console.print(row, overflow="fold")
    console.print()
    console.print(Text("  /help commands   /tasks agents   /quit exit", style="dim"))
    console.print()
    if not resumed:
        console.print(Text("  What would you like to investigate?"))
    console.print()


def _supports_blocks(encoding: str) -> bool:
    try:
        _ = "█╔╗╚╝═║━…".encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return False
    return True


def _folder_label(folder: Path, *, home: Path, width: int, unicode_ok: bool) -> str:
    """Abbreviate long ancestor paths while retaining the visible project name."""
    display = (
        str(Path("~") / folder.relative_to(home))
        if folder.is_relative_to(home)
        else str(folder)
    )
    if Text(display).cell_len <= width:
        return display
    marker = "…" if unicode_ok else "..."
    prefix = "~/" if folder.is_relative_to(home) else ""
    parts = folder.parts
    for start in range(1, len(parts)):
        candidate = prefix + marker + "/" + "/".join(parts[start:])
        if Text(candidate).cell_len <= width:
            return candidate
    # A single directory name can itself be wider than the terminal. Mark
    # truncation on its left rather than overflowing the metadata column.
    suffix = Text(folder.name)
    while suffix.cell_len > max(0, width - len(marker)):
        suffix = suffix[1:]
    return marker[:width] + suffix.plain
