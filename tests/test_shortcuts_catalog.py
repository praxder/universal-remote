from universal_remote.keys import Key
from universal_remote.tui.shortcuts import (
    CATALOG,
    Scope,
    conflicts,
    display_label,
    effective_key,
    is_bare_modifier,
    is_reserved,
)

_TWELVE_CLICK_ONLY = {
    "remote.vol_up",
    "remote.vol_down",
    "remote.mute",
    "remote.menu",
    "remote.ch_up",
    "remote.ch_down",
    "remote.play",
    "remote.pause",
    "remote.play_pause",
    "remote.rewind",
    "remote.fast_forward",
    "remote.stop",
}


def _by_id():
    return {action.id: action for action in CATALOG}


class TestRebindableCatalog:
    def test_given_the_catalog_when_read_then_the_four_home_actions_are_present(self):
        by_id = _by_id()

        home_ids = {a.id for a in CATALOG if a.scope is Scope.HOME}
        assert home_ids == {
            "home.manage_devices",
            "home.use_remote",
            "home.settings",
            "home.quit",
        }
        assert by_id["home.manage_devices"].default_key == "d"
        assert by_id["home.use_remote"].default_key == "r"
        assert by_id["home.settings"].default_key == "s"
        assert by_id["home.quit"].default_key == "q"
        assert all(a.editable for a in CATALOG if a.scope is Scope.HOME)

    def test_given_the_catalog_when_read_then_go_back_is_the_global_action(self):
        go_back = _by_id()["global.go_back"]

        assert go_back.scope is Scope.GLOBAL
        assert go_back.default_key == "escape"
        assert go_back.editable

    def test_given_the_catalog_when_read_then_there_are_26_rebindable_remote_actions(
        self,
    ):
        rebindable_remote = [
            a for a in CATALOG if a.scope is Scope.REMOTE and a.editable
        ]

        assert len(rebindable_remote) == 26

    def test_given_the_catalog_when_read_then_each_entry_has_id_label_scope_and_default(
        self,
    ):
        for action in CATALOG:
            assert action.id
            assert action.label
            assert isinstance(action.scope, Scope)
            assert isinstance(action.default_key, str)

    def test_given_the_twelve_click_only_keys_when_read_then_they_have_no_default(self):
        by_id = _by_id()

        for action_id in _TWELVE_CLICK_ONLY:
            assert by_id[action_id].default_key == ""

    def test_given_the_other_rebindable_actions_when_read_then_each_has_a_default(self):
        for action in CATALOG:
            if action.editable and action.id not in _TWELVE_CLICK_ONLY:
                assert action.default_key != ""


class TestReservedCatalog:
    def test_given_the_catalog_when_read_then_the_four_dpad_directions_are_reserved(
        self,
    ):
        by_id = _by_id()
        directions = [
            ("remote.up", "up", "k"),
            ("remote.down", "down", "j"),
            ("remote.left", "left", "h"),
            ("remote.right", "right", "l"),
        ]

        for action_id, arrow, alias in directions:
            action = by_id[action_id]
            assert action.editable is False
            assert action.default_key == arrow
            assert alias in action.aliases

    def test_given_the_catalog_when_read_then_the_framework_keys_are_reserved(self):
        by_id = _by_id()

        activate = by_id["framework.activate"]
        palette = by_id["framework.command_palette"]
        assert activate.editable is False
        assert activate.default_key == "enter"
        assert activate.target is None
        assert palette.editable is False
        assert palette.default_key == "ctrl+p"
        assert palette.target is None

    def test_given_the_catalog_when_read_then_the_focus_nav_keys_are_reserved(self):
        by_id = _by_id()

        focus_next = by_id["framework.focus_next"]
        focus_prev = by_id["framework.focus_prev"]
        assert focus_next.editable is False
        assert focus_next.default_key == "tab"
        assert focus_next.target is None
        assert focus_prev.editable is False
        assert focus_prev.default_key == "shift+tab"
        assert focus_prev.target is None

    def test_given_the_remote_device_actions_when_read_then_each_maps_to_a_real_key(
        self,
    ):
        for action in CATALOG:
            if action.scope is Scope.REMOTE and action.id != "remote.text":
                name = action.id.rsplit(".", 1)[-1].upper()
                assert Key[name]  # raises KeyError if not a real member

    def test_given_the_catalog_when_read_then_every_entry_id_is_unique(self):
        ids = [action.id for action in CATALOG]

        assert len(ids) == len(set(ids))


class TestEffectiveKey:
    def test_given_an_override_when_resolved_then_it_wins_over_the_default(self):
        assert effective_key("remote.vol_up", {"remote.vol_up": "v"}) == "v"

    def test_given_no_override_when_resolved_then_the_default_is_used(self):
        assert effective_key("home.quit", {}) == "q"

    def test_given_an_unbound_key_when_resolved_then_it_is_empty(self):
        assert effective_key("remote.vol_up", {}) == ""

    def test_given_a_reserved_entry_when_resolved_then_overrides_are_ignored(self):
        assert effective_key("remote.up", {"remote.up": "z"}) == "up"


class TestConflictsAndReserved:
    def test_given_a_key_another_action_uses_when_checked_then_it_conflicts(self):
        # remote.text defaults to `t`; assigning Mute the same key clashes.
        assert conflicts("remote.mute", "t", {}) is True

    def test_given_a_key_used_on_another_surface_when_checked_then_it_conflicts(self):
        # `d` is a Home default; shortcuts are globally unique, so the remote can't reuse it.
        assert conflicts("remote.vol_up", "d", {}) is True

    def test_given_go_back_assigned_a_remote_key_when_checked_then_it_conflicts(self):
        assert conflicts("global.go_back", "t", {}) is True

    def test_given_a_reserved_key_when_checked_then_is_reserved_is_true(self):
        assert is_reserved("j") is True
        assert is_reserved("enter") is True
        assert is_reserved("ctrl+p") is True
        assert is_reserved("up") is True
        assert is_reserved("tab") is True
        assert is_reserved("shift+tab") is True

    def test_given_a_free_key_when_checked_then_is_reserved_is_false(self):
        assert is_reserved("v") is False

    def test_given_a_bare_modifier_when_checked_then_it_is_unassignable(self):
        assert is_bare_modifier("shift") is True
        assert is_bare_modifier("ctrl") is True
        assert is_bare_modifier("d") is False
        assert is_bare_modifier("ctrl+p") is False

    def test_given_an_actions_own_default_when_checked_then_it_is_exempt(self):
        # OK legitimately defaults to `enter`, itself a reserved key.
        assert conflicts("remote.ok", "enter", {}) is False


class TestDisplayLabel:
    def test_given_a_modifier_combo_when_formatted_then_it_uses_a_hyphen(self):
        assert display_label("ctrl+p") == "CTRL-P"

    def test_given_named_keys_when_formatted_then_they_use_short_forms(self):
        assert display_label("space") == "SPACE"
        assert display_label("escape") == "ESC"

    def test_given_a_single_letter_when_formatted_then_it_is_uppercased(self):
        assert display_label("d") == "D"

    def test_given_an_empty_key_when_formatted_then_it_is_blank(self):
        assert display_label("") == ""
