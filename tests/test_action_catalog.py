import asyncio

from textual.app import App
from textual.widgets import OptionList

from universal_remote.tui.actions import (
    ACTION_CATALOG,
    ActionTypeListModal,
    RunScriptConfigModal,
    action_type,
)


class _Host(App[None]):
    """Pushes an ActionTypeListModal and records the value it dismisses with."""

    def __init__(self) -> None:
        super().__init__()
        self.captured = False
        self.result = "<unset>"

    def on_mount(self) -> None:
        self.push_screen(ActionTypeListModal(), self._capture)

    def _capture(self, value) -> None:
        self.captured = True
        self.result = value


class TestCatalog:
    def test_given_the_catalog_when_read_then_it_holds_one_run_script_entry(self):
        assert len(ACTION_CATALOG) == 1
        assert ACTION_CATALOG[0].id == "run_script"
        assert ACTION_CATALOG[0].label == "Run Custom Script"

    def test_given_run_script_when_looked_up_then_its_config_modal_is_returned(self):
        entry = action_type("run_script")

        assert entry.config_modal is RunScriptConfigModal

    def test_given_an_unknown_type_when_looked_up_then_it_is_none(self):
        assert action_type("nope") is None


class TestActionTypeListModal:
    def test_given_the_list_when_open_then_it_shows_the_catalog_labels(self):
        async def scenario():
            app = _Host()
            async with app.run_test() as pilot:
                await pilot.pause()
                options = app.screen.query_one(OptionList)
                labels = [
                    str(options.get_option_at_index(i).prompt)
                    for i in range(options.option_count)
                ]
                assert labels == ["Run Custom Script"]

        asyncio.run(scenario())

    def test_given_run_script_selected_when_chosen_then_the_config_modal_opens(self):
        async def scenario():
            app = _Host()
            async with app.run_test() as pilot:
                await pilot.pause()
                # Selecting the only entry opens its configuration modal.
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, RunScriptConfigModal)

        asyncio.run(scenario())

    def test_given_the_config_completes_when_it_returns_then_the_list_returns_it(self):
        # The list forwards the configured action up to its own caller, so the Button
        # Config modal receives the finished action regardless of the type chosen.
        async def scenario():
            app = _Host()
            async with app.run_test(size=(90, 40)) as pilot:
                await pilot.pause()
                await pilot.press("enter")  # choose Run Custom Script
                await pilot.pause()
                await pilot.click("#source-inline")
                await pilot.pause()
                app.screen.query_one("#run-script-inline").text = "echo hi"
                await pilot.click("#run-script-ok")
                await pilot.pause()
                assert app.result == {
                    "type": "run_script",
                    "source": "inline",
                    "script": "echo hi",
                    "show_results": False,
                }

        asyncio.run(scenario())
