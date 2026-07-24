import asyncio

from textual.widgets import DataTable

from universal_remote.devices.store import DeviceStore
from universal_remote.preferences.store import Preferences, PreferencesStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.devices_screen import DeviceListScreen
from universal_remote.tui.menu import MenuScreen
from universal_remote.tui.shortcuts import CATALOG
from universal_remote.tui.shortcuts_screen import (
    CaptureModal,
    ShortcutsCommandProvider,
    ShortcutsScreen,
    ShortcutsViewModal,
)

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
    def test_given_the_screen_when_shown_then_every_action_is_listed_under_a_group(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                table = app.screen.query_one(DataTable)
                for action in CATALOG:
                    table.get_row_index(action.id)  # raises if the row is missing
                for scope in ("home", "global", "remote"):
                    table.get_row_index(f"__group__{scope}")  # surface header row

        asyncio.run(scenario())

    def test_given_a_group_header_when_activated_then_no_capture_modal_opens(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                table = app.screen.query_one(DataTable)
                table.move_cursor(row=table.get_row_index("__group__remote"))
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, ShortcutsScreen)  # not a modal

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

    def test_given_the_table_when_j_pressed_then_the_cursor_moves_down_one_row(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                table = app.screen.query_one(DataTable)
                start = table.cursor_row
                await pilot.press("j")
                await pilot.pause()
                assert table.cursor_row == start + 1

        asyncio.run(scenario())

    def test_given_the_table_when_k_pressed_then_the_cursor_moves_up_one_row(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                table = app.screen.query_one(DataTable)
                table.move_cursor(row=table.cursor_row + 1)
                start = table.cursor_row
                await pilot.press("k")
                await pilot.pause()
                assert table.cursor_row == start - 1

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

    def test_given_the_modal_when_del_button_clicked_then_the_shortcut_is_cleared(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "remote.ok")
                await pilot.click("#capture-del")
                await pilot.pause()
                assert app.shortcut_overrides["remote.ok"] == ""
                assert isinstance(app.screen, ShortcutsScreen)
                table = app.screen.query_one(DataTable)
                assert _cell(table, "remote.ok", 1) == ""

        asyncio.run(scenario())

    def test_given_the_modal_when_delete_key_pressed_then_delete_is_assigned(
        self, tmp_path
    ):
        # Delete is now an ordinary key: pressing it assigns `delete`, it does not clear.
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "remote.vol_up")
                await pilot.press("delete")
                await pilot.pause()
                assert app.shortcut_overrides["remote.vol_up"] == "delete"
                assert isinstance(app.screen, ShortcutsScreen)

        asyncio.run(scenario())

    def test_given_the_modal_when_escape_pressed_then_it_is_captured_not_cancelled(
        self, tmp_path
    ):
        # Escape is a normal key now: it routes through assign. Here it conflicts with
        # Go Back's default, so the modal stays open with an error — it does not cancel.
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "remote.vol_up")
                await pilot.press("escape")
                await pilot.pause()
                assert "remote.vol_up" not in app.shortcut_overrides
                assert isinstance(app.screen, CaptureModal)  # captured, not cancelled
                assert any(n.severity == "error" for n in app._notifications)

        asyncio.run(scenario())

    def test_given_go_back_cleared_when_escape_pressed_then_escape_is_assigned(
        self, tmp_path
    ):
        # With Go Back's escape freed, Escape is assignable like any other key.
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.shortcut_overrides["global.go_back"] = ""
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "remote.vol_up")
                await pilot.press("escape")
                await pilot.pause()
                assert app.shortcut_overrides["remote.vol_up"] == "escape"
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
    def test_given_a_taken_key_when_assigned_then_it_is_refused(self, tmp_path):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "remote.mute")
                await pilot.press("t")  # `t` is Text entry's key — taken app-wide
                await pilot.pause()
                assert "remote.mute" not in app.shortcut_overrides
                assert isinstance(app.screen, CaptureModal)  # stays open to retry
                assert any(n.severity == "error" for n in app._notifications)

        asyncio.run(scenario())

    def test_given_a_tab_key_when_assigned_then_it_is_refused(self, tmp_path):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                await _open_modal(app, pilot, "remote.mute")
                await pilot.press("tab")  # reserved for focus navigation
                await pilot.pause()
                assert "remote.mute" not in app.shortcut_overrides
                assert isinstance(app.screen, CaptureModal)
                assert any(n.severity == "error" for n in app._notifications)

        asyncio.run(scenario())


class TestCommandPalette:
    def test_given_the_app_then_the_shortcuts_provider_is_registered(self):
        assert ShortcutsCommandProvider in UniversalRemoteApp.COMMANDS

    def test_given_the_provider_when_shown_then_the_read_only_view_opens(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                provider = ShortcutsCommandProvider(app.screen)
                provider._show()
                await pilot.pause()
                assert isinstance(app.screen, ShortcutsViewModal)
                table = app.screen.query_one(DataTable)
                for action in CATALOG:
                    table.get_row_index(action.id)  # every action listed

        asyncio.run(scenario())

    def test_given_the_provider_when_discovered_then_one_command_is_offered(
        self, tmp_path
    ):
        # Exercises the real discover() path + DiscoveryHit construction.
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE):
                provider = ShortcutsCommandProvider(app.screen)
                hits = [hit async for hit in provider.discover()]
                assert len(hits) == 1

        asyncio.run(scenario())

    def test_given_the_provider_when_searched_then_the_hit_opens_the_view(
        self, tmp_path
    ):
        # Exercises the real search() path + Hit construction, then runs the callback.
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                provider = ShortcutsCommandProvider(app.screen)
                hits = [hit async for hit in provider.search("keyboard")]
                assert hits
                hits[0].command()
                await pilot.pause()
                assert isinstance(app.screen, ShortcutsViewModal)

        asyncio.run(scenario())

    def test_given_the_read_only_view_when_j_pressed_then_the_cursor_moves_down(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsViewModal())
                await pilot.pause()
                table = app.screen.query_one(DataTable)
                start = table.cursor_row
                await pilot.press("j")
                await pilot.pause()
                assert table.cursor_row == start + 1

        asyncio.run(scenario())

    def test_given_the_read_only_view_when_a_row_is_activated_then_no_capture_opens(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsViewModal())
                await pilot.pause()
                table = app.screen.query_one(DataTable)
                table.move_cursor(row=table.get_row_index("remote.vol_up"))
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, ShortcutsViewModal)  # read-only

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


class TestReservedOverrideMigration:
    def test_given_an_override_on_a_now_reserved_key_when_loaded_then_it_is_dropped(
        self, tmp_path
    ):
        # `e` was assignable to Stop before it was reserved for edit-mode; a stale
        # saved override on it must be pruned on load and re-persisted, while a free
        # override survives.
        prefs = PreferencesStore(path=tmp_path / "settings.json")
        prefs.save(Preferences(shortcuts={"remote.stop": "e", "remote.mute": "m"}))

        async def scenario():
            app = UniversalRemoteApp(
                store=DeviceStore(path=tmp_path / "d.json"),
                registry=AdapterRegistry(),
                preferences=prefs,
            )
            async with app.run_test(size=_SIZE) as pilot:
                await pilot.pause()
                assert "remote.stop" not in app.shortcut_overrides
                assert app.shortcut_overrides["remote.mute"] == "m"

        asyncio.run(scenario())

        # The cleaned map was written back, so the stale override stays gone next run.
        assert "remote.stop" not in prefs.load().shortcuts
