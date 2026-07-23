from universal_remote.tui.custom_buttons import (
    ButtonScope,
    default_title,
    resolve_title,
    set_title,
)


class TestDefaultTitle:
    def test_given_an_index_when_defaulted_then_it_reads_custom_n(self):
        assert default_title(4) == "Custom 4"


class TestResolveTitle:
    def test_given_no_saved_titles_when_resolved_then_the_default_is_used(self):
        assert resolve_title({}, 3, device_id="dev-1", platform="roku") == "Custom 3"

    def test_given_a_device_title_when_resolved_then_it_wins_over_type_and_global(self):
        # Arrange: the same button has a title at all three scopes.
        custom_buttons = {
            "device": {"dev-1": {"1": {"title": "Netflix"}}},
            "type": {"roku": {"1": {"title": "Kids"}}},
            "global": {"1": {"title": "Reboot"}},
        }

        # Act / Assert: the most-specific (device) title wins.
        resolved = resolve_title(custom_buttons, 1, device_id="dev-1", platform="roku")
        assert resolved == "Netflix"

    def test_given_no_device_title_when_resolved_then_it_falls_through_to_type(self):
        custom_buttons = {"type": {"roku": {"1": {"title": "Kids"}}}}

        resolved = resolve_title(custom_buttons, 1, device_id="dev-1", platform="roku")

        assert resolved == "Kids"

    def test_given_no_device_or_type_title_when_resolved_then_it_falls_through_to_global(
        self,
    ):
        custom_buttons = {"global": {"2": {"title": "Reboot"}}}

        resolved = resolve_title(custom_buttons, 2, device_id="dev-1", platform="roku")

        assert resolved == "Reboot"

    def test_given_a_blank_device_title_when_resolved_then_it_falls_through(self):
        # A blank entry at one scope is treated as absent and yields to the next.
        custom_buttons = {
            "device": {"dev-1": {"1": {"title": "   "}}},
            "type": {"roku": {"1": {"title": "Kids"}}},
        }

        resolved = resolve_title(custom_buttons, 1, device_id="dev-1", platform="roku")

        assert resolved == "Kids"


class TestSetTitle:
    def test_given_this_device_scope_when_set_then_only_that_device_resolves_it(self):
        # Arrange
        custom_buttons: dict = {}

        # Act
        set_title(
            custom_buttons,
            1,
            "Netflix",
            ButtonScope.DEVICE,
            device_id="dev-1",
            platform="roku",
        )

        # Assert: the active device sees it; a different device does not.
        assert (
            resolve_title(custom_buttons, 1, device_id="dev-1", platform="roku")
            == "Netflix"
        )
        assert (
            resolve_title(custom_buttons, 1, device_id="dev-2", platform="roku")
            == "Custom 1"
        )

    def test_given_type_scope_when_set_then_any_device_of_that_type_resolves_it(self):
        custom_buttons: dict = {}

        set_title(
            custom_buttons,
            1,
            "Kids",
            ButtonScope.TYPE,
            device_id="dev-1",
            platform="roku",
        )

        assert (
            resolve_title(custom_buttons, 1, device_id="dev-2", platform="roku")
            == "Kids"
        )

    def test_given_global_scope_when_set_then_every_device_resolves_it(self):
        custom_buttons: dict = {}

        set_title(
            custom_buttons,
            1,
            "Reboot",
            ButtonScope.GLOBAL,
            device_id="dev-1",
            platform="roku",
        )

        assert (
            resolve_title(custom_buttons, 1, device_id="other", platform="samsung")
            == "Reboot"
        )
