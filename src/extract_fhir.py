import json
import os
from pathlib import Path

import requests

BASE_URL = "https://r4.smarthealthit.org"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "fhir"
RESOURCES = ("Patient", "Encounter", "Condition")
PAGE_SIZE = int(os.getenv("FHIR_PAGE_SIZE", "200"))

RAW_DIR.mkdir(parents=True, exist_ok=True)

def fetch_all_pages(resource_type, page_size=PAGE_SIZE):
    url = f"{BASE_URL}/{resource_type}"
    params = {'_count': page_size}

    all_entries = []
    page_num = 1

    while url:
        response = requests.get(url, params=params, timeout=60)
        print(f"{resource_type} | Page {page_num} | Status: {response.status_code}")
        response.raise_for_status()

        bundle = response.json()

        entries = bundle.get('entry', [])
        all_entries.extend(entries)
        print(f"{resource_type} | Page {page_num} | Entries Fetched: {len(entries)}")

        params = None

        next_url = None
        for link in bundle.get("link", []):
            if link.get("relation") == "next":
                next_url = link.get("url")
                break
        
        url = next_url
        page_num += 1

        if not entries:
            break

    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total_entries_collected": len(all_entries),
        "entry": all_entries
    }


def save_bundle(resource_type, bundle_json):
    path = RAW_DIR / f"{resource_type.lower()}_bundle.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(bundle_json, f, indent=2)
    print(f"Saved: {path}")


def extract_all():
    for resource in RESOURCES:
        bundle = fetch_all_pages(resource, page_size=PAGE_SIZE)
        print(f"{resource} | Total entries collected: {bundle['total_entries_collected']}")
        save_bundle(resource, bundle)


if __name__ == "__main__":
    extract_all()
