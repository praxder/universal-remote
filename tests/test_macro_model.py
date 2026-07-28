from universal_remote.macros.models import (
    Macro,
    action_step,
    delete_step,
    insert_after,
    key_step,
    move_down,
    move_up,
    pause_step,
    step_description,
    text_step,
)


class TestStepConstructors:
    def test_given_a_key_name_when_built_then_it_is_a_key_step(self):
        assert key_step("HOME") == {"type": "key", "key": "HOME"}

    def test_given_text_when_built_then_it_is_a_text_step(self):
        assert text_step("hello") == {"type": "text", "text": "hello"}

    def test_given_a_duration_when_built_then_it_is_a_pause_step(self):
        assert pause_step(500) == {"type": "pause", "ms": 500}

    def test_given_an_action_when_captured_then_the_step_holds_a_copy_of_it(self):
        # A captured action is a frozen snapshot: reconfiguring the button afterwards
        # must not reach into the recorded step.
        action = {"type": "run_script", "script": "echo hi"}

        step = action_step(action)
        action["script"] = "echo changed"

        assert step["action"] == {"type": "run_script", "script": "echo hi"}


class TestStepDescription:
    def test_given_a_key_step_when_described_then_it_names_the_key(self):
        assert step_description(key_step("HOME")) == "Key: HOME"

    def test_given_a_pause_step_when_described_then_it_names_the_duration(self):
        assert step_description(pause_step(500)) == "Pause: 500ms"

    def test_given_a_text_step_when_described_then_it_quotes_the_text(self):
        assert step_description(text_step("hello")) == 'Text: "hello"'

    def test_given_an_action_step_when_described_then_it_names_the_action_type(self):
        step = action_step({"type": "run_script", "script": "echo hi"})

        assert step_description(step) == "Run Custom Script"

    def test_given_an_unknown_action_type_when_described_then_it_still_reads(self):
        # Hand-edited preferences can hold a type the catalog does not know; the step
        # must still describe itself rather than rendering blank.
        step = action_step({"type": "mystery"})

        assert step_description(step) == "Action: mystery"

    def test_given_an_unknown_step_type_when_described_then_it_still_reads(self):
        assert step_description({"type": "nonsense"}) == "Unknown step: nonsense"


class TestMacroPersistence:
    def test_given_a_macro_when_built_then_it_has_a_stable_id(self):
        first = Macro(name="Login")
        second = Macro(name="Login")

        assert first.id and first.id != second.id

    def test_given_a_macro_when_serialized_then_the_id_is_not_in_the_body(self):
        # The registry keys each macro by its id, so the stored body holds only the
        # name and steps.
        macro = Macro(name="Login", steps=[key_step("HOME")])

        assert macro.to_dict() == {
            "name": "Login",
            "steps": [{"type": "key", "key": "HOME"}],
        }

    def test_given_a_stored_body_when_read_then_it_round_trips_with_its_id(self):
        macro = Macro(name="Login", steps=[pause_step(250)])

        restored = Macro.from_dict(macro.id, macro.to_dict())

        assert restored == macro

    def test_given_a_body_missing_its_fields_when_read_then_it_loads_empty(self):
        # Fault tolerance mirrors the rest of the preferences file: a malformed body
        # loads as an empty macro rather than raising.
        restored = Macro.from_dict("abc", {"steps": "not a list"})

        assert restored == Macro(name="", steps=[], id="abc")


class TestDraftStepOperations:
    def test_given_a_middle_step_when_moved_up_then_it_swaps_with_the_one_above(self):
        steps = [key_step("A"), key_step("B"), key_step("C")]

        index = move_up(steps, 1)

        assert [step["key"] for step in steps] == ["B", "A", "C"]
        assert index == 0

    def test_given_the_first_step_when_moved_up_then_nothing_changes(self):
        steps = [key_step("A"), key_step("B")]

        index = move_up(steps, 0)

        assert [step["key"] for step in steps] == ["A", "B"]
        assert index == 0

    def test_given_a_middle_step_when_moved_down_then_it_swaps_with_the_one_below(self):
        steps = [key_step("A"), key_step("B"), key_step("C")]

        index = move_down(steps, 1)

        assert [step["key"] for step in steps] == ["A", "C", "B"]
        assert index == 2

    def test_given_the_last_step_when_moved_down_then_nothing_changes(self):
        steps = [key_step("A"), key_step("B")]

        index = move_down(steps, 1)

        assert [step["key"] for step in steps] == ["A", "B"]
        assert index == 1

    def test_given_a_step_when_deleted_then_it_is_removed(self):
        steps = [key_step("A"), key_step("B"), key_step("C")]

        delete_step(steps, 1)

        assert [step["key"] for step in steps] == ["A", "C"]

    def test_given_an_index_when_inserting_after_it_then_the_step_follows_it(self):
        steps = [key_step("A"), key_step("C")]

        index = insert_after(steps, 0, key_step("B"))

        assert [step["key"] for step in steps] == ["A", "B", "C"]
        assert index == 1

    def test_given_no_selection_when_inserting_then_the_step_is_appended(self):
        # An empty list has no selected step; -1 stands in for "nothing selected", so
        # the step lands at the front of an empty draft.
        steps = []

        index = insert_after(steps, -1, key_step("A"))

        assert [step["key"] for step in steps] == ["A"]
        assert index == 0
