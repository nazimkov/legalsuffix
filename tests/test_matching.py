import unittest

from legalsuffix import (
    match_legal_suffix,
    normalize_legal_suffix,
    parse_company_name,
    strip_legal_suffix,
)


class MatchingTests(unittest.TestCase):
    def test_match_returns_normalized_suffix_original_offsets_and_records(self) -> None:
        company_name = "Acme G.m.b.H.; "

        match = match_legal_suffix(company_name, country_code="de", language_code="DE")

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.suffix, "G.m.b.H")
        self.assertEqual(match.normalized_suffix, "gmbh")
        self.assertEqual((match.start_pos, match.end_pos), (5, 12))
        self.assertEqual(company_name[match.start_pos : match.end_pos], match.suffix)
        self.assertTrue(match.records)
        self.assertTrue(all(record.country_code == "DE" for record in match.records))

    def test_longest_matching_form_is_selected(self) -> None:
        company_name = "Acme OHG mbH"

        match = match_legal_suffix(company_name, country_code="DE", language_code="de")

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.suffix, "OHG mbH")

    def test_suffix_can_be_matched_before_descriptive_text(self) -> None:
        company_name = "Acme GmbH Holdings, Europe"

        match = match_legal_suffix(company_name, country_code="DE", language_code="de")

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.suffix, "GmbH")
        self.assertEqual(company_name[match.start_pos : match.end_pos], "GmbH")

    def test_suffix_matches_without_spaces_between_wide_characters(self) -> None:
        company_name = "アクメ有限会社"

        match = match_legal_suffix(company_name, country_code="JP", language_code="ja")

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.suffix, "有限会社")
        self.assertEqual(company_name[: match.start_pos], "アクメ")

    def test_suffix_inside_a_word_is_not_matched(self) -> None:
        company_name = "AcmeGmbH"

        match = match_legal_suffix(company_name, country_code="DE")

        self.assertIsNone(match)

    def test_strip_removes_suffix_and_adjacent_separator_punctuation(self) -> None:
        company_name = "Acme, GmbH; "

        clean_name = strip_legal_suffix(company_name, country_code="DE")

        self.assertEqual(clean_name, "Acme")

    def test_strip_preserves_text_after_suffix(self) -> None:
        company_name = "Acme GmbH Holdings"

        clean_name = strip_legal_suffix(company_name, country_code="DE")

        self.assertEqual(clean_name, "Acme Holdings")

    def test_strip_returns_original_name_when_no_suffix_matches(self) -> None:
        company_name = "Acme Holdings"

        clean_name = strip_legal_suffix(company_name)

        self.assertEqual(clean_name, company_name)

    def test_parse_returns_clean_name_and_match(self) -> None:
        company_name = "Acme GmbH Holdings"

        parsed = parse_company_name(company_name, country_code="DE")

        self.assertEqual(parsed.name, "Acme Holdings")
        self.assertIsNotNone(parsed.suffix)
        assert parsed.suffix is not None
        self.assertEqual(parsed.suffix.suffix, "GmbH")

    def test_parse_returns_original_name_when_no_suffix_matches(self) -> None:
        company_name = "Acme Holdings"

        parsed = parse_company_name(company_name)

        self.assertEqual(parsed.name, company_name)
        self.assertIsNone(parsed.suffix)

    def test_normalize_ignores_case_accents_and_punctuation(self) -> None:
        suffix = "  Société G.m.b.H.!  "

        normalized = normalize_legal_suffix(suffix)

        self.assertEqual(normalized, "societe gmbh")

    def test_matching_rejects_invalid_country_or_language_code(self) -> None:
        company_name = "Acme GmbH"

        with self.assertRaises(ValueError):
            match_legal_suffix(company_name, country_code="DEU")
        with self.assertRaises(ValueError):
            match_legal_suffix(company_name, language_code="eng")


if __name__ == "__main__":
    unittest.main()
