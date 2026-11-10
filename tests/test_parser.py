import unittest

from legalsuffix.parser import norm, parse_suffixes, suffix_key


class ParseSuffixesTests(unittest.TestCase):
    def test_parses_and_normalizes_country_suffixes(self) -> None:
        suffixes = parse_suffixes("us\t LLC. | Inc, |LTD\nde\te. V. | GmbH\n")

        actual = (suffixes.by_country["US"], suffixes.by_country["DE"], suffixes.all)

        self.assertEqual(
            actual,
            (
                frozenset({"llc", "inc", "ltd"}),
                frozenset({"e. v", "gmbh"}),
                frozenset({"llc", "inc", "ltd", "e. v", "gmbh"}),
            ),
        )

    def test_ignores_blank_lines_and_comments(self) -> None:
        text = "\n# comment\nUS\tLLC\n  \nDE\tGmbH\n"

        suffixes = parse_suffixes(text)

        self.assertEqual(suffixes.by_country, {"US": frozenset({"llc"}), "DE": frozenset({"gmbh"})})
        self.assertEqual(suffixes.all, frozenset({"llc", "gmbh"}))

    def test_line_without_tab_raises_value_error_with_line_number(self) -> None:
        text = "US\tLLC\nnot-a-row\n"

        with self.assertRaisesRegex(ValueError, r"line 2: expected"):
            parse_suffixes(text)

    def test_invalid_country_code_raises_value_error(self) -> None:
        text = "USA\tLLC"

        with self.assertRaisesRegex(ValueError, r"line 1: bad ISO code 'USA'"):
            parse_suffixes(text)

    def test_empty_suffix_list_raises_value_error(self) -> None:
        text = "US\t | . | , "

        with self.assertRaisesRegex(ValueError, r"line 1: no suffixes for US"):
            parse_suffixes(text)

    def test_norm_trims_whitespace_and_trailing_punctuation(self) -> None:
        suffix = "  Inc.,  "

        normalized = norm(suffix)

        self.assertEqual(normalized, "inc")

    def test_suffix_key_joins_short_tokens_and_removes_accents(self) -> None:
        suffix = "Société G.m.b.H."

        normalized = suffix_key(suffix)

        self.assertEqual(normalized, "societe gmbh")


if __name__ == "__main__":
    unittest.main()
