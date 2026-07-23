import asyncio

from textual.app import App
from textual.containers import VerticalScroll

from universal_remote.tui.actions import (
    ScriptResult,
    ScriptResultModal,
    present_result,
)

_OK = ScriptResult(True, 0, "all good\n", "", "Succeeded")
_FAIL = ScriptResult(False, 2, "", "boom\n", "Exited with code 2")


class _Host(App[None]):
    """A bare app that records notifications so toast wiring can be asserted."""

    def __init__(self) -> None:
        super().__init__()
        self.notifications: list[tuple[str, str]] = []

    def notify(self, message, *, title="", severity="information", **_kwargs) -> None:
        self.notifications.append((message, severity))


class TestDontShow:
    def test_given_a_success_when_results_are_hidden_then_nothing_is_shown(self):
        async def scenario():
            app = _Host()
            async with app.run_test() as pilot:
                present_result(app, _OK, show_results=False)
                await pilot.pause()
                assert app.notifications == []
                assert not isinstance(app.screen, ScriptResultModal)

        asyncio.run(scenario())

    def test_given_a_failure_when_results_are_hidden_then_an_error_toast_fires(self):
        async def scenario():
            app = _Host()
            async with app.run_test() as pilot:
                present_result(app, _FAIL, show_results=False)
                await pilot.pause()
                assert len(app.notifications) == 1
                message, severity = app.notifications[0]
                assert severity == "error"
                assert "code 2" in message
                assert not isinstance(app.screen, ScriptResultModal)

        asyncio.run(scenario())


class TestShow:
    def test_given_a_success_when_results_are_shown_then_a_result_modal_opens(self):
        async def scenario():
            app = _Host()
            async with app.run_test() as pilot:
                present_result(app, _OK, show_results=True)
                await pilot.pause()
                assert isinstance(app.screen, ScriptResultModal)
                # No toast when the modal carries the outcome.
                assert app.notifications == []

        asyncio.run(scenario())

    def test_given_a_failure_when_results_are_shown_then_the_modal_reports_it(self):
        from textual.widgets import Label

        async def scenario():
            app = _Host()
            async with app.run_test() as pilot:
                present_result(app, _FAIL, show_results=True)
                await pilot.pause()
                assert isinstance(app.screen, ScriptResultModal)
                exit_label = app.screen.query_one("#script-result-exit", Label)
                assert "2" in str(exit_label.render())

        asyncio.run(scenario())


class TestResultModalStructure:
    def test_given_the_result_modal_when_open_then_its_output_pane_scrolls(self):
        async def scenario():
            app = _Host()
            async with app.run_test() as pilot:
                present_result(app, _FAIL, show_results=True)
                await pilot.pause()
                # A scrollable container so long output is shown in full, not clipped.
                assert isinstance(
                    app.screen.query_one("#script-result-output"), VerticalScroll
                )

        asyncio.run(scenario())

    def test_given_the_result_modal_when_shown_then_the_full_output_is_present(self):
        long_output = "line\n" * 200
        result = ScriptResult(True, 0, long_output, "", "Succeeded")

        async def scenario():
            app = _Host()
            async with app.run_test() as pilot:
                present_result(app, result, show_results=True)
                await pilot.pause()
                body = app.screen.query_one("#script-result-body")
                assert str(body.render()).count("line") == 200

        asyncio.run(scenario())
