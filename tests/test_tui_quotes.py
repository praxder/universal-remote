from universal_remote.tui.quotes import Quote, load_quotes, random_quote


class TestLoadQuotes:
    def test_given_a_wellformed_line_when_loaded_then_it_becomes_a_quote(self):
        text = "May the Force be with you.|Darth Vader|Star Wars"

        quotes = load_quotes(text)

        assert quotes == [
            Quote("May the Force be with you.", "Darth Vader", "Star Wars")
        ]

    def test_given_blank_and_malformed_lines_when_loaded_then_they_are_skipped(self):
        text = "\n".join(
            [
                "Here's Johnny!|Jack Torrance|The Shining",
                "",
                "   ",
                "missing fields|only two",
                "too|many|fields|here",
                "|empty|fields",
                "I'll be back.|The Terminator|The Terminator",
            ]
        )

        quotes = load_quotes(text)

        assert quotes == [
            Quote("Here's Johnny!", "Jack Torrance", "The Shining"),
            Quote("I'll be back.", "The Terminator", "The Terminator"),
        ]


class TestRandomQuote:
    def test_given_a_list_of_quotes_when_choosing_then_the_result_is_from_the_list(
        self,
    ):
        options = [
            Quote("a", "b", "c"),
            Quote("d", "e", "f"),
        ]

        chosen = random_quote(options)

        assert chosen in options

    def test_given_no_quotes_when_choosing_then_the_result_is_none(self):
        assert random_quote([]) is None
