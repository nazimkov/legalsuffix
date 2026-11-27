import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

IMPORTER = Path(__file__).resolve().parents[1] / "scripts" / "gleif" / "import-elf.py"
FIELDS = [
    "ELF Code",
    "Country Code (ISO 3166-1)",
    "Language Code (ISO 639-1)",
    "Abbreviations Local language",
    "Date created YYYY-MM-DD (ISO 8601)",
    "ELF Status ACTV/INAC",
    "Modification",
    "Modification date YYYY-MM-DD (ISO 8601)",
    "Reason",
]


class ImportElfTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "source.csv"
        self.extra = self.root / "extra.csv"
        self.output = self.root / "suffixes.csv"

    def _write_csv(self, path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def _import(self, source: list[dict[str, str]], extra: list[dict[str, str]]) -> list[dict[str, str]]:
        self._write_csv(self.source, FIELDS, source)
        self._write_csv(self.extra, [*FIELDS, "Merge Type"], extra)
        subprocess.run(
            [sys.executable, str(IMPORTER), str(self.source), str(self.output), "--extra", str(self.extra)],
            check=True,
            capture_output=True,
            text=True,
        )
        with self.output.open(encoding="utf-8", newline="") as stream:
            return list(csv.DictReader(stream))

    def test_reserved_codes_from_official_source_are_excluded(self) -> None:
        source = [{"ELF Code": code} for code in ("ABCD", "8888", "9999")]

        rows = self._import(source, [])

        self.assertEqual([row["ELF Code"] for row in rows], ["ABCD"])

    def test_new_reserved_code_records_from_extras_are_retained(self) -> None:
        extra = [{"ELF Code": code, "Merge Type": "NEW"} for code in ("8888", "9999")]

        rows = self._import([], extra)

        self.assertEqual([row["ELF Code"] for row in rows], ["8888", "9999"])

    def test_extra_suffix_is_merged_into_matching_source_record(self) -> None:
        key = {"ELF Code": "ABCD", "Country Code (ISO 3166-1)": "DK", "Language Code (ISO 639-1)": "da"}
        source = [{**key, "Abbreviations Local language": "A"}]
        extra = [{**key, "Abbreviations Local language": "B", "Merge Type": "EXTRA_SUFFIX"}]

        rows = self._import(source, extra)

        self.assertEqual(rows[0]["Abbreviations Local language"], "A;B")


if __name__ == "__main__":
    unittest.main()
