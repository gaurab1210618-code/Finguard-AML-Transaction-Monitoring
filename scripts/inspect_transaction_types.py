import csv
from collections import Counter, defaultdict
from pathlib import Path


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "transactions.csv"
)


with open(DATA_FILE, "r", encoding="utf-8-sig", newline="") as file:
    rows = list(csv.DictReader(file))


print("=" * 60)
print("Transaction Type Inspection")
print("=" * 60)

counts = Counter(
    row["transaction_type"]
    for row in rows
)

print("\nTransaction type counts:")

for transaction_type, count in sorted(counts.items()):
    print(f"  {transaction_type}: {count}")


print("\nSample transactions by type:")

samples = defaultdict(list)

for row in rows:
    transaction_type = row["transaction_type"]

    if len(samples[transaction_type]) < 3:
        samples[transaction_type].append(row)


for transaction_type in sorted(samples):

    print(f"\n--- {transaction_type} ---")

    for row in samples[transaction_type]:

        print(
            f"ID={row['transaction_id']} | "
            f"Customer={row['customer_id']} | "
            f"Amount={row['amount']} | "
            f"Sender={row['sender_id']} | "
            f"Receiver={row['receiver_id']} | "
            f"Channel={row['channel']}"
        )