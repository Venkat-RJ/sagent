# CLI welcome review evidence

Captured on 2026-10-10 in native macOS Terminal, using the same dark profile,
font, window geometry, working directory, provider, and model for both versions.
These are actual CLI screenshots, not mockups or rendered transcript images.
The capture region excludes the window title bar. No screenshot pixels were
retouched. Static screenshots show the final state, not the animation.

| Image | Source revision | What it shows |
| --- | --- | --- |
| [Before](before.png) | `e58865992aa22a7766b8d62a19ff3654dbd31bfd` | Untouched upstream startup and input prompt. |
| [After](after.png) | `aeaa1f281ab4867cb5933f44dbc054ed0dc4c1b3` | New welcome after the icon finishes its two laps. |
| [Live response](after-response.png) | `aeaa1f281ab4867cb5933f44dbc054ed0dc4c1b3` | A real model response followed by the next input prompt. |

## Reproduce the live check

Use an authenticated provider and a separate checkout for each revision.
Both checks used the same virtual environment and `PYTHONPATH` pointed to the
respective checkout. The working directory was `/tmp/sagent-welcome-demo`
(displayed as `/private/tmp/sagent-welcome-demo` on macOS).

```bash
python -m sagent.bin.cli \
  --provider OpenAISubscription --model sol-6.1 \
  --tools none --recipe bare --no-compact \
  --ephemeral --no-resume-persistent \
  --history /tmp/sagent-welcome-review-history
```

After startup, enter:

```text
Reply with exactly: Ready for research.
/help
/quit
```

Both revisions returned `Ready for research.`, displayed the command list, and
exited after `/quit`. Tools were disabled. No research experiments were run.
Startup itself makes no model request; the typed prompt does.

The native captures used the same screen region, `100,132,860,467`, producing
1720 by 934 pixel images on the Retina display. Capture command:

```bash
screencapture -x -R100,132,860,467 after.png
```

## Validation

- Focused welcome, CLI, and REPL tests: **253 passed, 1 deselected**.
- Five actual CLI PTY cases: animated 80 by 24, compact 40 by 24, short 80 by
  18, `NO_COLOR=1`, and `SAGENT_NO_ANIMATION=1`. All exited with status 0 after
  `/quit`, without making a model request.
- Whole-repository Ruff lint/format, ty, basedpyright, import, and build passed.
- Full branch suite: **7393 passed, 13 failed, 132 skipped, 121 deselected**.
- Untouched upstream suite: **7343 passed, 17 failed, 132 skipped,
  121 deselected**. All 13 branch failures also occurred upstream. They are in
  `sagent/lib/files/grep_test.py` and `sagent/lib/worker_count_test.py`, which this
  change does not modify. The full suite is not green on this host.
- Whole-repository codespell reports the existing `crate` finding at
  `pyproject.toml:73`. The changed files pass codespell.

The test environment was macOS arm64 with Python 3.14.6. Checks used
`DEVELOPER_DIR=/Library/Developer/CommandLineTools` on this host. This evidence
does not establish visual compatibility with every terminal or font. Automated
tests cover narrow layouts, resumed sessions, non-Unicode terminals, redirected
output, color opt-out, and cursor cleanup during interruption.
