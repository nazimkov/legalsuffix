import unittest

from legalsuffix.models import LegalSuffix, SuffixTrie


def _record() -> LegalSuffix:
    return LegalSuffix(
        elf_code="TEST",
        country_of_formation="Testland",
        country_code="DE",
        jurisdiction_of_formation=None,
        country_subdivision_code=None,
        entity_legal_form_name_local_name="Limited",
        language="English",
        language_code="en",
        entity_legal_form_name_transliterated_name="Limited",
        abbreviations_local_language=(),
        abbreviations_transliterated=(),
    )


class SuffixTrieTests(unittest.TestCase):
    def test_forward_trie_finds_complete_key(self) -> None:
        records = [_record()]
        trie = SuffixTrie()
        trie.add("limited", records)

        actual = trie.find("limited")

        self.assertIs(actual, records)
        self.assertIsNone(trie.find("limit"))

    def test_reversed_trie_finds_key_from_its_end(self) -> None:
        records = [_record()]
        trie = SuffixTrie(reversed_keys=True)
        trie.add("limited", records)

        actual = trie.find("limited")

        self.assertIs(actual, records)
        self.assertIsNone(trie.find("limitedx"))


if __name__ == "__main__":
    unittest.main()
