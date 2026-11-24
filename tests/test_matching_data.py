import unittest

from legalsuffix import parse_company_name, strip_legal_suffix

from .case_loader import TEST_CASES_PATH, CompanyNameTestCase, load_test_cases


class MatchingDataTests(unittest.TestCase):
    pass


def _strip_test(path):
    def test(self) -> None:
        for case in load_test_cases(CompanyNameTestCase, path):
            with self.subTest(
                lei=case.lei,
                entity_name=case.entity_name,
                suffix=case.suffix,
                elf_code=case.elf_code,
            ):
                actual = strip_legal_suffix(
                    case.entity_name,
                    country_code=case.country_code,
                    language_code=case.language_code,
                )

                self.assertEqual(actual, case.clean_entity)

    return test


def _parse_test(path):
    def test(self) -> None:
        for case in load_test_cases(CompanyNameTestCase, path):
            with self.subTest(
                lei=case.lei,
                entity_name=case.entity_name,
                suffix=case.suffix,
                elf_code=case.elf_code,
            ):
                parsed = parse_company_name(
                    case.entity_name,
                    country_code=case.country_code,
                    language_code=case.language_code,
                )

                self.assertEqual(parsed.name, case.clean_entity)
                self.assertEqual(parsed.suffix.suffix if parsed.suffix else None, case.suffix)

    return test


for test_case_path in sorted(TEST_CASES_PATH.glob("*.csv")):
    setattr(MatchingDataTests, f"test_strips_expected_name_for_{test_case_path.stem}", _strip_test(test_case_path))
    setattr(MatchingDataTests, f"test_parses_expected_name_for_{test_case_path.stem}", _parse_test(test_case_path))


if __name__ == "__main__":
    unittest.main()
