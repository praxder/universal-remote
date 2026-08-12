from universal_remote.keys import Key


class TestKeyVocabulary:
    def test_given_the_key_enum_when_listing_members_then_all_remote_actions_are_present(
        self,
    ):
        expected = {
            "UP",
            "DOWN",
            "LEFT",
            "RIGHT",
            "OK",
            "BACK",
            "HOME",
            "VOL_UP",
            "VOL_DOWN",
            "MUTE",
            "MENU",
            "CH_UP",
            "CH_DOWN",
            "PLAY",
            "PAUSE",
            "PLAY_PAUSE",
            "REWIND",
            "FAST_FORWARD",
            "STOP",
        } | {f"NUM_{digit}" for digit in range(10)}

        actual = {key.name for key in Key}

        assert actual == expected
