import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SAMPLER = Path(__file__).resolve().parents[1] / "scripts" / "gleif" / "sample-test-cases.py"


class GleifSamplingTests(unittest.TestCase):
    def test_disputed_lei_is_excluded_from_samples(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.csv"
            disputed = root / "disputed.csv"
            output = root / "sample.csv"
            with source.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(
                    ["LEI", "Entity.LegalName", "Entity.LegalForm.EntityLegalFormCode", "Entity.LegalAddress.Country"]
                )
                writer.writerow(["disputed", "Disputed Company", "8888", "DK"])
                writer.writerow(["available", "Available Company", "8888", "DK"])
            with disputed.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["lei", "reason", "evidence"])
                writer.writerow(["disputed", "unresolved", "review pending"])

            subprocess.run(
                [
                    sys.executable,
                    str(SAMPLER),
                    str(source),
                    str(output),
                    "--countries",
                    "1",
                    "--codes-per-country",
                    "1",
                    "--used-cases",
                    str(root / "used"),
                    "--uncertain-cases",
                    str(root / "uncertain.csv"),
                    "--disputed-cases",
                    str(disputed),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            with output.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual([row["lei"] for row in rows], ["available"])


if __name__ == "__main__":
    unittest.main()
