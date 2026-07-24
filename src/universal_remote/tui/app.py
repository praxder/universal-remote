"""The root Textual application, holding the device store and adapter registry."""

from __future__ import annotations

from textual.app import App, SystemCommand
from textual.screen import Screen
from textual.worker import WorkerFailed

from typing import Callable, Iterable

from ..devices.store import DeviceStore
from ..error_log import log_exception
from ..errors import UniversalRemoteError
from ..preferences.store import Preferences, PreferencesStore
from ..registry import AdapterRegistry
from ..registry import registry as default_registry
from .custom_buttons import forget_device
from .menu import MenuScreen
from .quotes import Quote, random_quote
from .shortcuts_screen import ShortcutsCommandProvider


class UniversalRemoteApp(App[None]):
    """Launches into the entry menu; screens read `store` and `registry` off the app."""

    TITLE = "Universal Remote"

    # Add the read-only "Keyboard Shortcuts" entry to the default command palette.
    COMMANDS = App.COMMANDS | {ShortcutsCommandProvider}

    CSS = """
    Screen { align: center middle; }
    #menu { width: 100%; height: auto; }
    #menu Button { width: 28; margin: 1 0; }
    /* Settings entry: a bottom-left button docked above the Footer (which docks
       last, so it stays below this). Left-aligned; the centered #menu is untouched. */
    #settings-bar { dock: bottom; height: auto; width: 100%; align-horizontal: left; }
    #settings-bar Button { width: auto; margin: 0 0 2 2; }
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
    /* wider than #devices-title so the "Add/Edit Device" banner never wraps;
       same top/bottom margin as #devices-title */
    #add-title { width: 52; text-align: left; margin: 1 0 1 0; color: $accent; }
    /* wide enough for the "Select Device" banner; padded above and below */
    #use-remote-title { width: 58; text-align: left; margin: 1 0 1 0; color: $accent; }
    /* wide enough for the "Discover" banner; padded like the Devices banner */
    #discover-title { width: 40; text-align: left; margin: 1 0 1 0; color: $accent; }
    /* wide enough for the "Settings" banner; padded like the other banners */
    #settings-title { width: 40; text-align: left; margin: 1 0 1 0; color: $accent; }
    /* Settings rows: each wrapped in Center; the version is a muted, non-interactive label */
    #settings { width: 100%; height: auto; }
    #settings Button { width: 40; margin-bottom: 1; }
    #settings #version { width: auto; margin-top: 1; color: $text-muted; }
    /* the "searching" indicator: an animated spinner + bold text, hidden once done */
    #discover-status { height: 1; margin-top: 1; }
    #discover-status LoadingIndicator { width: 8; height: 1; color: $accent; }
    #discover-status-text {
        width: auto; height: 1; margin-left: 2;
        text-style: bold; color: $accent;
    }
    /* left edge aligned with the fields above (no left indent) */
    #add-device #save { margin: 1 0 0 0; }
    /* edit-only Delete button: same left edge and top margin as Save */
    #add-device #delete { margin: 1 0 0 0; }
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
        preferences: PreferencesStore | None = None,
    ) -> None:
        super().__init__()
        self.store = store or DeviceStore()
        self.registry = registry or default_registry
        self.quote_provider = quote_provider or random_quote
        self.preferences = preferences or PreferencesStore()
        # Action id -> key overrides for the catalogued shortcuts; populated from the
        # saved preferences on mount (see `on_mount`) and edited live from the
        # Keyboard Shortcuts screen. Screens read this to build their bindings.
        self.shortcut_overrides: dict[str, str] = {}
        # Layered custom-button titles keyed by scope; populated from saved preferences
        # on mount and read by the remote to label its custom buttons. Resolution lives
        # in `tui.custom_buttons`.
        self.custom_buttons: dict = {}
        # Set true only once our own mount handler has run, so the safety net can
        # tell a post-mount error (stay open) from a startup/compose/mount failure
        # (fall through). See `_handle_exception`.
        self._mount_succeeded = False

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        """Drop the Maximize and Screenshot commands from the command palette."""
        for command in super().get_system_commands(screen):
            if command.title in ("Maximize", "Screenshot"):
                continue
            yield command

    def watch_theme(self, theme_name: str) -> None:
        """Persist every theme change, wherever it originates.

        Textual dispatches both its own private `_watch_theme` and this public
        watcher, so a change from the Settings picker or the command palette is
        saved here without touching framework internals. The current shortcuts ride
        along so saving the theme never drops them.
        """
        self.persist_preferences()

    def delete_device(self, device_id: str) -> None:
        """Remove a saved device and the custom-button titles scoped only to it.

        Deletes from the device store and purges that device's device-scoped
        `custom_buttons` entries (device-type and global titles stand), then persists
        the preferences — the two stores are kept in step here so both delete sites
        do it the same way.
        """
        self.store.delete(device_id)
        forget_device(self.custom_buttons, device_id)
        self.persist_preferences()

    def persist_preferences(self) -> None:
        """Write the current theme, shortcuts, and custom buttons together, best-effort."""
        self.preferences.save(
            Preferences(
                theme=self.theme,
                shortcuts=dict(self.shortcut_overrides),
                custom_buttons=self.custom_buttons,
            )
        )

    def apply_shortcuts(self) -> None:
        """Rebuild the catalogued bindings of every mounted screen from the overrides.

        Called after a shortcut is assigned or cleared so the change takes effect
        without a restart across the whole screen stack.
        """
        from .shortcuts import rebuild_shortcuts

        for screen in self.screen_stack:
            scopes = getattr(screen, "SHORTCUT_SCOPES", None)
            if scopes:
                hide = getattr(screen, "SHORTCUT_HIDE", ())
                rebuild_shortcuts(screen, self.shortcut_overrides, scopes, hide=hide)

    def on_mount(self) -> None:
        from .shortcuts import without_bare_modifiers, without_reserved

        preferences = self.preferences.load()
        # Load saved shortcuts into the override map before the menu is pushed, so
        # its bindings (and every later screen's) build from them. Drop any override
        # whose key has since become reserved (e.g. `e` bound to a device action before
        # it was reserved for edit-mode) or is a lone modifier (assignable before the
        # `is_bare_modifier` guard was fixed): left in place either would bind a fixed
        # or modifier-only key, so the action reverts to its default. `update` keeps
        # any overrides set directly on the app (e.g. in tests) when none are saved.
        kept = without_bare_modifiers(without_reserved(preferences.shortcuts))
        self.shortcut_overrides.update(kept)
        # Load saved custom-button titles the same way, before any remote is opened.
        self.custom_buttons.update(preferences.custom_buttons)
        # Ignore a saved theme that is no longer registered (e.g. removed by a
        # Textual upgrade) so `_validate_theme` cannot raise; the default stands.
        if preferences.theme in self.available_themes:
            self.theme = preferences.theme
        # Persist the cleaned overrides so a pruned stale binding stays gone next run.
        if kept != preferences.shortcuts:
            self.persist_preferences()
        self.push_screen(MenuScreen())
        self._mount_succeeded = True

    def _handle_exception(self, error: Exception) -> None:
        """App-wide safety net: an unexpected error toasts and stays, not crashes.

        Until our own `on_mount` has run there is no surface to toast on, so a
        startup/compose/mount failure falls through to Textual's default teardown.
        We gate on our own `_mount_succeeded` flag rather than Textual's
        `_is_mounted`, which is set unconditionally even when compose/mount raises
        and so cannot distinguish the two. Once mounted, a worker or handler error is
        logged, surfaced as an error toast, and swallowed so the session survives.
        The `_exception` bookkeeping is preserved so `run_test()` still re-raises and
        tests keep surfacing bugs; `run()` never re-raises it, so a real session
        stays open.
        """
        if not self._mount_succeeded:
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
