import csv
import tempfile
import unittest
from pathlib import Path
from typing import Literal
from unittest.mock import patch

from legalsuffix import get_suffixes, loader

CSVField = Literal[
    "ELF Code",
    "Country of formation",
    "Country Code (ISO 3166-1)",
    "Jurisdiction of formation",
    "Country sub-division code (ISO 3166-2)",
    "Entity Legal Form name Local name",
    "Language",
    "Language Code (ISO 639-1)",
    "Entity Legal Form name Transliterated name (per ISO 01-140-10)",
    "Abbreviations Local language",
    "Abbreviations transliterated",
]

CSV_FIELDS: tuple[CSVField, ...] = (
    "ELF Code",
    "Country of formation",
    "Country Code (ISO 3166-1)",
    "Jurisdiction of formation",
    "Country sub-division code (ISO 3166-2)",
    "Entity Legal Form name Local name",
    "Language",
    "Language Code (ISO 639-1)",
    "Entity Legal Form name Transliterated name (per ISO 01-140-10)",
    "Abbreviations Local language",
    "Abbreviations transliterated",
)


def _row(country_code: str, language_code: str, abbreviation: str) -> dict[CSVField, str]:
    return {
        "ELF Code": "TEST",
        "Country of formation": "Testland",
        "Country Code (ISO 3166-1)": country_code,
        "Jurisdiction of formation": "",
        "Country sub-division code (ISO 3166-2)": "",
        "Entity Legal Form name Local name": "Gesellschaft mit beschränkter Haftung",
        "Language": "German",
        "Language Code (ISO 639-1)": language_code,
        "Entity Legal Form name Transliterated name (per ISO 01-140-10)": "Gesellschaft mit beschrankter Haftung",
        "Abbreviations Local language": abbreviation,
        "Abbreviations transliterated": "GmbH",
    }


class LoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        loader._load_suffixes.cache_clear()

    def tearDown(self) -> None:
        loader._load_suffixes.cache_clear()

    def test_get_suffixes_filters_country_and_language_and_returns_tuple(self) -> None:
        records = get_suffixes(country_code="de", language_code="DE")

        self.assertIsInstance(records, tuple)
        self.assertTrue(records)
        self.assertTrue(all(record.country_code == "DE" for record in records))
        self.assertTrue(all(record.language_code == "de" for record in records))

    def test_load_suffixes_normalizes_filter_codes_and_indexes_forms(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_path = Path(temporary_directory) / "suffixes.csv"
            with data_path.open("w", encoding="utf-8", newline="") as data_file:
                writer = csv.DictWriter(data_file, fieldnames=CSV_FIELDS)
                writer.writeheader()
                writer.writerow(_row("DE", "de", "GmbH;GmbH"))
                writer.writerow(_row("DE", "fr", "SARL"))
                writer.writerow(_row("FR", "de", "UG"))
                writer.writerow(_row("FR", "fr", "SARL"))

            with patch.object(loader, "DATA_FILE_PATH", data_path):
                country_suffixes = loader.load_suffixes(country_code="de")
                language_suffixes = loader.load_suffixes(language_code="DE")
                suffixes = loader.load_suffixes(country_code="de", language_code="DE")

            self.assertEqual(len(country_suffixes.records), 2)
            self.assertEqual(len(language_suffixes.records), 2)
            self.assertEqual(len(suffixes.records), 1)
            self.assertEqual(suffixes.records[0].abbreviations_local_language, ["GmbH", "GmbH"])
            self.assertIn("gmbh", suffixes.all)
            self.assertIn("gesellschaft mit beschrankter haftung", suffixes.all)
            self.assertEqual(len(suffixes.by_normalized_suffix["gmbh"]), 1)

    def test_load_suffixes_rejects_row_without_country_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_path = Path(temporary_directory) / "suffixes.csv"
            row = _row("", "de", "GmbH")
            with data_path.open("w", encoding="utf-8", newline="") as data_file:
                writer = csv.DictWriter(data_file, fieldnames=CSV_FIELDS)
                writer.writeheader()
                writer.writerow(row)

            with patch.object(loader, "DATA_FILE_PATH", data_path):
                with self.assertRaisesRegex(ValueError, "missing Country Code"):
                    loader.load_suffixes()

    def test_get_suffixes_rejects_invalid_codes(self) -> None:
        with self.assertRaises(ValueError):
            get_suffixes(country_code="USA")
        with self.assertRaises(ValueError):
            get_suffixes(language_code="eng")


if __name__ == "__main__":
    unittest.main()
