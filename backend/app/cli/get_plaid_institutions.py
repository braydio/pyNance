# app/cli/get_plaid_institutions.py

import csv
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))  # for local imports

from config import plaid_client
from plaid.model.institutions_get_request import InstitutionsGetRequest
from plaid.model.country_code import CountryCode


def fetch_plaid_institutions(count=500, country_codes=["US"]):
    # Convert string codes to CountryCode enums
    country_codes_enum = [CountryCode(code) for code in country_codes]
    institutions = []
    offset = 0
    while True:
        req = InstitutionsGetRequest(
            count=count, offset=offset, country_codes=country_codes_enum
        )
        resp = plaid_client.institutions_get(req)
        data = resp.to_dict()
        insts = data.get("institutions", [])
        if not insts:
            break
        institutions.extend(insts)
        offset += len(insts)
        if len(insts) < count:
            break
    return institutions


def save_as_csv(institutions, path="plaid_institutions.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["plaid_institution_id", "name", "type", "url"])
        for inst in institutions:
            writer.writerow(
                [
                    inst.get("institution_id"),
                    inst.get("name"),
                    inst.get("institution_type", ""),
                    inst.get("url", ""),
                ]
            )
    print(f"Saved {len(institutions)} institutions to {path}")


if __name__ == "__main__":
    institutions = fetch_plaid_institutions()
    save_as_csv(institutions)
