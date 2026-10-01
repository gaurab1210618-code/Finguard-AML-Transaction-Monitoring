import csv
from pathlib import Path


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "scenario_metadata.csv"
)

OLD_TEXT = (
    "profile_avg = monthly_avg_volume / monthly_avg_txn_count; "
    "alert if txn > 3x profile_avg. "
    "For CUST-0001 profile_avg ~3143, injected ~26714 ~8.5x."
)

NEW_TEXT = (
    "profile_avg = monthly_avg_volume / monthly_avg_txn_count; "
    "alert if txn > 2.5x profile_avg. "
    "For CUST-0001 profile_avg ~3143, injected ~26714 ~8.5x."
)


def main():
    with open(DATA_FILE, "r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
        fieldnames = rows[0].keys()

    updated = False

    for row in rows:
        if row["scenario_id"] == "SCN_001":
            if row["baseline_definition"] == OLD_TEXT:
                row["baseline_definition"] = NEW_TEXT
                updated = True

    if not updated:
        raise RuntimeError(
            "SCN_001 baseline wording was not found exactly. "
            "No changes were made."
        )

    with open(DATA_FILE, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("SCN_001 baseline wording updated successfully.")


if __name__ == "__main__":
    main()