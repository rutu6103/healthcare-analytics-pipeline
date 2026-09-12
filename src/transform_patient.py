# %%
import os
import pandas as pd
import json
from datetime import datetime, timezone


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, "data", "raw", "fhir", "patient_bundle.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "processed", "fhir")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "patient.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_patient_fields(resource):
    patient_id = resource.get("id")
    gender = resource.get("gender")
    birth_date = resource.get("birthDate")

    city = None
    state = None
    country = None

    addresses = resource.get("address", [])
    if addresses:
        address = addresses[0]
        city = address.get("city")
        state = address.get("state")
        country = address.get("country")

    deceased = resource.get("deceasedBoolean", False)

    return {
        "patient_id": patient_id,
        "gender": gender,
        "birth_date": birth_date,
        "city": city,
        "state": state,
        "country": country,
        "deceased_flag": deceased
    }

def transform_patient():
    print("Input Path:", INPUT_PATH)
    print("Output Path:", OUTPUT_PATH)
    with open(INPUT_PATH, "r", encoding= "utf-8") as f:
        bundle = json.load(f)

    entries = bundle.get("entry", [])
    rows = []

    for entry in entries:
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Patient":
            rows.append(extract_patient_fields(resource))

    df = pd.DataFrame(rows)
    df.drop_duplicates(inplace=True)
    df["etl_load_time"] = datetime.now(timezone.utc)

    print("Patient shape:", df.shape)
    print(df.head())

    df.to_csv(OUTPUT_PATH, index= False)
    print(f"Saved: {OUTPUT_PATH}")

if __name__ == "__main__":
    transform_patient()



# %%
