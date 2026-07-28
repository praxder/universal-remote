"""Custom-button actions: the extensible catalog, Run Custom Script, and Run Macro.

An action is a small dict persisted inside a custom button's entry (see
`custom_buttons`). Each action *type* is a catalog entry pairing an id and display
label with the modal that configures it and the coroutine that runs it, so a further
action type slots in without touching the remote surface. Every runner is handed the
same `ActionContext` and reads only the fields its own type needs.

**Trust boundary.** Run Custom Script executes arbitrary shell the user authored, on
the user's own machine, under the user's own privileges — no sandbox, no vetting.
`REMOTE_IP` is the only value the app injects into the environment. The timeout is a
reliability guard against a hung script, not a security control.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Awaitable, Callable

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

from ..errors import TextUnsupportedError, UnsupportedKeyError
from ..keys import Key

# `macros.models.step_description` reaches back into this module (deferred, inside the
# function) to name a captured action, so these imports must stay one-directional here.
from ..macros.models import Macro, step_description
from ..macros.registry import get as macro_by_id
from ..macros.registry import list_macros
from .macros_screen import MacroOptionList

if TYPE_CHECKING:
    from ..session import Session

# A fixed guard against a hung script, not user-configurable in this phase and not a
# security boundary. Overridable only as a test seam.
DEFAULT_TIMEOUT = 30.0

# The Run Macro type id. Named because two places outside its own catalog entry must
# recognise it: recording refuses to capture it, and playback refuses to run it.
RUN_MACRO = "run_macro"

_HELPLINE = (
    "REMOTE_IP is set in the script's environment to the connected device's IP address."
)


@dataclass(frozen=True)
class ActionContext:
    """Everything a running action may need, gathered in one place.

    A runner reads only the fields its own type needs — Run Custom Script uses
    `remote_ip` alone — so serving a new action type means adding a field here
    rather than widening every runner's signature again. `app` is the running
    application, through which an action reports a message to the user or (for a
    type that owns its own progress UI) pushes its own modal.
    """

    app: App
    remote_ip: str
    session: "Session"
    macros: dict
    custom_buttons: dict
    device_id: str
    platform: str


@dataclass(frozen=True)
class ActionResult:
    """The outcome of running any catalog action, whatever happened.

    `ok` is true only for a clean run. `exit_code` and the captured output belong to
    action types that produce them (Run Custom Script); a type that does not leaves
    `exit_code` None and the streams empty. `message` is a short human summary
    suitable for a toast title or a result-modal heading.
    """

    ok: bool
    exit_code: int | None
    stdout: str
    stderr: str
    message: str


async def run_script(
    action: dict, context: "ActionContext", *, timeout: float = DEFAULT_TIMEOUT
) -> ActionResult:
    """Run `action`'s shell script with `REMOTE_IP` set, bounded by `timeout`.

    Reads only `remote_ip` from the shared context. Always returns an `ActionResult`,
    never raises: a script that cannot start, one that exits non-zero, and one killed
    on timeout all come back as a result the caller surfaces per the button's Results
    choice.
    """
    env = {**os.environ, "REMOTE_IP": context.remote_ip}
    try:
        process = await _spawn(action, env)
    except OSError as error:
        return ActionResult(False, None, "", "", f"Could not start script: {error}")
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()  # reap the killed child so nothing dangles
        return ActionResult(False, None, "", "", f"Timed out after {timeout:g} seconds")
    out = stdout.decode(errors="replace")
    err = stderr.decode(errors="replace")
    code = process.returncode
    ok = code == 0
    return ActionResult(
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

    def __init__(self, result: ActionResult) -> None:
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


def present_result(app: App, result: ActionResult, *, show_results: bool) -> None:
    """Surface a run's outcome per its Results choice.

    Show → a result modal for success and failure alike. Don't Show → nothing on
    success, an error toast naming the failure otherwise.
    """
    if show_results:
        app.push_screen(ScriptResultModal(result))
    elif not result.ok:
        app.notify(result.message, title="Script failed", severity="error")


class MacroPlaybackModal(ModalScreen[ActionResult]):
    """Plays one macro behind a blocking modal, showing progress and offering Cancel.

    Being a modal is what freezes the remote: Textual truncates the binding chain at
    the topmost modal, so no shortcut can interleave a key of the user's own with the
    macro's own sends.

    The modal owns its reporting — a failed step names itself in an error notification
    here — which is why the `run_macro` catalog entry declares `reports_own_outcome`
    and the shared path stays quiet about its result.

    Each captured action step runs through `run_action` **directly** and never through
    the remote's own execute path, which would present a script step's result modal
    mid-run and sit there waiting on the user.
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    MacroPlaybackModal { align: center middle; background: $background 60%; }
    #macro-playback {
        width: 60%; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #macro-playback-title {
        width: 100%; text-align: center; text-style: bold; margin-bottom: 1;
    }
    #macro-playback-progress { width: 100%; text-align: center; margin-bottom: 1; }
    #macro-playback-buttons { width: 100%; height: auto; align-horizontal: center; }
    #macro-playback-buttons Button { width: 16; min-width: 0; }
    """

    def __init__(self, macro: Macro, context: ActionContext) -> None:
        super().__init__()
        self._macro = macro
        self._action_context = context
        # The step the run has reached (1-based, 0 before the first), so an abort or a
        # cancellation can name where it stopped.
        self._index = 0
        # Cancel and the step loop can both reach the end of the run, so dismissal is
        # funnelled through `_settle` and happens exactly once.
        self._finished = False
        self._worker = None

    def compose(self) -> ComposeResult:
        with Vertical(id="macro-playback"):
            yield Label(f"Playing '{self._macro.name}'", id="macro-playback-title")
            yield Label(self._progress_text(), id="macro-playback-progress")
            with Horizontal(id="macro-playback-buttons"):
                yield Button("Cancel", id="macro-playback-cancel")

    def on_mount(self) -> None:
        self._worker = self.run_worker(self._play())

    def _progress_text(self) -> str:
        return f"Step {max(self._index, 1)} of {len(self._macro.steps)}"

    async def _play(self) -> None:
        """Run every step in order, stopping at the first one that fails.

        The macro's own gap is waited *before* the index advances, so a cancel landing
        inside a gap names the step that ran rather than the one about to.
        """
        for index, step in enumerate(self._macro.steps, start=1):
            if index > 1:
                await asyncio.sleep(self._macro.step_pause_ms / 1000)
            self._index = index
            self.query_one("#macro-playback-progress", Label).update(
                self._progress_text()
            )
            failure = await self._run_step(step)
            if failure is not None:
                self._abort(step, failure)
                return
        total = len(self._macro.steps)
        self._settle(
            ActionResult(
                True,
                None,
                "",
                "",
                f"Macro '{self._macro.name}' completed: {total} steps",
            )
        )

    async def _run_step(self, step: dict) -> str | None:
        """Perform one step, returning None on success or why it failed."""
        kind = step.get("type")
        if kind == "key":
            return await self._send_key(step.get("key"))
        if kind == "text":
            return await self._send_text(step.get("text") or "")
        if kind == "pause":
            ms = step.get("ms")
            await asyncio.sleep(max(ms if isinstance(ms, int) else 0, 0) / 1000)
            return None
        if kind == "action":
            return await self._run_action_step(step.get("action") or {})
        return f"unknown step type: {kind}"

    async def _send_key(self, key_name: str | None) -> str | None:
        try:
            key = Key[key_name or ""]
        except KeyError:
            return f"{key_name} is not a known key"
        try:
            await self._action_context.session.send_key(key)
        except UnsupportedKeyError:
            return "this device does not support that key"
        except Exception:
            return "the device may be unreachable"
        return None

    async def _send_text(self, text: str) -> str | None:
        try:
            await self._action_context.session.send_text(text)
        except TextUnsupportedError:
            return "this device does not support text entry"
        except Exception:
            return "the device may be unreachable"
        return None

    async def _run_action_step(self, action: dict) -> str | None:
        """Run a captured action, refusing one that would invoke another macro.

        The depth guard: recording refuses to capture a Run Macro action, but a
        hand-edited preferences file can hold one, and running it would recurse. A
        refused step is a failed step, so the run aborts like any other failure.
        """
        if action.get("type") == RUN_MACRO:
            return "nested macros are not supported"
        result = await run_action(action, self._action_context)
        return None if result.ok else result.message

    def _abort(self, step: dict, reason: str) -> None:
        """Stop the run at the failing step, naming it and why in one error."""
        message = (
            f"Macro '{self._macro.name}' failed at step {self._index} "
            f"({step_description(step)}): {reason}"
        )
        self._action_context.app.notify(message, title="Macro failed", severity="error")
        self._settle(ActionResult(False, None, "", "", message))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self._cancel()

    def action_cancel(self) -> None:
        self._cancel()

    def _cancel(self) -> None:
        """Stop where the run has reached, raising no error notification.

        The user chose to stop it, and reporting their own choice back at them as an
        error is noise — but the run did not complete, so its result is unsuccessful
        and names the step it stopped at. Steps already performed stay performed.
        """
        if self._finished:
            return
        if self._worker is not None:
            self._worker.cancel()  # stops mid-step, including inside a pause
        where = ""
        if 0 < self._index <= len(self._macro.steps):
            step = self._macro.steps[self._index - 1]
            where = f" at step {self._index} ({step_description(step)})"
        self._settle(
            ActionResult(
                False, None, "", "", f"Macro '{self._macro.name}' cancelled{where}"
            )
        )

    def _settle(self, result: ActionResult) -> None:
        """Dismiss with `result`, ignoring any later attempt.

        Cancel and the step loop race by construction: the worker's cancellation only
        lands on the next tick, so the loop can reach its own ending first.
        """
        if self._finished:
            return
        self._finished = True
        self.dismiss(result)


class RunMacroConfigModal(ModalScreen[dict | None]):
    """Picks the macro a custom button plays; OK returns the action, Cancel None.

    Stores the macro's stable id and never a copy of it, so editing the macro
    afterwards changes what the button does. There is no Results choice: playback
    presents its own progress modal and reports a failing step itself.
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    RunMacroConfigModal { align: center middle; background: $background 60%; }
    #run-macro {
        width: 70%; height: 80%; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #run-macro-title {
        width: 100%; text-align: center; text-style: bold; margin-bottom: 1;
    }
    #run-macro-options { width: 100%; height: 1fr; }
    #run-macro-buttons {
        width: 100%; height: auto; align-horizontal: center; margin-top: 1;
    }
    #run-macro-buttons Button { width: 16; min-width: 0; margin: 0 1; }
    """

    def __init__(self, action: dict | None = None) -> None:
        super().__init__()
        # The macro this button already plays, so re-editing preselects it.
        self._macro_id = (action or {}).get("macro_id")

    def compose(self) -> ComposeResult:
        with Vertical(id="run-macro"):
            yield Label("Choose a Macro", id="run-macro-title")
            yield MacroOptionList(*self._rows(), id="run-macro-options")
            with Horizontal(id="run-macro-buttons"):
                yield Button("OK", id="run-macro-ok", variant="primary")
                yield Button("Cancel", id="run-macro-cancel")

    def _rows(self) -> list[Option]:
        saved = self._saved()
        if not saved:
            return [Option("No macros to choose — record one first", disabled=True)]
        return [Option(macro.name, id=macro.id) for macro in saved]

    def _saved(self) -> list[Macro]:
        return list_macros(self.app.macros)

    def on_mount(self) -> None:
        options = self.query_one(MacroOptionList)
        options.focus()
        ids = [macro.id for macro in self._saved()]
        if self._macro_id in ids:
            options.highlighted = ids.index(self._macro_id)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(self._collect())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-macro-ok":
            self.dismiss(self._collect())
        else:
            self.dismiss(None)

    def _collect(self) -> dict | None:
        """The Run Macro action for the highlighted macro, or None when there is none."""
        ids = [macro.id for macro in self._saved()]
        highlighted = self.query_one(MacroOptionList).highlighted
        if highlighted is None or not ids:
            return None
        return {"type": RUN_MACRO, "macro_id": ids[highlighted]}

    def action_cancel(self) -> None:
        self.dismiss(None)


async def run_macro(action: dict, context: ActionContext) -> ActionResult:
    """Play the macro `action` refers to, behind its own progress modal.

    Resolves the id rather than holding a copy, so a macro edited since the button was
    configured plays as it is now. A button pointing at a deleted macro reports that
    and sends nothing.
    """
    macro = macro_by_id(context.macros, action.get("macro_id") or "")
    if macro is None:
        message = "That macro no longer exists"
        context.app.notify(message, title="Macro failed", severity="error")
        return ActionResult(False, None, "", "", message)
    return await context.app.push_screen_wait(MacroPlaybackModal(macro, context))


@dataclass(frozen=True)
class ActionType:
    """One entry in the action catalog: how to configure and how to run a type.

    `reports_own_outcome` marks a type that tells the user how it went itself, so the
    shared path must not surface its result a second time — macro playback already
    names a failing step in its own error notification, and a cancelled run is not an
    error at all.
    """

    id: str
    label: str
    config_modal: type[ModalScreen]
    runner: Callable[[dict, ActionContext], Awaitable[ActionResult]]
    reports_own_outcome: bool = False


# The extensible catalog. Adding a further action type means adding an entry here plus
# its config modal and runner — the remote surface and Button Config modal are
# untouched.
ACTION_CATALOG: list[ActionType] = [
    ActionType("run_script", "Run Custom Script", RunScriptConfigModal, run_script),
    ActionType(
        RUN_MACRO,
        "Run Macro",
        RunMacroConfigModal,
        run_macro,
        reports_own_outcome=True,
    ),
]

_CATALOG_BY_ID = {entry.id: entry for entry in ACTION_CATALOG}


def action_type(type_id: str | None) -> ActionType | None:
    """The catalog entry for `type_id`, or None when no such type is registered."""
    return _CATALOG_BY_ID.get(type_id or "")


async def run_action(action: dict, context: ActionContext) -> ActionResult:
    """Run `action` via its catalog runner; an unknown type is a graceful failure."""
    entry = action_type(action.get("type"))
    if entry is None:
        return ActionResult(
            False, None, "", "", f"Unknown action type: {action.get('type')}"
        )
    return await entry.runner(action, context)


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

    def __init__(self, current: dict | None = None) -> None:
        super().__init__()
        # The button's currently-assigned action, forwarded to a chosen type's config
        # modal so re-editing prefills its fields. Only forwarded when its type matches
        # the chosen one, so it stays correct as the catalog grows.
        self._current = current

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
            existing = (
                self._current
                if self._current and self._current.get("type") == entry.id
                else None
            )
            self.app.push_screen(entry.config_modal(existing), self._configured)

    def _configured(self, action: dict | None) -> None:
        self.dismiss(action)

    def action_cancel(self) -> None:
        self.dismiss(None)
