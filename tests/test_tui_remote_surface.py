import asyncio

from textual.widgets import Button, Label

from tests.fakes import FakeAdapter
from universal_remote.capabilities import Capabilities
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.keys import Key
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.remote_screen import RemoteScreen, TextField


def _app(store, adapter):
    registry = AdapterRegistry()
    registry.register(adapter)
    return UniversalRemoteApp(store=store, registry=registry)


def _store_with_device(tmp_path):
    store = DeviceStore(path=tmp_path / "d.json")
    store.add(Device(name="TV", platform="fake-tv", ip="1.1.1.1", credential="tok"))
    return store


async def _goto_remote(app, pilot):
    await pilot.press("r")
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()
    assert isinstance(app.screen, RemoteScreen)


class TestRemoteSurface:
    def test_given_the_full_button_set_on_an_80x24_terminal_then_the_remote_does_not_scroll(
        self, tmp_path
    ):
        # Arrange: a full-capability adapter so every button renders.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=(80, 24)) as pilot:
                await _goto_remote(app, pilot)

                # Assert: the whole screen fits — no vertical scroll range. The
                # remote sizes to its content (`#remote` is height:auto), so a
                # button set taller than 80×24 makes the screen scroll and this
                # fires; compact one-row buttons keep it at zero.
                assert app.screen.max_scroll_y == 0

        asyncio.run(scenario())

    def test_given_the_compact_style_when_shown_then_buttons_render_a_visible_row(
        self, tmp_path
    ):
        # Regression: the borderless compact style must leave each button one row
        # tall. If `border: none` fails to win, box-sizing collapses the content
        # to zero rows and every button renders blank (no label).
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=(80, 24)) as pilot:
                await _goto_remote(app, pilot)
                for key in (Key.MENU, Key.OK, Key.VOL_UP, Key.NUM_0):
                    button = app.screen.query_one(f"#key-{key.name.lower()}", Button)
                    assert button.size.height == 1

        asyncio.run(scenario())

    def test_given_the_dpad_when_shown_then_it_forms_a_centered_cross(self, tmp_path):
        # The D-pad should read like a physical remote: Up and Down centered over
        # OK, with Left and Right symmetric around it — not left-packed in a column.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        def center(button):
            return button.region.x + button.region.width / 2

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=(80, 24)) as pilot:
                await _goto_remote(app, pilot)
                q = app.screen.query_one
                up, ok, down = (q(f"#key-{k}", Button) for k in ("up", "ok", "down"))
                left, right = q("#key-left", Button), q("#key-right", Button)
                # Up and Down sit over OK (within a cell), forming the vertical bar.
                assert abs(center(up) - center(ok)) <= 1
                assert abs(center(down) - center(ok)) <= 1
                # Left and Right flank OK symmetrically, forming the horizontal bar.
                assert center(left) < center(ok) < center(right)

        asyncio.run(scenario())

    def test_given_the_remote_when_shown_then_every_key_has_a_button(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                ids = {button.id for button in app.screen.query(Button)}
                expected = {f"key-{key.name.lower()}" for key in Key}
                assert expected <= ids

        asyncio.run(scenario())

    def test_given_menu_and_channel_buttons_when_clicked_then_their_keys_are_sent(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.click("#key-menu")
                await pilot.click("#key-ch_up")
                await pilot.click("#key-ch_down")
                await pilot.pause()

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == [Key.MENU, Key.CH_UP, Key.CH_DOWN]

    def test_given_media_transport_buttons_when_clicked_then_their_keys_are_sent(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                for key in (
                    Key.REWIND,
                    Key.PLAY,
                    Key.PAUSE,
                    Key.PLAY_PAUSE,
                    Key.STOP,
                    Key.FAST_FORWARD,
                ):
                    await pilot.click(f"#key-{key.name.lower()}")
                await pilot.pause()

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == [
            Key.REWIND,
            Key.PLAY,
            Key.PAUSE,
            Key.PLAY_PAUSE,
            Key.STOP,
            Key.FAST_FORWARD,
        ]

    def test_given_a_button_when_clicked_then_the_mapped_key_is_sent(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.click("#key-mute")
                await pilot.pause()

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == [Key.MUTE]

    def test_given_the_remote_when_arrow_keys_pressed_then_dpad_ok_and_back_map(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.press("up")
                await pilot.press("left")
                await pilot.press("enter")
                await pilot.press("escape")
                await pilot.pause()

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == [
            Key.UP,
            Key.LEFT,
            Key.OK,
            Key.BACK,
        ]

    def test_given_the_remote_when_vim_keys_pressed_then_the_dpad_directions_map(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.press("h")
                await pilot.press("j")
                await pilot.press("k")
                await pilot.press("l")
                await pilot.pause()

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == [
            Key.LEFT,
            Key.DOWN,
            Key.UP,
            Key.RIGHT,
        ]

    def test_given_the_remote_when_space_pressed_then_home_is_sent(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.press("space")
                await pilot.pause()

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == [Key.HOME]

    def test_given_the_text_field_focused_when_vim_keys_and_space_typed_then_they_fill_not_navigate(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.press("t")  # enter the text field
                await pilot.pause()
                await pilot.press("h", "j", "k", "l", "space")
                await pilot.pause()
                assert app.screen.query_one("#text", TextField).value == "hjkl "

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == []  # no D-pad, no HOME while typing

    def test_given_a_number_pad_button_when_clicked_then_its_key_is_sent(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.click("#key-num_5")
                await pilot.pause()

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == [Key.NUM_5]

    def test_given_the_remote_when_digit_keys_pressed_then_the_number_keys_are_sent(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                for digit in range(10):
                    await pilot.press(str(digit))
                await pilot.pause()

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == [Key[f"NUM_{d}"] for d in range(10)]

    def test_given_the_text_field_focused_when_digits_typed_then_they_fill_not_send(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.press("t")  # enter the text field
                await pilot.pause()
                await pilot.press("1", "2", "3")
                await pilot.pause()
                assert app.screen.query_one("#text", TextField).value == "123"

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == []  # no number keys while typing

    def test_given_no_number_support_when_a_digit_is_pressed_then_nothing_and_no_error(
        self, tmp_path
    ):
        # An adapter without number keys (like Apple TV): the digit hotkey behaves
        # like the disabled button — nothing sent, no error message.
        store = _store_with_device(tmp_path)
        caps = Capabilities(
            keys=frozenset(Key) - {Key[f"NUM_{d}"] for d in range(10)}, text=True
        )
        adapter = FakeAdapter(platform="fake-tv", capabilities=caps)

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.press("5")
                await pilot.pause()
                status = str(app.screen.query_one("#text-status", Label).content)
                assert status == ""

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == []

    def test_given_a_key_dispatch_fails_when_pressed_then_the_remote_survives(
        self, tmp_path
    ):
        # Arrange: a live remote whose device will fail the next key dispatch.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                adapter.sessions[0].dispatch_error = RuntimeError("device dropped")

                # Act: press a key that will raise inside dispatch.
                await pilot.press("up")
                await pilot.pause()

                # Assert: the remote is still up and reports the failure.
                assert isinstance(app.screen, RemoteScreen)
                status = app.screen.query_one("#text-status", Label)
                assert "UP" in str(status.content)

        asyncio.run(scenario())
