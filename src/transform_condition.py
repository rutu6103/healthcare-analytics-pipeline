# %%
import os
import pandas as pd
import json
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, "data", "raw", "fhir", "condition_bundle.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "processed", "fhir")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "condition.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_reference_id(reference_value):
    if not reference_value:
        return None
    if "/" in reference_value:
        return reference_value.split("/")[-1]
    return reference_value

def extract_condition_fields(resource):
    condition_id = resource.get("id")

    patient_id = None
    if resource.get("subject"):
        patient_id = get_reference_id(resource['subject'].get('reference'))

    encounter_id = None
    if resource.get("encounter"):
        encounter_id = get_reference_id(resource['encounter'].get('reference'))

    clinical_status = None
    if resource.get('clinicalStatus', {}).get('coding'):
        clinical_status = resource['clinicalStatus']['coding'][0].get('code')

    verification_status = None
    if resource.get('verificationStatus', {}).get('coding'):
        verification_status = resource['verificationStatus']['coding'][0].get('code')

    condition_code = None
    condition_name = None

    if resource.get('code', {}).get('coding'):
        condition_code = resource['code']['coding'][0].get('code')
        condition_name = resource['code'].get('text')

    onset_date = resource.get('onsetDateTime')

    return {
        'condition_id': condition_id,
        'patient_id': patient_id,
        'encounter_id': encounter_id,
        'clinical_status': clinical_status,
        'verification_status': verification_status,
        'condition_code': condition_code,
        'condition_name': condition_name,
        "onset_date": onset_date
    }

def transform_condition():
    print('Input Path:', INPUT_PATH)
    print('Output Path:', OUTPUT_PATH)

    with open(INPUT_PATH, "r", encoding= "utf-8") as f:
        bundle = json.load(f)

    entries = bundle.get("entry", [])
    rows = []

    for entry in entries:
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Condition":
            rows.append(extract_condition_fields(resource))

    df = pd.DataFrame(rows)
    df.drop_duplicates(inplace=True)

    df['onset_date'] = pd.to_datetime(df['onset_date'], errors= "coerce", utc=True)

    df['onset_date_only'] = df['onset_date'].dt.date
    df["etl_load_time"] = datetime.now(timezone.utc)

    print("Condition shape:", df.shape)
    print("Null onset_date:", df['onset_date'].isna().sum())
    print(df.head())

    df.to_csv(OUTPUT_PATH, index= False)
    print(f"Saved: {OUTPUT_PATH}")

if __name__ == "__main__":
    transform_condition()
# %%
