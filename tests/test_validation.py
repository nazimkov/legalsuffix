import unittest
from typing import get_type_hints

from legalsuffix import CountryCodeFilter, LanguageCodeFilter, list_legal_suffixes
from legalsuffix.validation import validate_country_code, validate_language_code


class ValidationTests(unittest.TestCase):
    def test_country_code_filter_is_publicly_exported_and_used_by_suffix_listing(self) -> None:
        annotation = get_type_hints(list_legal_suffixes)["country_code"]

        self.assertIs(annotation, CountryCodeFilter)

    def test_language_code_filter_is_publicly_exported_and_used_by_suffix_listing(self) -> None:
        annotation = get_type_hints(list_legal_suffixes)["language_code"]

        self.assertIs(annotation, LanguageCodeFilter)

    def test_country_code_none_is_preserved(self) -> None:
        country_code = None

        normalized = validate_country_code(country_code)

        self.assertIsNone(normalized)

    def test_country_code_is_uppercased(self) -> None:
        country_code = "de"

        normalized = validate_country_code(country_code)

        self.assertEqual(normalized, "DE")

    def test_country_code_sequence_is_uppercased(self) -> None:
        country_codes = ["de", "Fr"]

        normalized = validate_country_code(country_codes)

        self.assertEqual(normalized, ("DE", "FR"))

    def test_invalid_country_code_raises_value_error(self) -> None:
        invalid_country_codes = ("D", "DEU", "D1")

        for country_code in invalid_country_codes:
            with self.subTest(country_code=country_code):
                with self.assertRaises(ValueError):
                    validate_country_code(country_code)

    def test_language_code_none_is_preserved(self) -> None:
        language_code = None

        normalized = validate_language_code(language_code)

        self.assertIsNone(normalized)

    def test_language_code_is_lowercased(self) -> None:
        language_code = "DE"

        normalized = validate_language_code(language_code)

        self.assertEqual(normalized, "de")

    def test_language_code_sequence_is_lowercased(self) -> None:
        language_codes = ["DE", "FR"]

        normalized = validate_language_code(language_codes)

        self.assertEqual(normalized, ("de", "fr"))

    def test_invalid_language_code_raises_value_error(self) -> None:
        invalid_language_codes = ("d", "deu", "d1")

        for language_code in invalid_language_codes:
            with self.subTest(language_code=language_code):
                with self.assertRaises(ValueError):
                    validate_language_code(language_code)

    def test_code_sequence_with_invalid_value_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            validate_country_code(["DE", "USA"])


if __name__ == "__main__":
    unittest.main()
