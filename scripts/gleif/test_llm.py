#!/usr/bin/env python3
"""Smoke test the Azure OpenAI company name extractor."""

import logging

from dotenv import load_dotenv
from llm import AzureOpenAIExtractor

load_dotenv()

COMPANY_NAMES = [
    "SORIA NATURAL SOCIEDAD ANONIMA",
    "Alltime Montage GmbH & Co KG",
]


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


with AzureOpenAIExtractor.from_environment() as extractor:
    result = extractor.extract_batch(COMPANY_NAMES)

for cmp in result.companies:
    print(f"{cmp.id}: {cmp.company_name} | legal form: {cmp.legal_form}")
print(f"Usage: {result.usage}")
