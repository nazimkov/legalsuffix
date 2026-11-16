import os

from dotenv import load_dotenv
from jev import CompanyState, JevClient, JevVerifier

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("JEV_MODEL")

if not model:
    raise ValueError("Missing JEV_MODEL")

if not api_key:
    raise ValueError("Missing OPENROUTER_API_KEY")

client = JevClient(api_key=api_key, model=model)
verifier = JevVerifier(client=client)

pos_cases = [
    CompanyState(
        id=1,
        original_company_name="SORIA NATURAL SOCIEDAD ANONIMA",
        extracted_company_name="SORIA NATURAL",
        extracted_suffix="SOCIEDAD ANONIMA",
    )
]


neg_cases = [
    CompanyState(
        id=2,
        original_company_name="Alltime Montage GmbH & Co KG",
        extracted_company_name="Alltime Montage GmbH & Co KG",
        extracted_suffix="KG",
    )
]

states = pos_cases + neg_cases

verification_result = verifier.validate(states=states)

for id, r in verification_result.items():
    print(f"{id}: {r.overall_verdict.correct}")
    for dn, d in r.decisions.items():
        print(f"\t {dn}:{d.choice}, confidence = {d.confidence}")
