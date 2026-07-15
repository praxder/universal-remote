import asyncio

from textual.widgets import Button

from universal_remote.adapters.appletv import PLATFORM as APPLETV_PLATFORM
from universal_remote.adapters.firetv import PLATFORM as FIRETV_PLATFORM
from universal_remote.adapters.lg import PLATFORM as LG_PLATFORM
from universal_remote.adapters.roku import PLATFORM as ROKU_PLATFORM
from universal_remote.adapters.samsung import PLATFORM
from universal_remote.cli import build_app
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.tui.devices_screen import DeviceListScreen


class TestCliWiring:
    def test_given_the_built_app_when_started_then_samsung_is_registered_and_the_menu_shows(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        app = build_app(store=store)

        async def scenario():
            async with app.run_test() as pilot:
                await pilot.pause()
                assert app.registry.is_supported(PLATFORM)
                assert app.registry.is_supported(LG_PLATFORM)
                assert app.registry.is_supported(APPLETV_PLATFORM)
                assert app.registry.is_supported(ROKU_PLATFORM)
                assert app.registry.is_supported(FIRETV_PLATFORM)
                labels = {str(button.label) for button in app.screen.query(Button)}
                assert {"Manage Devices", "Use Remote"} <= labels

        asyncio.run(scenario())

    def test_given_a_saved_samsung_device_when_managing_then_the_registry_resolves_its_adapter(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="Den TV", platform=PLATFORM, ip="10.0.0.5"))
        app = build_app(store=store)

        async def scenario():
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)
                adapter = app.registry.resolve(PLATFORM)
                assert adapter.platform == PLATFORM

        asyncio.run(scenario())
