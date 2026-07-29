from universal_remote.adapters.adb_text import (
    build_input_text_command,
    escape_for_input_text,
)


class TestEscapeForInputText:
    def test_given_a_plain_word_when_escaped_then_it_is_unchanged(self):
        assert escape_for_input_text("hello") == "hello"

    def test_given_spaces_when_escaped_then_they_become_percent_s(self):
        assert escape_for_input_text("hello world") == "hello%sworld"

    def test_given_shell_special_characters_when_escaped_then_they_are_backslashed(
        self,
    ):
        assert escape_for_input_text("a&b|c;d") == "a\\&b\\|c\\;d"

    def test_given_a_dollar_sign_when_escaped_then_it_is_backslashed(self):
        assert escape_for_input_text("$HOME") == "\\$HOME"


class TestBuildInputTextCommand:
    def test_given_plain_text_when_built_then_a_single_input_text_call(self):
        assert build_input_text_command("hi there") == "input text hi%sthere"

    def test_given_a_literal_percent_s_when_built_then_it_is_split_across_calls(self):
        # Android's `input text` collapses "%s" to a space, so a literal "%s" must
        # be split between the % and the s across separate calls to survive.
        assert build_input_text_command("50%s") == "input text 50\\%; input text s"
