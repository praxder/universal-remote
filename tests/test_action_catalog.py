import asyncio

from textual.app import App
from textual.widgets import OptionList

from universal_remote.tui import actions
from universal_remote.tui.actions import (
    ACTION_CATALOG,
    ActionContext,
    ActionResult,
    ActionType,
    ActionTypeListModal,
    RunMacroConfigModal,
    RunScriptConfigModal,
    action_type,
    run_action,
)


def _context(remote_ip: str = "10.0.0.5") -> ActionContext:
    """A context with only the fields these tests read; the rest are placeholders."""
    return ActionContext(
        app=None,
        remote_ip=remote_ip,
        session=None,
        macros={},
        custom_buttons={},
        device_id="dev-1",
        platform="fake-tv",
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
    def test_given_the_catalog_when_read_then_it_holds_run_script_and_run_macro(self):
        assert [(entry.id, entry.label) for entry in ACTION_CATALOG] == [
            ("run_script", "Run Custom Script"),
            ("run_macro", "Run Macro"),
        ]

    def test_given_run_script_when_looked_up_then_its_config_modal_is_returned(self):
        entry = action_type("run_script")

        assert entry.config_modal is RunScriptConfigModal

    def test_given_run_macro_when_looked_up_then_its_config_modal_is_returned(self):
        entry = action_type("run_macro")

        assert entry.config_modal is RunMacroConfigModal

    def test_given_an_unknown_type_when_looked_up_then_it_is_none(self):
        assert action_type("nope") is None

    def test_given_run_macro_when_read_then_it_reports_its_own_outcome(self):
        # Playback names a failing step itself, so the shared path must stay quiet;
        # Run Custom Script still surfaces its result per the button's Results choice.
        assert action_type("run_macro").reports_own_outcome is True
        assert action_type("run_script").reports_own_outcome is False


class TestRunAction:
    def test_given_an_action_when_run_then_its_runner_receives_the_context(
        self, monkeypatch
    ):
        # Arrange: a probe type registered in the catalog, recording what it is given.
        received = []

        async def runner(action, context):
            received.append(context)
            return ActionResult(True, 0, "", "", "probed")

        monkeypatch.setitem(
            actions._CATALOG_BY_ID,
            "probe",
            ActionType("probe", "Probe", RunScriptConfigModal, runner),
        )
        context = _context()

        # Act
        result = asyncio.run(run_action({"type": "probe"}, context))

        # Assert: the context object itself is handed to the runner, unchanged.
        assert received == [context]
        assert result.message == "probed"

    def test_given_an_unknown_type_when_run_then_it_fails_without_raising(self):
        result = asyncio.run(run_action({"type": "nope"}, _context()))

        assert result.ok is False
        assert "nope" in result.message

    def test_given_run_script_when_run_then_it_reads_the_ip_from_the_context(self):
        # The shared contract hands every runner a context; run_script reads only
        # `remote_ip` from it and injects that into the script's environment.
        action = {
            "type": "run_script",
            "source": "inline",
            "script": 'echo "$REMOTE_IP"',
        }

        result = asyncio.run(run_action(action, _context("7.7.7.7")))

        assert result.stdout.strip() == "7.7.7.7"


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
                assert labels == ["Run Custom Script", "Run Macro"]

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
