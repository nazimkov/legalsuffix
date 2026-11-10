import unittest

from legalsuffix import parse_company_name, strip_legal_suffix

from .case_loader import CompanyNameTestCase, load_test_cases


class MatchingDataTests(unittest.TestCase):
    cases = load_test_cases(CompanyNameTestCase)

    def test_strips_expected_suffix_for_each_company_name_case(self) -> None:
        for case in self.cases:
            with self.subTest(elf_code=case.elf_code, entity_name=case.entity_name):
                actual = strip_legal_suffix(case.entity_name, country_code=case.country_code)

                self.assertEqual(actual, case.clean_entity)

    def test_parses_expected_name_and_suffix_for_each_company_name_case(self) -> None:
        for case in self.cases:
            with self.subTest(elf_code=case.elf_code, entity_name=case.entity_name):
                parsed = parse_company_name(case.entity_name, country_code=case.country_code)

                self.assertEqual(parsed.name, case.clean_entity)
                self.assertEqual(parsed.suffix.suffix if parsed.suffix else None, case.suffix)


if __name__ == "__main__":
    unittest.main()
