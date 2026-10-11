# Live CLI comparison

These images were refreshed on 2026-10-11. The before and after runs used the same prompt, provider, model settings and terminal size.

Before is untouched upstream `f4db9bf079159df5ad8eedd704101ff256a99216`.
After is PR runtime revision `6d88005a33489ae916488ff9848289f538561c07`.
The manifest records both revisions and the actual source hashes.

| Waiting for the result | |
| --- | --- |
| Before | After |
| ![Upstream waiting reply](before-waiting.png) | ![Persistent pending report](after-waiting.png) |

| User input needed | |
| --- | --- |
| Before | After |
| ![Upstream approval reply](before-action-needed.png) | ![Persistent approval handoff](after-action-needed.png) |

These are PNG renderings of terminal cells captured from live PTYs. They are not native macOS Terminal screenshots. Computer Use rejected access to Terminal, so native screenshots remain unavailable.

The CLI made real OpenAISubscription requests using `sol-6.1`, high effort and hidden thinking. Each run used a fresh session, a 100-column by 34-row terminal, and only AgentSelf, Bash and BackgroundTask. Both runs exited with status 0.

The fixture first returns `INITIAL_RECEIPT_OK`. A second Bash command runs in the background until the capture driver releases a local file. It then returns `FINAL_RECEIPT_OK`. The driver captured both screens while the CLI process was alive. The after run emitted two checkpoint changes, with a real background task still running at the first change. Opening `/pending` added no model events.

[Full after view](after-pending-details.png) · [Exact prompt](prompt.txt) · [Capture manifest and source hashes](capture.json)

The `.ansi.gz` files contain the exact terminal bytes, compressed with gzip. Their manifest hashes refer to the uncompressed bytes. The `.screen.txt` files show the terminal cells interpreted with pyte, with trailing blank padding omitted. Pillow rasterized those cells with Menlo at 18 px and Apple Symbols for gutter glyphs. Replaying each ANSI capture reproduced its saved text grid exactly. No model response, runtime event or waiting line was injected. A read-only observer recorded events after the normal CLI renderer.

The fresh focused test run passed all 357 tests covering checkpoints, AgentSelf, session persistence, slash commands, rendering and replay. A separate resume check displayed the saved-report warning, exercised 40/80/120-column widths, and opened `/pending` without a model call or a change to the saved session. Both fresh sessions and the resumed session exited successfully.

This is a directed UI check. The prompt asks the agent to use the available reporting mechanism. It does not prove that agents will always adopt checkpoints, or that the audit's 202 repeated waiting lines disappear. Independent model calls also produce different wording and timings.

To reproduce, run the base and patched CLI in separate fresh sessions with the provider, model, effort, tools and terminal size above. Use the linked prompt with a local receipt fixture, capture while the background command is pending, then release it and capture the input-needed state. On the patched CLI, inspect `/pending` before quitting. Keep the full terminal stream alongside each image.
