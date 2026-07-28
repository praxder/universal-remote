from universal_remote.macros.models import Macro, key_step
from universal_remote.macros.registry import (
    add,
    create,
    delete,
    get,
    list_macros,
)


class TestRegistryStorage:
    def test_given_a_macro_when_added_then_it_is_found_by_its_id(self):
        macros = {}
        macro = Macro(name="Login", steps=[key_step("HOME")])

        add(macros, macro)

        assert get(macros, macro.id) == macro

    def test_given_an_unknown_id_when_read_then_it_is_none(self):
        assert get({}, "nope") is None

    def test_given_a_macro_when_deleted_then_it_is_gone(self):
        macros = {}
        macro = Macro(name="Login")
        add(macros, macro)

        delete(macros, macro.id)

        assert get(macros, macro.id) is None

    def test_given_an_unknown_id_when_deleted_then_nothing_raises(self):
        macros = {}

        delete(macros, "nope")

        assert list_macros(macros) == []

    def test_given_several_macros_when_listed_then_they_keep_their_saved_order(self):
        macros = {}
        first, second, third = Macro(name="A"), Macro(name="B"), Macro(name="C")
        for macro in (first, second, third):
            add(macros, macro)

        assert [macro.name for macro in list_macros(macros)] == ["A", "B", "C"]

    def test_given_a_readded_id_when_listed_then_it_is_replaced_not_duplicated(self):
        # Saving a detail-modal draft re-adds the macro under the same id.
        macros = {}
        macro = Macro(name="Login")
        add(macros, macro)

        add(macros, Macro(name="Renamed", steps=[key_step("OK")], id=macro.id))

        assert [m.name for m in list_macros(macros)] == ["Renamed"]

    def test_given_a_malformed_registry_when_listed_then_it_reads_as_empty(self):
        assert list_macros({"items": "not a dict"}) == []


class TestDefaultNames:
    def test_given_three_recordings_when_created_then_they_are_numbered_in_sequence(
        self,
    ):
        macros = {}

        names = [create(macros, []).name for _ in range(3)]

        assert names == ["Macro 1", "Macro 2", "Macro 3"]

    def test_given_a_deleted_macro_when_another_is_created_then_its_name_is_not_reused(
        self,
    ):
        # The counter is monotonic, not derived from the number of saved macros.
        macros = {}
        create(macros, [])
        second = create(macros, [])
        delete(macros, second.id)

        assert create(macros, []).name == "Macro 3"

    def test_given_a_created_macro_when_created_then_it_holds_the_given_steps(self):
        macros = {}
        steps = [key_step("HOME")]

        macro = create(macros, steps)

        assert get(macros, macro.id).steps == steps

    def test_given_a_saved_counter_when_reloaded_then_numbering_continues(self):
        # The counter rides in the persisted registry, so a restart resumes it.
        macros = {}
        create(macros, [])
        create(macros, [])
        reloaded = dict(macros)

        assert create(reloaded, []).name == "Macro 3"
