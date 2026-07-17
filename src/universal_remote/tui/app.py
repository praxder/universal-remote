"""The root Textual application, holding the device store and adapter registry."""

from __future__ import annotations

from textual.app import App, SystemCommand
from textual.screen import Screen
from textual.worker import WorkerFailed

from typing import Callable, Iterable

from ..devices.store import DeviceStore
from ..error_log import log_exception
from ..errors import UniversalRemoteError
from ..registry import AdapterRegistry
from ..registry import registry as default_registry
from .menu import MenuScreen
from .quotes import Quote, random_quote


class UniversalRemoteApp(App[None]):
    """Launches into the entry menu; screens read `store` and `registry` off the app."""

    TITLE = "Universal Remote"

    CSS = """
    Screen { align: center middle; }
    #menu { width: 100%; height: auto; }
    #menu Button { width: 28; margin: 1 0; }
    /* focus: accent text on a slightly lighter fill instead of reversing fg/bg;
       keep the default `tall` top/bottom border so the height never changes */
    Button:focus {
        text-style: bold;
        color: $accent;
        background: $surface-lighten-1;
        border-top: tall $surface-lighten-1;
        border-bottom: tall $surface-lighten-1;
    }
    /* #title width matches the TITLE_ART banner so it never wraps */
    #title { width: 42; text-align: center; margin-bottom: 1; color: $accent; }
    /* left-aligned so the multi-width banner lines keep their column alignment */
    #devices-title { width: 36; text-align: left; margin: 1 0 1 0; color: $accent; }
    /* wider than #devices-title so the "Add/Edit Device" banner never wraps */
    #add-title { width: 52; text-align: left; margin: 1 0 2 0; color: $accent; }
    /* wide enough for the "Select Device" banner; padded above and below */
    #use-remote-title { width: 58; text-align: left; margin: 1 0 1 0; color: $accent; }
    /* wide enough for the "Discover" banner; padded like the Devices banner */
    #discover-title { width: 40; text-align: left; margin: 1 0 1 0; color: $accent; }
    /* the "searching" indicator: an animated spinner + bold text, hidden once done */
    #discover-status { height: 1; margin-top: 1; }
    #discover-status LoadingIndicator { width: 8; height: 1; color: $accent; }
    #discover-status-text {
        width: auto; height: 1; margin-left: 2;
        text-style: bold; color: $accent;
    }
    /* slight left indent on Save to offset it from the fields above */
    #add-device #save { margin: 1 0 0 1; }
    /* text-input mode toggle: a labelled switch on one row, shown only for Android TV.
       Match the Inputs' filled box: $surface fill at height 3, and left/right `tall` borders
       so the fill insets by 1 col on each side exactly like an Input. Only left/right (not
       top/bottom): a full `tall` border would leave a 1-row content area and clip the
       3-row-tall Switch, so the top/bottom stay open to fit it. */
    #text-adb-cell {
        height: 3; width: 100%; background: $surface;
        border-left: tall $border-blurred; border-right: tall $border-blurred;
    }
    #text-adb-label { width: 1fr; content-align: left middle; height: 100%; padding-left: 2; }
    #text-adb-switch { margin-right: 1; }
    /* duplicate-save error: hidden until there is a message, then shown in red */
    #add-device #error { display: none; color: $error; margin: 1 0 0 0; }
    #quote { width: 42; text-align: center; margin-top: 1; color: $text-muted; }
    /* delete confirmation: dim the device list behind a centered dialog box */
    ConfirmDeleteScreen { align: center middle; background: $background 60%; }
    #confirm-delete {
        width: auto; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #confirm-message { text-align: center; margin-bottom: 1; }
    #confirm-delete Button { width: 16; margin-top: 1; }
    /* connecting: dim the device list behind a centered dialog box */
    ConnectingModal { align: center middle; background: $background 60%; }
    #connecting {
        width: auto; height: auto; padding: 1 2;
        border: thick $primary; background: $surface; align: center middle;
    }
    #connecting-loading, #connecting-error { width: auto; height: auto; align: center middle; }
    #connecting LoadingIndicator { height: 1; margin-bottom: 1; }
    #connect-error { text-align: center; margin-bottom: 1; }
    #connecting Button { width: 16; margin-top: 1; }
    #cancel-row { width: 100%; }  /* full width so its centered button centers in the box */
    #error-buttons { width: 100%; }  /* full width so the retry/back column centers in the box */
    /* pairing: dim the device selection behind a centered dialog box */
    PairingScreen { align: center middle; background: $background 60%; }
    #pairing {
        width: auto; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    /* guidance sets the box width; title/buttons fill it and center their content */
    #pairing-guidance { text-align: center; }
    #pairing-title { width: 100%; text-align: center; }
    /* PIN entry: hidden until an adapter (e.g. Apple TV) asks for a PIN */
    #pin-entry { display: none; width: 100%; height: auto; }
    #pin-entry Input { width: 100%; margin-top: 1; }
    #pairing #submit, #pairing #cancel { width: 100%; margin-top: 1; }
    /* ADB text setup: dim the device list behind a centered dialog box */
    AdbTextSetupScreen { align: center middle; background: $background 60%; }
    #adb-setup {
        width: 62; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #adb-setup-title { width: 100%; text-align: center; text-style: bold; }
    #adb-setup-guidance { width: 100%; margin: 1 0; }
    #adb-setup Input { width: 100%; margin-bottom: 1; }
    #adb-setup-status { width: 100%; color: $warning; }
    #adb-setup #adb-setup-submit, #adb-setup #cancel { width: 100%; margin-top: 1; }
    /* post-add ADB text hint: a centered dialog over the device list */
    AdbTextHintScreen { align: center middle; background: $background 60%; }
    #adb-hint {
        width: 54; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #adb-hint-title { width: 100%; text-align: center; text-style: bold; }
    #adb-hint-body { width: 100%; margin: 1 0; }
    #adb-hint #adb-hint-ok { width: 100%; }
    """

    def __init__(
        self,
        store: DeviceStore | None = None,
        registry: AdapterRegistry | None = None,
        quote_provider: Callable[[], Quote | None] | None = None,
    ) -> None:
        super().__init__()
        self.store = store or DeviceStore()
        self.registry = registry or default_registry
        self.quote_provider = quote_provider or random_quote

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        """Drop the Maximize and Screenshot commands from the command palette."""
        for command in super().get_system_commands(screen):
            if command.title in ("Maximize", "Screenshot"):
                continue
            yield command

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())

    def _handle_exception(self, error: Exception) -> None:
        """App-wide safety net: an unexpected error toasts and stays, not crashes.

        Until the app has finished its initial mount, a compose/mount failure leaves
        a half-built widget tree with no surface to toast on, so those errors fall
        through to Textual's default teardown (`_is_mounted` is only set once the
        app's Compose and Mount have succeeded). Once mounted, a worker or handler
        error is logged, surfaced as an error toast, and swallowed so the session
        survives. The `_exception` bookkeeping is preserved so `run_test()` still
        re-raises and tests keep surfacing bugs; `run()` never re-raises it, so a
        real session stays open.
        """
        if not self._is_mounted:
            super()._handle_exception(error)
            return
        original = error.error if isinstance(error, WorkerFailed) else error
        try:
            # The net must never crash on its own reporting — an unwritable log dir
            # or a failed toast cannot be allowed to become the fatal error.
            log_exception(original)
            self.notify(self._error_message(original), title="Error", severity="error")
        except Exception:
            pass
        # Preserve Textual's bookkeeping so `run_test()` re-raises and tests keep
        # surfacing bugs; `run()` never re-raises it, so a real session stays open.
        if self._exception is None:
            self._exception = error
            self._exception_event.set()

    @staticmethod
    def _error_message(error: BaseException) -> str:
        """A domain error's message is user-safe; anything else stays generic."""
        if isinstance(error, UniversalRemoteError):
            return str(error)
        return f"Something went wrong — {type(error).__name__}. The error was logged."
