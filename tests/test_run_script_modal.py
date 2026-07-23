import asyncio

from textual.app import App
from textual.widgets import Input, Label, RadioSet, TextArea

from universal_remote.tui.actions import RunScriptConfigModal


class _Host(App[None]):
    """Pushes one RunScriptConfigModal and records the value it dismisses with."""

    def __init__(self, action=None) -> None:
        super().__init__()
        self._action = action
        self.captured = False
        self.result = "<unset>"

    def on_mount(self) -> None:
        self.push_screen(RunScriptConfigModal(self._action), self._capture)

    def _capture(self, value) -> None:
        self.captured = True
        self.result = value


class TestSourceToggle:
    def test_given_the_file_source_when_selected_then_the_path_input_shows(self):
        async def scenario():
            app = _Host()
            async with app.run_test(size=(90, 40)) as pilot:
                await pilot.pause()
                await pilot.click("#source-file")
                await pilot.pause()
                assert app.screen.query_one("#run-script-path", Input).display is True
                assert (
                    app.screen.query_one("#run-script-inline", TextArea).display
                    is False
                )

        asyncio.run(scenario())

    def test_given_the_inline_source_when_selected_then_the_editor_shows(self):
        async def scenario():
            app = _Host()
            async with app.run_test(size=(90, 40)) as pilot:
                await pilot.pause()
                await pilot.click("#source-inline")
                await pilot.pause()
                assert (
                    app.screen.query_one("#run-script-inline", TextArea).display is True
                )
                assert app.screen.query_one("#run-script-path", Input).display is False

        asyncio.run(scenario())


class TestHelpline:
    def test_given_the_modal_when_open_then_a_helpline_names_remote_ip(self):
        async def scenario():
            app = _Host()
            async with app.run_test(size=(90, 40)) as pilot:
                await pilot.pause()
                helpline = app.screen.query_one("#run-script-helpline", Label)
                assert "REMOTE_IP" in str(helpline.render())

        asyncio.run(scenario())


class TestResultsToggle:
    def test_given_the_modal_when_open_then_a_results_toggle_offers_two_choices(self):
        async def scenario():
            app = _Host()
            async with app.run_test(size=(90, 40)) as pilot:
                await pilot.pause()
                results = app.screen.query_one("#run-script-results", RadioSet)
                assert len(results.children) == 2

        asyncio.run(scenario())


class TestOkAndCancel:
    def test_given_an_inline_script_when_ok_then_it_returns_the_action(self):
        async def scenario():
            app = _Host()
            async with app.run_test(size=(90, 40)) as pilot:
                await pilot.pause()
                await pilot.click("#source-inline")
                await pilot.pause()
                app.screen.query_one("#run-script-inline", TextArea).text = "echo hi"
                await pilot.click("#results-show")
                await pilot.pause()
                await pilot.click("#run-script-ok")
                await pilot.pause()
                assert app.result == {
                    "type": "run_script",
                    "source": "inline",
                    "script": "echo hi",
                    "show_results": True,
                }

        asyncio.run(scenario())

    def test_given_a_script_file_when_ok_then_it_returns_the_path_action(self):
        async def scenario():
            app = _Host()
            async with app.run_test(size=(90, 40)) as pilot:
                await pilot.pause()
                await pilot.click("#source-file")
                await pilot.pause()
                app.screen.query_one("#run-script-path", Input).value = "/opt/run.sh"
                await pilot.click("#run-script-ok")
                await pilot.pause()
                assert app.result == {
                    "type": "run_script",
                    "source": "file",
                    "script": "/opt/run.sh",
                    "show_results": False,
                }

        asyncio.run(scenario())

    def test_given_the_modal_when_cancel_then_it_returns_none(self):
        async def scenario():
            app = _Host()
            async with app.run_test(size=(90, 40)) as pilot:
                await pilot.pause()
                await pilot.click("#run-script-cancel")
                await pilot.pause()
                assert app.captured is True
                assert app.result is None

        asyncio.run(scenario())


class TestFitsShortTerminal:
    def test_given_the_inline_editor_when_shown_on_a_short_terminal_then_ok_is_reachable(
        self,
    ):
        # Inline mode is the tallest state; on a minimal 80x24 terminal the OK/Cancel
        # row must stay on-screen (the body scrolls) rather than clipping off the
        # bottom where it can't be clicked.
        async def scenario():
            app = _Host()
            async with app.run_test(size=(80, 24)) as pilot:
                await pilot.pause()
                await pilot.click("#source-inline")
                await pilot.pause()
                ok = app.screen.query_one("#run-script-ok")
                assert ok.region.y >= 0
                assert ok.region.y + ok.region.height <= app.screen.size.height

        asyncio.run(scenario())


class TestPrefill:
    def test_given_an_existing_action_when_reopened_then_its_values_prefill(self):
        action = {
            "type": "run_script",
            "source": "inline",
            "script": "reboot now",
            "show_results": True,
        }

        async def scenario():
            app = _Host(action)
            async with app.run_test(size=(90, 40)) as pilot:
                await pilot.pause()
                assert (
                    app.screen.query_one("#run-script-inline", TextArea).text
                    == "reboot now"
                )
                # Inline is preselected (index 1) and Show is preselected (index 1).
                assert (
                    app.screen.query_one("#run-script-source", RadioSet).pressed_index
                    == 1
                )
                assert (
                    app.screen.query_one("#run-script-results", RadioSet).pressed_index
                    == 1
                )

        asyncio.run(scenario())
