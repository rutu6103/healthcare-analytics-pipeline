import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

scripts = [
    "extract_fhir.py",
    "transform_patient.py",
    "transform_encounter.py",
    "transform_condition.py",
    "load_postgres.py"
]

for script in scripts:
    script_path = BASE_DIR / script

    print(f"Running {script}")

    subprocess.run(
        [sys.executable, str(script_path)],
        check=True
    )

print("Pipeline Completed")
