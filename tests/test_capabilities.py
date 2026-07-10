from universal_remote.capabilities import Capabilities
from universal_remote.keys import Key


class TestCapabilities:
    def test_given_a_declared_key_when_asked_if_supported_then_true(self):
        caps = Capabilities(keys=frozenset({Key.UP}))

        assert caps.supports(Key.UP) is True

    def test_given_an_undeclared_key_when_asked_if_supported_then_false(self):
        caps = Capabilities(keys=frozenset({Key.UP}))

        assert caps.supports(Key.DOWN) is False

    def test_given_a_text_flag_when_read_then_it_is_exposed(self):
        caps = Capabilities(keys=frozenset(), text=True)

        assert caps.text is True

    def test_given_no_flags_when_constructed_then_text_defaults_false(self):
        caps = Capabilities(keys=frozenset())

        assert caps.text is False
