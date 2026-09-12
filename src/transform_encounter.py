# %%
import os
import pandas as pd
import json
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, "data", "raw", "fhir", "encounter_bundle.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "processed", "fhir")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "encounter.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_reference_id(reference_value):
    if not reference_value:
        return None
    if "/" in reference_value:
        return reference_value.split("/")[-1]
    return reference_value

def extract_encounter_fields(resource):
    encounter_id = resource.get("id")
    status = resource.get("status")

    encounter_class = None
    if resource.get("class"):
        encounter_class = resource["class"].get("code")

    subject_ref = None
    if resource.get("subject"):
        subject_ref = get_reference_id(resource['subject'].get('reference'))

    start_date = None
    end_date = None

    if resource.get('period'):
        start_date = resource['period'].get('start')
        end_date = resource['period'].get('end')

    service_provider = None
    if resource.get('serviceProvider'):
        service_provider = get_reference_id(resource['serviceProvider'].get('reference'))

    return {
        'encounter_id': encounter_id,
        'patient_id': subject_ref,
        'status': status,
        'encounter_class': encounter_class,
        'start_date': start_date,
        'end_date': end_date,
        "service_provider_id": service_provider 
    }

def transform_encounter():
    print('Input Path:', INPUT_PATH)
    print('Output Path:', OUTPUT_PATH)

    with open(INPUT_PATH, "r", encoding= "utf-8") as f:
        bundle = json.load(f)

    entries = bundle.get("entry", [])
    rows = []

    for entry in entries:
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Encounter":
            rows.append(extract_encounter_fields(resource))

    df = pd.DataFrame(rows)
    df.drop_duplicates(inplace=True)

    df['start_date'] = pd.to_datetime(df['start_date'], errors= "coerce", utc=True)
    df['end_date'] = pd.to_datetime(df['end_date'], errors= "coerce", utc=True)

    df['start_date_only'] = df['start_date'].dt.date
    df['end_date_only'] = df['end_date'].dt.date
    df["etl_load_time"] = datetime.now(timezone.utc)

    print("Encounter shape:", df.shape)
    print("Null start_date:", df['start_date'].isna().sum())
    print("Null end_date:", df['end_date'].isna().sum())
    print(df.head())

    df.to_csv(OUTPUT_PATH, index= False)
    print(f"Saved: {OUTPUT_PATH}")

if __name__ == "__main__":
    transform_encounter()
