import unittest

from legalsuffix.parser import suffix_key


class SuffixKeyTests(unittest.TestCase):
    def test_suffix_key_applies_unicode_casefolding(self) -> None:
        self.assertEqual(suffix_key("Stra\u00dfe GmbH"), "strasse gmbh")

    def test_suffix_key_joins_short_tokens_and_removes_accents(self) -> None:
        self.assertEqual(suffix_key("Soci\u00e9t\u00e9 G.m.b.H."), "societe gmbh")

    def test_suffix_key_casefolds_and_removes_punctuation(self) -> None:
        self.assertEqual(
            suffix_key("  OOO \u201c\u0420\u043e\u043c\u0430\u0448\u043a\u0430\u201d \u2014 Ltd.!  "),
            "ooo \u0440\u043e\u043c\u0430\u0448\u043a\u0430 ltd",
        )

    def test_suffix_key_preserves_word_boundaries_around_long_tokens(self) -> None:
        self.assertEqual(suffix_key("Co., Ltd."), "co ltd")

    def test_suffix_key_joins_adjacent_short_tokens(self) -> None:
        self.assertEqual(suffix_key("A / S"), "as")

    def test_suffix_key_returns_empty_for_punctuation_only_input(self) -> None:
        self.assertEqual(suffix_key("... / \u2014"), "")


if __name__ == "__main__":
    unittest.main()
