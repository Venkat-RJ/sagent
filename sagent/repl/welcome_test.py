"""Startup layout, literal metadata, and terminal fallbacks."""

from __future__ import annotations

from pathlib import Path

import io

from rich.cells import cell_len
from rich.console import Console

import pytest

from sagent.repl import welcome
from sagent.repl.welcome import render_welcome


@pytest.fixture(autouse=True)
def _terminal_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TERM", "xterm-256color")


def _render(
    *,
    width: int = 80,
    height: int = 24,
    terminal: bool = True,
    resumed: bool = False,
    folder: Path = Path("/research"),
) -> str:
    stream = io.StringIO()
    console = Console(
        file=stream,
        force_terminal=terminal,
        no_color=True,
        width=width,
        height=height,
    )
    render_welcome(
        console,
        model="test-model",
        provider="TestProvider",
        folder=folder,
        resumed=resumed,
    )
    # Rich still emits bold/dim when no_color is set; export recorded text in
    # the dedicated NO_COLOR test below instead of assuming ANSI-free output.
    return stream.getvalue()


def test_fresh_terminal_has_banner_actual_metadata_and_invitation() -> None:
    out = _render()
    assert "███████" in out
    assert "Turn questions into experiments." in out
    assert "test-model" in out
    assert "TestProvider" in out
    assert "/research" in out
    assert "Hello, scientist! What are we doing today?" in out
    assert "/help" in out
    assert "/quit" in out
    assert "/tasks" in out


@pytest.mark.parametrize(("width", "height"), [(40, 24), (80, 18)])
def test_small_terminal_has_compact_heading(width: int, height: int) -> None:
    out = _render(width=width, height=height)
    assert "SAGENT" in out
    assert "█" not in out
    assert "test-model" in out


def test_resume_keeps_transcript_prominent() -> None:
    out = _render(resumed=True)
    assert "SAGENT" in out
    assert "Resuming your session." in out
    assert "█" not in out
    assert "Hello, scientist! What are we doing today?" not in out


def test_redirected_output_retains_only_plain_model_line() -> None:
    assert _render(terminal=False) == "[TestProvider] test-model\n"


def test_no_color_keeps_readable_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    stream = io.StringIO()
    console = Console(file=stream, force_terminal=True, record=True)
    render_welcome(
        console,
        model="test-model",
        provider="TestProvider",
        folder=Path("/research"),
    )
    assert console.no_color
    assert "\x1b[38;" not in stream.getvalue()
    plain = console.export_text(styles=False)
    assert "test-model" in plain
    assert "\x1b" not in plain


def test_dumb_terminal_uses_text_heading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TERM", "dumb")
    out = _render()
    assert "SAGENT" in out
    assert "█" not in out


def test_ascii_terminal_does_not_receive_unicode_blocks() -> None:
    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="ascii")
    render_welcome(
        Console(file=stream, force_terminal=True, width=80),
        model="test-model",
        provider="TestProvider",
        folder=Path("/research"),
    )
    stream.flush()
    out = raw.getvalue().decode("ascii")
    assert "SAGENT" in out
    assert "█" not in out
    _ = out.encode("ascii")


def test_home_abbreviation_respects_path_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: Path("/people/alex"))
    assert "~/research" in _render(folder=Path("/people/alex/research"))
    assert "/people/alexander/research" in _render(
        folder=Path("/people/alexander/research"),
    )


def test_literal_metadata_and_long_paths_fit_terminal() -> None:
    stream = io.StringIO()
    console = Console(
        file=stream,
        force_terminal=True,
        record=True,
        width=40,
    )
    folder = Path("/research/[bold]/a-very-long-project-directory/experiments")
    render_welcome(
        console,
        model="[red]literal-model[/red]",
        provider="TestProvider",
        folder=folder,
    )
    plain = console.export_text(styles=False)
    assert "[red]literal-model[/red]" in plain
    assert "…/" in plain
    assert "experiments" in plain
    assert all(len(line) <= 40 for line in plain.splitlines())


def test_long_directory_name_and_wide_characters_fit_metadata() -> None:
    stream = io.StringIO()
    console = Console(file=stream, force_terminal=True, record=True, width=40)
    render_welcome(
        console,
        model="test-model",
        provider="TestProvider",
        folder=Path("/research/" + "研究" * 20 + "-project"),
    )
    plain = console.export_text(styles=False)
    assert "…" in plain
    assert "-project" in plain
    assert all(cell_len(line) <= 40 for line in plain.splitlines())


def test_literal_metadata_is_not_parsed_as_markup() -> None:
    out = _render(folder=Path("/research/[bold]"))
    assert "[bold]" in out


def test_sweep_finishes_before_metadata_and_restores_cursor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delays: list[float] = []
    monkeypatch.setattr("sagent.repl.welcome.time.sleep", delays.append)
    stream = io.StringIO()
    render_welcome(
        Console(
            file=stream,
            force_terminal=True,
            color_system="truecolor",
            no_color=False,
            width=80,
            height=24,
        ),
        model="test-model",
        provider="TestProvider",
        folder=Path("/research"),
        animate=True,
    )
    out = stream.getvalue()
    assert 0 < sum(delays) < 0.5
    assert "\x1b[?25l" in out
    assert out.index("\x1b[?25h") < out.index("test-model")
    assert out.count("test-model") == 1
    assert "Hello, scientist! What are we doing today?" in out


@pytest.mark.parametrize(
    ("width", "height", "terminal", "no_color", "resumed"),
    [
        (40, 24, True, False, False),
        (80, 18, True, False, False),
        (80, 24, False, False, False),
        (80, 24, True, True, False),
        (80, 24, True, False, True),
    ],
)
def test_fallbacks_do_not_animate(
    monkeypatch: pytest.MonkeyPatch,
    *,
    width: int,
    height: int,
    terminal: bool,
    no_color: bool,
    resumed: bool,
) -> None:
    delays: list[float] = []
    monkeypatch.setattr("sagent.repl.welcome.time.sleep", delays.append)
    render_welcome(
        Console(
            file=io.StringIO(),
            force_terminal=terminal,
            no_color=no_color,
            width=width,
            height=height,
        ),
        model="test-model",
        provider="TestProvider",
        folder=Path("/research"),
        animate=True,
        resumed=resumed,
    )
    assert not delays


def test_environment_can_disable_startup_animation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SAGENT_NO_ANIMATION", "1")
    calls: list[bool] = []

    def capture(*_args: object, **kwargs: object) -> None:
        calls.append(kwargs["animate"] is False)

    monkeypatch.setattr(welcome, "render_welcome", capture)
    welcome.print_welcome(
        model="test-model", provider="TestProvider", folder=Path("/research")
    )
    assert calls == [True]


def test_interrupted_sweep_restores_terminal_cursor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def interrupt(_seconds: float) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("sagent.repl.welcome.time.sleep", interrupt)
    stream = io.StringIO()
    with pytest.raises(KeyboardInterrupt):
        render_welcome(
            Console(
                file=stream,
                force_terminal=True,
                color_system="truecolor",
                no_color=False,
                width=80,
                height=24,
            ),
            model="test-model",
            provider="TestProvider",
            folder=Path("/research"),
            animate=True,
        )
    assert "\x1b[?25h" in stream.getvalue()
