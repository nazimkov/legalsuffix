import unittest

from legalsuffix.parser import parse_suffixes


class ParseSuffixesTests(unittest.TestCase):
    def test_parses_and_normalizes_country_suffixes(self) -> None:
        suffixes = parse_suffixes("us\t LLC. | Inc, |LTD\nde\te. V. | GmbH\n")

        self.assertEqual(suffixes.by_country["US"], frozenset({"llc", "inc", "ltd"}))
        self.assertEqual(suffixes.by_country["DE"], frozenset({"e. v", "gmbh"}))
        self.assertEqual(suffixes.all, frozenset({"llc", "inc", "ltd", "e. v", "gmbh"}))


if __name__ == "__main__":
    unittest.main()
