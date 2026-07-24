"""Custom-button actions: the extensible catalog and the Run Custom Script action.

An action is a small dict persisted inside a custom button's entry (see
`custom_buttons`). Each action *type* is a catalog entry pairing an id and display
label with the modal that configures it and the coroutine that runs it, so future
action types slot in without touching the remote surface. This phase ships one type,
`run_script`.

**Trust boundary.** Run Custom Script executes arbitrary shell the user authored, on
the user's own machine, under the user's own privileges — no sandbox, no vetting.
`REMOTE_IP` is the only value the app injects into the environment. The timeout is a
reliability guard against a hung script, not a security control.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Awaitable, Callable

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Label,
    OptionList,
    RadioButton,
    RadioSet,
    Static,
    TextArea,
)
from textual.widgets.option_list import Option

# A fixed guard against a hung script, not user-configurable in this phase and not a
# security boundary. Overridable only as a test seam.
DEFAULT_TIMEOUT = 30.0

_HELPLINE = "REMOTE_IP is set in the environment to the connected device's IP address."


@dataclass(frozen=True)
class ScriptResult:
    """The outcome of one Run Custom Script run, whatever happened.

    `ok` is true only for a clean zero exit. `exit_code` is None when the script was
    killed on timeout or never started. `message` is a short human summary suitable
    for a toast title or a result-modal heading.
    """

    ok: bool
    exit_code: int | None
    stdout: str
    stderr: str
    message: str


async def run_script(
    action: dict, remote_ip: str, *, timeout: float = DEFAULT_TIMEOUT
) -> ScriptResult:
    """Run `action`'s shell script with `REMOTE_IP` set, bounded by `timeout`.

    Always returns a `ScriptResult`, never raises: a script that cannot start, one
    that exits non-zero, and one killed on timeout all come back as a result the
    caller surfaces per the button's Results choice.
    """
    env = {**os.environ, "REMOTE_IP": remote_ip}
    try:
        process = await _spawn(action, env)
    except OSError as error:
        return ScriptResult(False, None, "", "", f"Could not start script: {error}")
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()  # reap the killed child so nothing dangles
        return ScriptResult(False, None, "", "", f"Timed out after {timeout:g} seconds")
    out = stdout.decode(errors="replace")
    err = stderr.decode(errors="replace")
    code = process.returncode
    ok = code == 0
    return ScriptResult(
        ok, code, out, err, "Succeeded" if ok else f"Exited with code {code}"
    )


async def _spawn(action: dict, env: dict) -> asyncio.subprocess.Process:
    """Start the configured script through the shell: a file by path, inline by `-c`.

    A file is run as `/bin/sh <path>` rather than exec-ed directly, so it needs no
    execute bit or shebang — the field asks for a shell script, and inline text runs
    the same way. A `~` prefix is expanded, and a path that is not an existing file
    raises so the caller reports a clean start failure instead of a shell exit 127.
    """
    script = action.get("script", "")
    pipe = asyncio.subprocess.PIPE
    if action.get("source") == "file":
        path = os.path.expanduser(script)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"No such script file: {script}")
        return await asyncio.create_subprocess_exec(
            "/bin/sh", path, stdout=pipe, stderr=pipe, env=env
        )
    return await asyncio.create_subprocess_exec(
        "/bin/sh", "-c", script, stdout=pipe, stderr=pipe, env=env
    )


class RunScriptConfigModal(ModalScreen[dict | None]):
    """Configures a Run Custom Script action; OK returns it, Cancel returns None.

    A source toggle swaps a one-line path input (Script File) for a multi-line editor
    (Inline Script); a Results toggle chooses whether a run surfaces its output. The
    modal only builds and returns the action dict — persisting it is the Button Config
    modal's job, so cancelling anywhere up the chain leaves the button untouched.
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    RunScriptConfigModal { align: center middle; background: $background 60%; }
    #run-script {
        width: 70%; height: 90%; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #run-script-title {
        width: 100%; text-align: center; text-style: bold; margin-bottom: 1;
    }
    /* The scrolling body fills the space between the title and the docked buttons,
       so OK/Cancel stay reachable on a short terminal while the fields scroll. A
       bounded (1fr) height is what makes the pane scroll rather than overflow. */
    #run-script-body { width: 100%; height: 1fr; }
    #run-script-source, #run-script-results { width: 100%; margin-bottom: 1; }
    #run-script-path { width: 100%; margin-bottom: 1; }
    #run-script-inline { width: 100%; height: 8; margin-bottom: 1; }
    #run-script-helpline { width: 100%; color: $text-muted; margin-bottom: 1; }
    #run-script-buttons {
        width: 100%; height: auto; align-horizontal: center; margin-top: 1;
    }
    #run-script-buttons Button { width: 16; margin: 0 1; }
    """

    def __init__(self, action: dict | None = None) -> None:
        super().__init__()
        self._action = action or {}

    def compose(self) -> ComposeResult:
        is_inline = self._action.get("source") == "inline"
        show_results = bool(self._action.get("show_results"))
        script = self._action.get("script", "")
        with Vertical(id="run-script"):
            yield Label("Configure Run Custom Script", id="run-script-title")
            with VerticalScroll(id="run-script-body"):
                with RadioSet(id="run-script-source"):
                    yield RadioButton(
                        "Script File", value=not is_inline, id="source-file"
                    )
                    yield RadioButton(
                        "Inline Script", value=is_inline, id="source-inline"
                    )
                yield Input(
                    value="" if is_inline else script,
                    placeholder="Path to a shell script",
                    id="run-script-path",
                )
                yield TextArea(script if is_inline else "", id="run-script-inline")
                yield Label(_HELPLINE, id="run-script-helpline")
                with RadioSet(id="run-script-results"):
                    yield RadioButton(
                        "Don't Show", value=not show_results, id="results-hide"
                    )
                    yield RadioButton("Show", value=show_results, id="results-show")
            with Horizontal(id="run-script-buttons"):
                yield Button("OK", id="run-script-ok", variant="primary")
                yield Button("Cancel", id="run-script-cancel")

    def on_mount(self) -> None:
        self._apply_source()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id == "run-script-source":
            self._apply_source()

    def _apply_source(self) -> None:
        """Show only the input matching the selected source, hide the other."""
        is_file = self.query_one("#run-script-source", RadioSet).pressed_index == 0
        self.query_one("#run-script-path", Input).display = is_file
        self.query_one("#run-script-inline", TextArea).display = not is_file

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-script-ok":
            self.dismiss(self._collect())
        elif event.button.id == "run-script-cancel":
            self.dismiss(None)

    def _collect(self) -> dict:
        """Build the action dict from the current selections."""
        is_file = self.query_one("#run-script-source", RadioSet).pressed_index == 0
        show = self.query_one("#run-script-results", RadioSet).pressed_index == 1
        if is_file:
            script = self.query_one("#run-script-path", Input).value
        else:
            script = self.query_one("#run-script-inline", TextArea).text
        return {
            "type": "run_script",
            "source": "file" if is_file else "inline",
            "script": script,
            "show_results": show,
        }

    def action_cancel(self) -> None:
        self.dismiss(None)


class ScriptResultModal(ModalScreen[None]):
    """Shows one run's outcome: its summary, exit code, and full output.

    The output sits in a scrolling pane so long stdout/stderr is presented in full
    rather than truncated. Escape or Close dismisses it.
    """

    BINDINGS = [Binding("escape", "close", "Close")]

    DEFAULT_CSS = """
    ScriptResultModal { align: center middle; background: $background 60%; }
    #script-result {
        width: 70%; height: 80%; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #script-result-title {
        width: 100%; text-align: center; text-style: bold; margin-bottom: 1;
    }
    #script-result-exit { width: 100%; margin-bottom: 1; }
    #script-result-output {
        width: 100%; height: 1fr; border: round $primary; padding: 0 1;
    }
    #script-result-buttons {
        width: 100%; height: auto; align-horizontal: center; margin-top: 1;
    }
    #script-result-close { width: 16; }
    """

    def __init__(self, result: ScriptResult) -> None:
        super().__init__()
        self._result = result

    def compose(self) -> ComposeResult:
        code = "—" if self._result.exit_code is None else self._result.exit_code
        with Vertical(id="script-result"):
            yield Label(self._result.message, id="script-result-title")
            yield Label(f"Exit code: {code}", id="script-result-exit")
            with VerticalScroll(id="script-result-output"):
                yield Static(self._output_text(), id="script-result-body")
            with Horizontal(id="script-result-buttons"):
                yield Button("Close", id="script-result-close", variant="primary")

    def _output_text(self) -> str:
        """Combined stdout and stderr, or a placeholder when both are empty."""
        parts = [part for part in (self._result.stdout, self._result.stderr) if part]
        return "\n".join(parts) if parts else "(no output)"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)


def present_result(app: App, result: ScriptResult, *, show_results: bool) -> None:
    """Surface a run's outcome per its Results choice.

    Show → a result modal for success and failure alike. Don't Show → nothing on
    success, an error toast naming the failure otherwise.
    """
    if show_results:
        app.push_screen(ScriptResultModal(result))
    elif not result.ok:
        app.notify(result.message, title="Script failed", severity="error")


@dataclass(frozen=True)
class ActionType:
    """One entry in the action catalog: how to configure and how to run a type."""

    id: str
    label: str
    config_modal: type[ModalScreen]
    runner: Callable[[dict, str], Awaitable[ScriptResult]]


# The extensible catalog. Adding a future action type means adding an entry here
# plus its config modal and runner — the remote surface and Button Config modal are
# untouched. This phase ships exactly one.
ACTION_CATALOG: list[ActionType] = [
    ActionType("run_script", "Run Custom Script", RunScriptConfigModal, run_script),
]

_CATALOG_BY_ID = {entry.id: entry for entry in ACTION_CATALOG}


def action_type(type_id: str | None) -> ActionType | None:
    """The catalog entry for `type_id`, or None when no such type is registered."""
    return _CATALOG_BY_ID.get(type_id or "")


async def run_action(action: dict, remote_ip: str) -> ScriptResult:
    """Run `action` via its catalog runner; an unknown type is a graceful failure."""
    entry = action_type(action.get("type"))
    if entry is None:
        return ScriptResult(
            False, None, "", "", f"Unknown action type: {action.get('type')}"
        )
    return await entry.runner(action, remote_ip)


class ActionTypeListModal(ModalScreen[dict | None]):
    """Lists the action catalog; choosing a type opens its config and forwards it.

    Dismisses with the configured action dict, or None if the user cancels anywhere
    down the chain — so the Button Config modal only ever receives a finished action.
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    ActionTypeListModal { align: center middle; background: $background 60%; }
    #action-type-list {
        width: 60%; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #action-type-title {
        width: 100%; text-align: center; text-style: bold; margin-bottom: 1;
    }
    #action-type-options { width: 100%; height: auto; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="action-type-list"):
            yield Label("Choose an Action Type", id="action-type-title")
            yield OptionList(
                *(Option(entry.label, id=entry.id) for entry in ACTION_CATALOG),
                id="action-type-options",
            )

    def on_mount(self) -> None:
        self.query_one(OptionList).focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        entry = action_type(event.option.id)
        if entry is not None:
            self.app.push_screen(entry.config_modal(), self._configured)

    def _configured(self, action: dict | None) -> None:
        self.dismiss(action)

    def action_cancel(self) -> None:
        self.dismiss(None)
