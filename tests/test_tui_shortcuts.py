import asyncio

from textual.widgets import DataTable

from universal_remote.devices.store import DeviceStore
from universal_remote.preferences.store import PreferencesStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.devices_screen import DeviceListScreen
from universal_remote.tui.menu import MenuScreen
from universal_remote.tui.shortcuts import CATALOG
from universal_remote.tui.shortcuts_screen import CaptureModal, ShortcutsScreen

_SIZE = (100, 50)


def _app(tmp_path):
    return UniversalRemoteApp(
        store=DeviceStore(path=tmp_path / "d.json"),
        registry=AdapterRegistry(),
        preferences=PreferencesStore(path=tmp_path / "settings.json"),
    )


def _cell(table, action_id, column):
    return str(table.get_row(action_id)[column])


async def _open_modal(app, pilot, action_id):
    table = app.screen.query_one(DataTable)
    table.move_cursor(row=table.get_row_index(action_id))
    await pilot.press("enter")
    await pilot.pause()


class TestShortcutsTable:
    def test_given_the_screen_when_shown_then_a_row_per_catalog_entry_is_listed(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                table = app.screen.query_one(DataTable)
                assert table.row_count == len(CATALOG)

        asyncio.run(scenario())

    def test_given_a_bound_action_when_shown_then_its_shortcut_is_the_readable_label(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                table = app.screen.query_one(DataTable)
                assert _cell(table, "remote.ok", 1) == "ENTER"

        asyncio.run(scenario())

    def test_given_an_unbound_action_when_shown_then_its_shortcut_cell_is_blank(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                table = app.screen.query_one(DataTable)
                assert _cell(table, "remote.vol_up", 1) == ""

        asyncio.run(scenario())

    def test_given_a_reserved_dpad_row_when_shown_then_it_lists_arrow_and_alias(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                table = app.screen.query_one(DataTable)
                assert _cell(table, "remote.up", 1) == "UP / K"

        asyncio.run(scenario())

    def test_given_a_reserved_row_when_activated_then_no_capture_modal_opens(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "remote.up")
                assert isinstance(app.screen, ShortcutsScreen)

        asyncio.run(scenario())


class TestCaptureModal:
    def test_given_a_rebindable_row_when_activated_then_the_capture_modal_opens(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "remote.vol_up")
                assert isinstance(app.screen, CaptureModal)

        asyncio.run(scenario())

    def test_given_the_modal_when_an_available_key_is_pressed_then_it_is_assigned(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "remote.vol_up")
                await pilot.press("v")
                await pilot.pause()
                assert app.shortcut_overrides["remote.vol_up"] == "v"
                assert isinstance(app.screen, ShortcutsScreen)
                table = app.screen.query_one(DataTable)
                assert _cell(table, "remote.vol_up", 1) == "V"

        asyncio.run(scenario())

    def test_given_an_assignment_when_made_then_it_is_persisted(self, tmp_path):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "remote.vol_up")
                await pilot.press("v")
                await pilot.pause()

        asyncio.run(scenario())

        saved = PreferencesStore(path=tmp_path / "settings.json").load()
        assert saved.shortcuts["remote.vol_up"] == "v"

    def test_given_the_modal_when_delete_is_pressed_then_the_shortcut_is_cleared(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "remote.ok")
                await pilot.press("delete")
                await pilot.pause()
                assert app.shortcut_overrides["remote.ok"] == ""
                assert isinstance(app.screen, ShortcutsScreen)
                table = app.screen.query_one(DataTable)
                assert _cell(table, "remote.ok", 1) == ""

        asyncio.run(scenario())

    def test_given_the_modal_when_escape_is_pressed_then_the_shortcut_is_unchanged(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "remote.vol_up")
                await pilot.press("escape")
                await pilot.pause()
                assert "remote.vol_up" not in app.shortcut_overrides
                assert isinstance(app.screen, ShortcutsScreen)

        asyncio.run(scenario())

    def test_given_the_modal_when_cancel_is_clicked_then_the_shortcut_is_unchanged(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "remote.vol_up")
                await pilot.click("#capture-cancel")
                await pilot.pause()
                assert "remote.vol_up" not in app.shortcut_overrides
                assert isinstance(app.screen, ShortcutsScreen)

        asyncio.run(scenario())


class TestLiveApply:
    def test_given_a_home_shortcut_changed_when_back_on_the_menu_then_it_is_live(
        self, tmp_path
    ):
        # The Menu is mounted below Settings and Shortcuts; assigning a Home key must
        # rebuild it in place so the new key works on return, without a restart.
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                await pilot.press("s")  # menu -> settings
                await pilot.pause()
                await pilot.click("#keybindings")  # settings -> shortcuts
                await pilot.pause()
                await _open_modal(app, pilot, "home.manage_devices")
                await pilot.press("x")
                await pilot.pause()
                await pilot.press("escape")  # shortcuts -> settings
                await pilot.pause()
                await pilot.press("escape")  # settings -> menu
                await pilot.pause()
                assert isinstance(app.screen, MenuScreen)
                await pilot.press("x")  # the freshly-bound key fires live
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)

        asyncio.run(scenario())


class TestCaptureRejection:
    def test_given_a_same_scope_taken_key_when_assigned_then_it_is_refused(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "remote.mute")
                await pilot.press("t")  # `t` is Text entry's key on the same surface
                await pilot.pause()
                assert "remote.mute" not in app.shortcut_overrides
                assert isinstance(app.screen, CaptureModal)  # stays open to retry
                assert any(n.severity == "error" for n in app._notifications)

        asyncio.run(scenario())

    def test_given_go_back_assigned_a_remote_key_when_assigned_then_it_is_refused(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "global.go_back")
                await pilot.press("t")
                await pilot.pause()
                assert "global.go_back" not in app.shortcut_overrides
                assert any(n.severity == "error" for n in app._notifications)

        asyncio.run(scenario())

    def test_given_a_reserved_key_when_assigned_then_it_is_refused(self, tmp_path):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "remote.mute")
                await pilot.press("j")  # a reserved D-pad alias
                await pilot.pause()
                assert "remote.mute" not in app.shortcut_overrides
                assert any(n.severity == "error" for n in app._notifications)

        asyncio.run(scenario())
