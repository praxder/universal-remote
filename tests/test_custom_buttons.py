from universal_remote.tui.custom_buttons import (
    ButtonScope,
    default_title,
    forget_device,
    resolve_action,
    resolve_scope,
    resolve_title,
    set_action,
    set_title,
)

_ACTION = {"type": "run_script", "source": "inline", "script": "echo hi"}
_OTHER_ACTION = {"type": "run_script", "source": "file", "script": "/bin/true"}


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


class TestResolveScope:
    def test_given_no_saved_titles_when_resolved_then_the_scope_is_none(self):
        assert resolve_scope({}, 1, device_id="dev-1", platform="roku") is None

    def test_given_a_device_title_when_resolved_then_the_scope_is_device(self):
        # Arrange: a title at all three scopes; the most-specific one is what shows.
        custom_buttons = {
            "device": {"dev-1": {"1": {"title": "Netflix"}}},
            "type": {"roku": {"1": {"title": "Kids"}}},
            "global": {"1": {"title": "Reboot"}},
        }

        scope = resolve_scope(custom_buttons, 1, device_id="dev-1", platform="roku")

        assert scope is ButtonScope.DEVICE

    def test_given_only_a_type_title_when_resolved_then_the_scope_is_type(self):
        custom_buttons = {"type": {"roku": {"1": {"title": "Kids"}}}}

        scope = resolve_scope(custom_buttons, 1, device_id="dev-1", platform="roku")

        assert scope is ButtonScope.TYPE

    def test_given_only_a_global_title_when_resolved_then_the_scope_is_global(self):
        custom_buttons = {"global": {"2": {"title": "Reboot"}}}

        scope = resolve_scope(custom_buttons, 2, device_id="dev-1", platform="roku")

        assert scope is ButtonScope.GLOBAL

    def test_given_a_blank_device_title_when_resolved_then_it_falls_through_to_type(
        self,
    ):
        # A blank entry is skipped exactly as resolve_title skips it, so the reported
        # scope always matches the title actually shown.
        custom_buttons = {
            "device": {"dev-1": {"1": {"title": "   "}}},
            "type": {"roku": {"1": {"title": "Kids"}}},
        }

        scope = resolve_scope(custom_buttons, 1, device_id="dev-1", platform="roku")

        assert scope is ButtonScope.TYPE


class TestForgetDevice:
    def test_given_a_device_scoped_title_when_forgotten_then_it_is_removed(self):
        # Arrange: the same button has a device title and a global title.
        custom_buttons = {
            "device": {"dev-1": {"1": {"title": "Netflix"}}},
            "global": {"1": {"title": "Reboot"}},
        }

        # Act
        forget_device(custom_buttons, "dev-1")

        # Assert: the device entry is gone; the global entry stands.
        assert "dev-1" not in custom_buttons["device"]
        assert custom_buttons["global"]["1"]["title"] == "Reboot"

    def test_given_type_and_global_titles_when_forgotten_then_they_are_kept(self):
        custom_buttons = {
            "device": {"dev-1": {"1": {"title": "Netflix"}}},
            "type": {"roku": {"1": {"title": "Kids"}}},
            "global": {"2": {"title": "Reboot"}},
        }

        forget_device(custom_buttons, "dev-1")

        assert custom_buttons["type"]["roku"]["1"]["title"] == "Kids"
        assert custom_buttons["global"]["2"]["title"] == "Reboot"

    def test_given_no_entry_for_the_device_when_forgotten_then_it_is_a_no_op(self):
        custom_buttons = {"global": {"1": {"title": "Reboot"}}}

        forget_device(custom_buttons, "dev-1")  # must not raise

        assert custom_buttons == {"global": {"1": {"title": "Reboot"}}}


class TestSetAction:
    def test_given_an_action_when_set_then_it_round_trips_from_the_same_scope(self):
        custom_buttons: dict = {}

        set_action(
            custom_buttons,
            1,
            _ACTION,
            ButtonScope.DEVICE,
            device_id="dev-1",
            platform="roku",
        )

        assert (
            resolve_action(custom_buttons, 1, device_id="dev-1", platform="roku")
            == _ACTION
        )

    def test_given_an_existing_title_when_an_action_is_set_then_the_title_is_kept(self):
        # Arrange: a title already lives in the device entry.
        custom_buttons: dict = {}
        set_title(
            custom_buttons,
            1,
            "Reboot",
            ButtonScope.DEVICE,
            device_id="dev-1",
            platform="roku",
        )

        # Act: setting an action must merge into the same entry, not replace it.
        set_action(
            custom_buttons,
            1,
            _ACTION,
            ButtonScope.DEVICE,
            device_id="dev-1",
            platform="roku",
        )

        # Assert: title and action coexist in the one entry.
        entry = custom_buttons["device"]["dev-1"]["1"]
        assert entry["title"] == "Reboot"
        assert entry["action"] == _ACTION

    def test_given_an_existing_action_when_a_title_is_set_then_the_action_is_kept(self):
        # The symmetric guarantee: saving a title never drops an assigned action.
        custom_buttons: dict = {}
        set_action(
            custom_buttons,
            1,
            _ACTION,
            ButtonScope.DEVICE,
            device_id="dev-1",
            platform="roku",
        )

        set_title(
            custom_buttons,
            1,
            "Reboot",
            ButtonScope.DEVICE,
            device_id="dev-1",
            platform="roku",
        )

        entry = custom_buttons["device"]["dev-1"]["1"]
        assert entry["action"] == _ACTION
        assert entry["title"] == "Reboot"

    def test_given_a_none_action_when_set_then_the_action_key_is_cleared(self):
        custom_buttons: dict = {}
        set_action(
            custom_buttons,
            1,
            _ACTION,
            ButtonScope.DEVICE,
            device_id="dev-1",
            platform="roku",
        )

        set_action(
            custom_buttons,
            1,
            None,
            ButtonScope.DEVICE,
            device_id="dev-1",
            platform="roku",
        )

        assert "action" not in custom_buttons["device"]["dev-1"]["1"]


class TestResolveAction:
    def test_given_no_saved_action_when_resolved_then_it_is_none(self):
        assert resolve_action({}, 1, device_id="dev-1", platform="roku") is None

    def test_given_a_title_only_entry_when_resolved_then_there_is_no_action(self):
        # Back-compat: a pre-actions entry holds only a title and loads inert.
        custom_buttons = {"device": {"dev-1": {"1": {"title": "Netflix"}}}}

        assert (
            resolve_action(custom_buttons, 1, device_id="dev-1", platform="roku")
            is None
        )

    def test_given_actions_at_two_scopes_when_resolved_then_the_device_action_wins(
        self,
    ):
        custom_buttons = {
            "device": {"dev-1": {"1": {"title": "A", "action": _ACTION}}},
            "type": {"roku": {"1": {"title": "B", "action": _OTHER_ACTION}}},
        }

        assert (
            resolve_action(custom_buttons, 1, device_id="dev-1", platform="roku")
            == _ACTION
        )

    def test_given_a_device_entry_when_resolved_then_title_and_action_share_its_scope(
        self,
    ):
        # The entry resolves as a unit: the device entry carries both a title and an
        # action, while only a title is saved globally. Both must come from the
        # device entry — the global title is never mixed in.
        custom_buttons = {
            "device": {"dev-1": {"1": {"title": "Device", "action": _ACTION}}},
            "global": {"1": {"title": "Global"}},
        }

        assert (
            resolve_title(custom_buttons, 1, device_id="dev-1", platform="roku")
            == "Device"
        )
        assert (
            resolve_action(custom_buttons, 1, device_id="dev-1", platform="roku")
            == _ACTION
        )

    def test_given_an_action_only_device_entry_when_resolved_then_it_wins_as_a_unit(
        self,
    ):
        # The discriminating case: the device entry has an action but no title, while
        # the device type has only a title. Resolving as a unit, the most-specific
        # meaningful entry (device) wins whole — so its action runs and its (absent)
        # title falls back to the default, rather than splitting the type's title
        # onto the device's action.
        custom_buttons = {
            "device": {"dev-1": {"1": {"action": _ACTION}}},
            "type": {"roku": {"1": {"title": "Kids"}}},
        }

        assert (
            resolve_action(custom_buttons, 1, device_id="dev-1", platform="roku")
            == _ACTION
        )
        assert (
            resolve_title(custom_buttons, 1, device_id="dev-1", platform="roku")
            == "Custom 1"
        )
        assert (
            resolve_scope(custom_buttons, 1, device_id="dev-1", platform="roku")
            is ButtonScope.DEVICE
        )
