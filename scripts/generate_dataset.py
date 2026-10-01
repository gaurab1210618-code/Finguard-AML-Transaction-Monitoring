"""
FinGuard — AI-Assisted AML Transaction Monitoring & Human-in-the-Loop Investigation System
Synthetic Dataset Generator V2 (Portfolio Prototype)

V2 Improvements over V1:
- Transactions → deterministic monitoring rules → evidence-backed alerts
- evidence_transaction_ids added to alerts.csv
- case_history.csv now uses previous_alert_id referencing historical alerts
- Canonical alerts ALT-0001/0002/0003 all OPEN with correct priorities
- Weekday bias implemented
- Baseline definition documented and mathematically consistent
- Extended validation framework

Outputs:
  data/customers.csv
  data/transactions.csv
  data/alerts.csv (with evidence_transaction_ids)
  data/case_history.csv (with previous_alert_id)
  data/scenario_metadata.csv

Run:
  python generate_dataset.py
  python generate_dataset.py --seed 42

Dependencies: pandas, numpy
"""

import os
import re
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter

import numpy as np
import pandas as pd

# ===================== CONFIGURABLE PARAMETERS =====================
RANDOM_SEED = 42
NUM_CUSTOMERS = 300
NUM_TRANSACTIONS = 12000
NUM_ALERTS = 200
NUM_CASES = 100

OUTPUT_DIR = "data"

START_DATE = pd.Timestamp("2025-10-01")
END_DATE = pd.Timestamp("2026-03-31")
ALERT_START_DATE = pd.Timestamp("2026-02-01")

# Scenario extra transactions
SCN_001_EXTRA = 1
SCN_002_EXTRA = 8
SCN_003_EXTRA = 4
SCENARIO_EXTRA_TOTAL = SCN_001_EXTRA + SCN_002_EXTRA + SCN_003_EXTRA

# ===================== V2 MONITORING RULE THRESHOLDS =====================
RL01_WINDOW_HOURS = 24
RL01_MULTIPLIER = 2.0
RL01_MIN_COUNT = 2

RL02_MULTIPLIER = 2.5
RL02_MIN_AMOUNT = 10000

RL03_WINDOW_HOURS = 48
RL03_MIN_COUNT = 3
RL03_CV_THRESHOLD = 0.12
RL03_MIN_AMOUNT = 3000

RL04_INBOUND_MIN = 50000
RL04_OUTBOUND_MIN = 40000
RL04_WINDOW_HOURS = 12
RL04_SIMILARITY = 0.5

RL05_WINDOW_HOURS = 24
RL05_MIN_COUNTERPARTIES = 3

# ===================== CONSTANTS =====================
OCCUPATIONS = [
    "Software Engineer", "Teacher", "Retail Shop Owner", "Student", "Doctor",
    "Freelancer", "Business Analyst", "Driver", "Accountant", "Restaurant Owner",
    "Marketing Executive", "Civil Engineer", "Nurse", "Electrician",
    "Sales Manager", "Government Employee", "Consultant", "Graphic Designer",
    "Pharmacist", "Logistics Coordinator"
]

COUNTRIES_WEIGHTED = ["IN"]*17 + ["US", "GB", "SG", "AE", "DE"]
RISK_TIERS = ["LOW", "MEDIUM", "HIGH"]
RISK_WEIGHTS = [0.6, 0.3, 0.1]

CHANNELS = ["MOBILE", "INTERNET_BANKING", "BRANCH", "ATM", "CARD"]
TRANSACTION_TYPES = ["TRANSFER", "PAYMENT", "CASH_IN", "CASH_OUT", "CARD", "BANK_TRANSFER"]
TXN_TYPE_WEIGHTS = [0.25, 0.25, 0.075, 0.075, 0.20, 0.15]

ALERT_TYPES = ["HIGH_VELOCITY", "BASELINE_DEVIATION", "AMOUNT_CLUSTERING", "RAPID_IN_OUT", "MULTIPLE_COUNTERPARTIES"]
TRIGGER_RULE_MAP = {
    "HIGH_VELOCITY": f"RL-01: Transaction count > {RL01_MULTIPLIER}x expected in {RL01_WINDOW_HOURS}h",
    "BASELINE_DEVIATION": f"RL-02: Amount > {RL02_MULTIPLIER}x customer profile avg and > \u20b9{RL02_MIN_AMOUNT}",
    "AMOUNT_CLUSTERING": f"RL-03: >= {RL03_MIN_COUNT} similar amounts (CV < {RL03_CV_THRESHOLD}) in {RL03_WINDOW_HOURS}h",
    "RAPID_IN_OUT": f"RL-04: Large inbound (\u2265\u20b9{RL04_INBOUND_MIN}) followed by large outbound (\u2265\u20b9{RL04_OUTBOUND_MIN}) within {RL04_WINDOW_HOURS}h",
    "MULTIPLE_COUNTERPARTIES": f"RL-05: \u2265{RL05_MIN_COUNTERPARTIES} distinct counterparties in {RL05_WINDOW_HOURS}h"
}
STATUSES = ["OPEN", "IN_REVIEW", "CLOSED", "ESCALATED"]
PRIORITIES = ["LOW", "MEDIUM", "HIGH"]

PREV_DECISIONS = ["CLOSED", "ESCALATED", "FALSE_POSITIVE"]

ANALYST_TEMPLATES = {
    "benign": [
        "Reviewed customer history. Activity consistent with profile. Counterparty is regular. No adverse indicators. Recommended closure as false positive.",
        "Customer has stable transaction pattern over {account_age} months. Profile avg txn \u20b9{profile_avg:.0f}. Current transaction within expected variance after review. Source of funds verified.",
        "Temporary increase in volume due to seasonal business activity. Counterparties are known and verified. No suspicious indicators identified.",
        "Alert triggered by single large payment \u20b9{amount}. Customer contacted and provided invoice. Transaction explained. Marked as legitimate.",
        "No prior alerts in last 90 days. Customer risk tier {risk_tier}. Behavior broadly consistent. Closing as false positive for {customer_id}.",
        "Customer occupation {occupation} explains transaction pattern. Preferred channel {channel} used. Activity is explainable and consistent with baseline."
    ],
    "suspicious": [
        "Multiple transactions with similar amounts (\u20b9{amount}) observed within short window. Significant deviation from historical baseline profile avg \u20b9{profile_avg:.0f}. Multiple counterparties involved. Escalated for further review.",
        "Rapid inbound-outbound movement detected. Inbound \u20b9{inbound} followed by outbound \u20b9{outbound} within {hours} hours. Customer baseline profile avg \u20b9{profile_avg:.0f}/txn (monthly vol \u20b9{avg_volume}). Pattern inconsistent with profile. Escalated.",
        "Velocity exceeded threshold. {count} transactions in 24h vs expected {avg_count:.1f}. Amount clustering noted around \u20b9{amount}. Requires detailed investigation.",
        "Unusual counterparty network expansion. {count} distinct counterparties in {hours}h. Historical avg {hist_avg}. Deviation flagged for {customer_id}.",
        "Large cash transactions clustered below reporting threshold. Pattern resembles structuring-like behavior. Customer occupation {occupation} does not explain pattern. Escalated to Level-2.",
        "Inbound funds from counterparties {counterparties} followed by immediate transfer. Customer profile {risk_tier} risk. No documented business rationale. Escalated.",
        "Repeated round-tripping behavior observed for {customer_id}. Funds received and transferred within hours. No economic purpose identified. Recommended escalation."
    ]
}

def set_seeds(seed: int):
    random.seed(seed)
    np.random.seed(seed)

def random_timestamp(start: pd.Timestamp, end: pd.Timestamp, hour_weighted=True, weekday_biased=True) -> pd.Timestamp:
    max_attempts = 30
    base_date = None
    for _ in range(max_attempts):
        days = (end - start).days
        rand_day = random.randint(0, days)
        candidate = start + timedelta(days=rand_day)
        if not weekday_biased:
            base_date = candidate
            break
        wd = candidate.weekday()
        if wd < 5:
            if random.random() < 0.85:
                base_date = candidate
                break
        else:
            if random.random() < 0.35:
                base_date = candidate
                break
    if base_date is None:
        base_date = start + timedelta(days=random.randint(0, (end - start).days))

    if hour_weighted:
        hours = list(range(24))
        probs = [0.02]*9 + [0.06]*10 + [0.05]*4 + [0.02]
        hour = int(np.random.choice(hours, p=probs))
    else:
        hour = random.randint(0, 23)

    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return pd.Timestamp(base_date.year, base_date.month, base_date.day, hour, minute, second)

def random_timestamp_in_window(window_start: pd.Timestamp, window_end: pd.Timestamp) -> pd.Timestamp:
    delta_seconds = int((window_end - window_start).total_seconds())
    rand_sec = random.randint(0, max(0, delta_seconds))
    return window_start + timedelta(seconds=rand_sec)

def generate_customers(n: int) -> pd.DataFrame:
    customers = []
    for i in range(1, n+1):
        cid = f"CUST-{i:04d}"
        if cid == "CUST-0001":
            rec = {"customer_id": cid, "risk_tier": "LOW", "occupation": "Software Engineer", "country": "IN", "account_age_months": 48, "monthly_avg_volume": 110000, "monthly_avg_txn_count": 35, "preferred_channel": "MOBILE"}
        elif cid == "CUST-0002":
            rec = {"customer_id": cid, "risk_tier": "MEDIUM", "occupation": "Retail Shop Owner", "country": "IN", "account_age_months": 24, "monthly_avg_volume": 180000, "monthly_avg_txn_count": 55, "preferred_channel": "BRANCH"}
        elif cid == "CUST-0003":
            rec = {"customer_id": cid, "risk_tier": "HIGH", "occupation": "Freelancer", "country": "IN", "account_age_months": 14, "monthly_avg_volume": 80000, "monthly_avg_txn_count": 18, "preferred_channel": "INTERNET_BANKING"}
        else:
            risk = random.choices(RISK_TIERS, weights=RISK_WEIGHTS, k=1)[0]
            occupation = random.choice(OCCUPATIONS)
            country = random.choice(COUNTRIES_WEIGHTED)
            account_age = random.randint(6, 120)
            vol_tier = random.choices(["low", "medium", "high"], weights=[0.5, 0.35, 0.15], k=1)[0]
            if vol_tier == "low":
                avg_vol = random.randint(30000, 90000)
                avg_count = random.randint(8, 25)
            elif vol_tier == "medium":
                avg_vol = random.randint(80000, 250000)
                avg_count = random.randint(25, 60)
            else:
                avg_vol = random.randint(250000, 900000)
                avg_count = random.randint(60, 140)
            pref_channel = random.choice(CHANNELS)
            rec = {"customer_id": cid, "risk_tier": risk, "occupation": occupation, "country": country, "account_age_months": account_age, "monthly_avg_volume": avg_vol, "monthly_avg_txn_count": avg_count, "preferred_channel": pref_channel}
        customers.append(rec)
    return pd.DataFrame(customers)

def generate_transactions(customers_df: pd.DataFrame, total_target: int) -> pd.DataFrame:
    ext_counterparties = [f"EXT-{i:04d}" for i in range(1, 501)]
    all_customer_ids = customers_df["customer_id"].tolist()
    weights = customers_df["monthly_avg_txn_count"].values
    total_weight = weights.sum()
    raw_alloc = total_target * weights / total_weight
    alloc = np.floor(raw_alloc).astype(int)
    remainder = total_target - alloc.sum()
    frac = raw_alloc - alloc
    idx_sorted = np.argsort(-frac)
    for i in range(remainder):
        alloc[idx_sorted[i % len(alloc)]] += 1
    for i in range(len(alloc)):
        if alloc[i] < 5:
            alloc[i] = 5
    transactions = []
    txn_counter = 1
    for cust_idx, row in customers_df.iterrows():
        cust_id = row["customer_id"]
        pref_channel = row["preferred_channel"]
        cust_country = row["country"]
        monthly_vol = row["monthly_avg_volume"]
        monthly_count = row["monthly_avg_txn_count"]
        base_avg = monthly_vol / max(1, monthly_count)
        n_txn = int(alloc[cust_idx])
        for _ in range(n_txn):
            ts = random_timestamp(START_DATE, END_DATE, hour_weighted=True, weekday_biased=True)
            txn_type = random.choices(TRANSACTION_TYPES, weights=TXN_TYPE_WEIGHTS, k=1)[0]
            channel = pref_channel if random.random() < 0.6 else random.choice(CHANNELS)
            country = cust_country if random.random() < 0.9 else random.choice(COUNTRIES_WEIGHTED)
            factor = float(np.random.gamma(2.0, 0.6) + 0.2)
            amount = base_avg * factor
            if txn_type == "CARD":
                amount = min(amount, random.uniform(200, 8000))
            elif txn_type in ("CASH_IN", "CASH_OUT"):
                amount = max(amount, random.uniform(1000, base_avg * 1.5))
            elif txn_type == "PAYMENT":
                amount = amount * random.uniform(0.5, 1.2)
            amount = max(100, amount)
            amount = round(float(amount), 2)
            is_incoming = random.random() < 0.45
            if random.random() < 0.15:
                other_cust = random.choice([c for c in all_customer_ids if c != cust_id])
                counterparty = other_cust
            else:
                counterparty = random.choice(ext_counterparties)
            if is_incoming:
                sender_id = counterparty
                receiver_id = cust_id
            else:
                sender_id = cust_id
                receiver_id = counterparty
            txn_id = f"TXN-{txn_counter:05d}"
            txn_counter += 1
            transactions.append({"transaction_id": txn_id, "customer_id": cust_id, "timestamp": ts, "amount": amount, "transaction_type": txn_type, "sender_id": sender_id, "receiver_id": receiver_id, "channel": channel, "country": country})
    df = pd.DataFrame(transactions)
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df

def inject_scenario_transactions(transactions_df: pd.DataFrame, customers_df: pd.DataFrame):
    ext_counterparties = [f"EXT-{i:04d}" for i in range(1, 501)]
    scenario_txns = []
    evidence_map = {"SCN_001": [], "SCN_002": [], "SCN_003": []}
    max_txn_num = len(transactions_df) + 1
    cust_001 = customers_df[customers_df["customer_id"] == "CUST-0001"].iloc[0]
    profile_avg_001 = cust_001["monthly_avg_volume"] / cust_001["monthly_avg_txn_count"]
    scn1_amount = round(profile_avg_001 * 8.5, 2)
    scn1_ts = pd.Timestamp("2026-03-10 14:30:00")
    txn_id_1 = f"TXN-{max_txn_num:05d}"
    scenario_txns.append({"transaction_id": txn_id_1, "customer_id": "CUST-0001", "timestamp": scn1_ts, "amount": scn1_amount, "transaction_type": "PAYMENT", "sender_id": "CUST-0001", "receiver_id": random.choice(ext_counterparties), "channel": "MOBILE", "country": "IN"})
    evidence_map["SCN_001"].append(txn_id_1)
    max_txn_num += 1
    scn2_start = pd.Timestamp("2026-03-15 10:00:00")
    scn2_end = pd.Timestamp("2026-03-16 16:00:00")
    clustered_amounts = [48200, 48500, 48800, 49000, 48300, 48600, 48900, 48400]
    for amt in clustered_amounts:
        ts = random_timestamp_in_window(scn2_start, scn2_end)
        tid = f"TXN-{max_txn_num:05d}"
        scenario_txns.append({"transaction_id": tid, "customer_id": "CUST-0002", "timestamp": ts, "amount": float(amt), "transaction_type": "CASH_IN", "sender_id": random.choice(ext_counterparties), "receiver_id": "CUST-0002", "channel": "BRANCH", "country": "IN"})
        evidence_map["SCN_002"].append(tid)
        max_txn_num += 1
    scn3_defs = [(pd.Timestamp("2026-03-20 11:00:00"), 250000.0, True, "BANK_TRANSFER"), (pd.Timestamp("2026-03-20 14:30:00"), 240000.0, False, "BANK_TRANSFER"), (pd.Timestamp("2026-03-21 10:15:00"), 300000.0, True, "BANK_TRANSFER"), (pd.Timestamp("2026-03-21 13:45:00"), 290000.0, False, "TRANSFER")]
    for ts, amt, is_incoming, ttype in scn3_defs:
        tid = f"TXN-{max_txn_num:05d}"
        if is_incoming:
            sender = random.choice(ext_counterparties)
            receiver = "CUST-0003"
        else:
            sender = "CUST-0003"
            receiver = random.choice(ext_counterparties)
        scenario_txns.append({"transaction_id": tid, "customer_id": "CUST-0003", "timestamp": ts, "amount": float(amt), "transaction_type": ttype, "sender_id": sender, "receiver_id": receiver, "channel": "INTERNET_BANKING", "country": "IN"})
        evidence_map["SCN_003"].append(tid)
        max_txn_num += 1
    scn_df = pd.DataFrame(scenario_txns)
    combined = pd.concat([transactions_df, scn_df], ignore_index=True)
    combined = combined.sort_values("timestamp").reset_index(drop=True)
    return combined, evidence_map

def run_monitoring_rules(transactions_df: pd.DataFrame, customers_df: pd.DataFrame):
    candidates = []
    customer_map = {row["customer_id"]: row for _, row in customers_df.iterrows()}
    grouped = transactions_df.sort_values("timestamp").groupby("customer_id")
    for cust_id, group in grouped:
        group = group.sort_values("timestamp").reset_index(drop=True)
        cust_info = customer_map.get(cust_id)
        if cust_info is None:
            continue
        profile_avg = cust_info["monthly_avg_volume"] / max(1, cust_info["monthly_avg_txn_count"])
        expected_daily = cust_info["monthly_avg_txn_count"] / 30.0
        for _, txn in group.iterrows():
            if txn["amount"] >= RL02_MIN_AMOUNT and txn["amount"] > RL02_MULTIPLIER * profile_avg:
                candidates.append({"customer_id": cust_id, "created_at": txn["timestamp"] + timedelta(hours=1), "alert_type": "BASELINE_DEVIATION", "trigger_rule": TRIGGER_RULE_MAP["BASELINE_DEVIATION"], "evidence": [txn["transaction_id"]], "timestamp": txn["timestamp"]})
        group["date"] = pd.to_datetime(group["timestamp"]).dt.date
        daily_groups = group.groupby("date")
        for date, day_txns in daily_groups:
            cnt = len(day_txns)
            if cnt >= RL01_MIN_COUNT and cnt >= RL01_MULTIPLIER * max(1.0, expected_daily):
                max_ts = day_txns["timestamp"].max()
                candidates.append({"customer_id": cust_id, "created_at": max_ts + timedelta(hours=1), "alert_type": "HIGH_VELOCITY", "trigger_rule": TRIGGER_RULE_MAP["HIGH_VELOCITY"], "evidence": day_txns["transaction_id"].tolist(), "timestamp": max_ts})
        for i in range(len(group)):
            window_start = group.iloc[i]["timestamp"]
            window_end = window_start + timedelta(hours=RL03_WINDOW_HOURS)
            window_txns = group[(group["timestamp"] >= window_start) & (group["timestamp"] <= window_end)]
            window_filtered = window_txns[window_txns["amount"] >= RL03_MIN_AMOUNT]
            if len(window_filtered) >= RL03_MIN_COUNT:
                amounts = window_filtered["amount"]
                mean = amounts.mean()
                std = amounts.std()
                if mean > 0:
                    cv = std / mean
                    if cv < RL03_CV_THRESHOLD:
                        candidates.append({"customer_id": cust_id, "created_at": window_end, "alert_type": "AMOUNT_CLUSTERING", "trigger_rule": TRIGGER_RULE_MAP["AMOUNT_CLUSTERING"], "evidence": window_filtered["transaction_id"].tolist(), "timestamp": window_end})
        inbound_large = group[(group["receiver_id"] == cust_id) & (group["amount"] >= RL04_INBOUND_MIN)]
        outbound_large = group[(group["sender_id"] == cust_id) & (group["amount"] >= RL04_OUTBOUND_MIN)]
        for _, in_txn in inbound_large.iterrows():
            in_time = in_txn["timestamp"]
            window_end = in_time + timedelta(hours=RL04_WINDOW_HOURS)
            matching_out = outbound_large[(outbound_large["timestamp"] > in_time) & (outbound_large["timestamp"] <= window_end)]
            for _, out_txn in matching_out.iterrows():
                candidates.append({"customer_id": cust_id, "created_at": out_txn["timestamp"] + timedelta(minutes=30), "alert_type": "RAPID_IN_OUT", "trigger_rule": TRIGGER_RULE_MAP["RAPID_IN_OUT"], "evidence": [in_txn["transaction_id"], out_txn["transaction_id"]], "timestamp": out_txn["timestamp"]})
        for date, day_txns in daily_groups:
            counterparties = set()
            for _, txn in day_txns.iterrows():
                if txn["sender_id"] == cust_id:
                    counterparties.add(txn["receiver_id"])
                else:
                    counterparties.add(txn["sender_id"])
            counterparties.discard(cust_id)
            if len(counterparties) >= RL05_MIN_COUNTERPARTIES:
                max_ts = day_txns["timestamp"].max()
                candidates.append({"customer_id": cust_id, "created_at": max_ts + timedelta(hours=1), "alert_type": "MULTIPLE_COUNTERPARTIES", "trigger_rule": TRIGGER_RULE_MAP["MULTIPLE_COUNTERPARTIES"], "evidence": day_txns["transaction_id"].tolist(), "timestamp": max_ts})
    return candidates

def deduplicate_candidates(candidates):
    deduped = {}
    for cand in candidates:
        date_key = pd.to_datetime(cand["created_at"]).date()
        key = (cand["customer_id"], cand["alert_type"], date_key)
        if key not in deduped:
            deduped[key] = cand
        else:
            existing = deduped[key]
            merged_evidence = list(set(existing["evidence"] + cand["evidence"]))
            existing["evidence"] = merged_evidence[:20]
            if cand["created_at"] > existing["created_at"]:
                existing["created_at"] = cand["created_at"]
            deduped[key] = existing
    return list(deduped.values())

def generate_alerts_from_rules(candidates, customers_df, evidence_map, num_alerts=200):
    filtered = [c for c in candidates if ALERT_START_DATE <= pd.to_datetime(c["created_at"]) <= END_DATE]
    deduped = deduplicate_candidates(filtered)
    ordinary_pool = [c for c in deduped if c["customer_id"] not in ("CUST-0001", "CUST-0002", "CUST-0003")]
    ordinary_pool = sorted(ordinary_pool, key=lambda x: (x["created_at"], x["customer_id"]))
    needed = num_alerts - 3
    if len(ordinary_pool) >= needed:
        sampled = random.sample(ordinary_pool, needed)
    else:
        sampled = ordinary_pool
        print(f"WARNING: Only {len(ordinary_pool)} rule-based candidates found, less than needed {needed}. Using all.")
    sampled = sorted(sampled, key=lambda x: x["created_at"])
    alerts = []
    canonical_defs = [
        {"alert_id": "ALT-0001", "customer_id": "CUST-0001", "created_at": pd.Timestamp("2026-03-11 09:15:00"), "alert_type": "BASELINE_DEVIATION", "trigger_rule": TRIGGER_RULE_MAP["BASELINE_DEVIATION"], "status": "OPEN", "priority": "LOW", "evidence": evidence_map["SCN_001"]},
        {"alert_id": "ALT-0002", "customer_id": "CUST-0002", "created_at": pd.Timestamp("2026-03-16 18:00:00"), "alert_type": "AMOUNT_CLUSTERING", "trigger_rule": TRIGGER_RULE_MAP["AMOUNT_CLUSTERING"], "status": "OPEN", "priority": "HIGH", "evidence": evidence_map["SCN_002"]},
        {"alert_id": "ALT-0003", "customer_id": "CUST-0003", "created_at": pd.Timestamp("2026-03-21 15:00:00"), "alert_type": "RAPID_IN_OUT", "trigger_rule": TRIGGER_RULE_MAP["RAPID_IN_OUT"], "status": "OPEN", "priority": "HIGH", "evidence": evidence_map["SCN_003"]},
    ]
    for can in canonical_defs:
        alerts.append({"alert_id": can["alert_id"], "customer_id": can["customer_id"], "created_at": can["created_at"], "alert_type": can["alert_type"], "trigger_rule": can["trigger_rule"], "status": can["status"], "priority": can["priority"], "evidence_transaction_ids": "|".join(can["evidence"])})
    for idx, cand in enumerate(sampled, start=4):
        alert_id = f"ALT-{idx:04d}"
        if cand["alert_type"] in ("AMOUNT_CLUSTERING", "RAPID_IN_OUT", "HIGH_VELOCITY"):
            priority = random.choices(PRIORITIES, weights=[0.15, 0.35, 0.5], k=1)[0]
        else:
            priority = random.choices(PRIORITIES, weights=[0.35, 0.4, 0.25], k=1)[0]
        ev_list = cand["evidence"][:15]
        ev_str = "|".join(ev_list)
        alerts.append({"alert_id": alert_id, "customer_id": cand["customer_id"], "created_at": cand["created_at"], "alert_type": cand["alert_type"], "trigger_rule": cand["trigger_rule"], "status": "OPEN", "priority": priority, "evidence_transaction_ids": ev_str})
    alerts_df = pd.DataFrame(alerts)
    alerts_df = alerts_df.sort_values("created_at").reset_index(drop=True)
    return alerts_df

def generate_case_history_v2(alerts_df: pd.DataFrame, customers_df: pd.DataFrame, num_cases: int) -> pd.DataFrame:
    prev_pool = alerts_df[~alerts_df["alert_id"].isin(["ALT-0001", "ALT-0002", "ALT-0003"])].copy()
    prev_pool = prev_pool.sort_values("created_at")
    if len(prev_pool) == 0:
        prev_pool = alerts_df.copy()
    customers_map = {row["customer_id"]: row for _, row in customers_df.iterrows()}
    prev_list = prev_pool.to_dict(orient="records")
    random.shuffle(prev_list)
    cases = []
    used_prev_counts = Counter()
    for i in range(1, num_cases+1):
        case_id = f"CASE-{i:04d}"
        eligible = [p for p in prev_list if used_prev_counts[p["alert_id"]] < 2]
        if not eligible:
            eligible = prev_list
            used_prev_counts = Counter()
        prev_alert = random.choice(eligible)
        used_prev_counts[prev_alert["alert_id"]] += 1
        prev_alert_id = prev_alert["alert_id"]
        customer_id = prev_alert["customer_id"]
        cust_info = customers_map.get(customer_id, {})
        prev_created = pd.to_datetime(prev_alert["created_at"])
        delta_days = random.randint(1, 20)
        delta_hours = random.randint(0, 23)
        case_created = prev_created + timedelta(days=delta_days, hours=delta_hours)
        if case_created > END_DATE:
            case_created = END_DATE - timedelta(days=random.randint(0, 5))
        if case_created <= prev_created:
            case_created = prev_created + timedelta(days=1)
        prev_decision = random.choices(PREV_DECISIONS, weights=[0.3, 0.2, 0.5], k=1)[0]
        disposition = prev_decision
        if prev_decision in ("FALSE_POSITIVE", "CLOSED"):
            template = random.choice(ANALYST_TEMPLATES["benign"])
        else:
            template = random.choice(ANALYST_TEMPLATES["suspicious"])
        try:
            profile_avg = cust_info.get("monthly_avg_volume", 100000) / max(1, cust_info.get("monthly_avg_txn_count", 20))
            note = template.format(customer_id=customer_id, account_age=cust_info.get("account_age_months", 24), amount=round(random.uniform(20000, 50000), 2), avg_volume=cust_info.get("monthly_avg_volume", 100000), risk_tier=cust_info.get("risk_tier", "LOW"), occupation=cust_info.get("occupation", "Business Owner"), channel=cust_info.get("preferred_channel", "MOBILE"), inbound=random.choice([250000, 300000, 180000]), outbound=random.choice([240000, 290000, 170000]), hours=random.choice([2, 3, 4, 5]), baseline=cust_info.get("monthly_avg_volume", 80000), count=random.randint(6, 12), avg_count=cust_info.get("monthly_avg_txn_count", 10) / 30.0, hist_avg=random.randint(1, 3), counterparties="EXT-0123, EXT-0456, EXT-0789", profile_avg=profile_avg)
        except Exception:
            note = template
        cases.append({"case_id": case_id, "customer_id": customer_id, "previous_alert_id": prev_alert_id, "previous_decision": prev_decision, "disposition": disposition, "analyst_notes": note, "created_at": case_created})
    df = pd.DataFrame(cases)
    df = df.sort_values("created_at").reset_index(drop=True)
    return df

def generate_scenario_metadata() -> pd.DataFrame:
    data = [
        {"scenario_id": "SCN_001", "customer_id": "CUST-0001", "alert_id": "ALT-0001", "scenario_name": "False Positive", "expected_risk_band": "LOW", "expected_reason": "Activity is explainable and broadly consistent with customer history.", "baseline_definition": "profile_avg = monthly_avg_volume / monthly_avg_txn_count; alert if txn > 3x profile_avg. For CUST-0001 profile_avg ~3143, injected ~26714 ~8.5x."},
        {"scenario_id": "SCN_002", "customer_id": "CUST-0002", "alert_id": "ALT-0002", "scenario_name": "Structuring-like Pattern", "expected_risk_band": "HIGH", "expected_reason": "Multiple clustered transactions materially deviate from the normal customer pattern.", "baseline_definition": "Normal avg ~3273 (180k/55). Clustered amounts 48.2k-49k (~15x baseline) within 30h, CV < 5%."},
        {"scenario_id": "SCN_003", "customer_id": "CUST-0003", "alert_id": "ALT-0003", "scenario_name": "Rapid Inbound-Outbound Pattern", "expected_risk_band": "HIGH", "expected_reason": "Rapid movement of funds and substantial deviation from historical customer behavior.", "baseline_definition": "Baseline monthly vol 70k-90k, profile avg ~4444. Injected 250k/240k and 300k/290k in-out within 6h windows."},
    ]
    return pd.DataFrame(data)

def validate_datasets_v2(customers_df, transactions_df, alerts_df, cases_df, scenario_df, evidence_map):
    print("\n========== VALIDATION REPORT V2 ==========")
    checks_passed = 0
    checks_failed = 0
    def check(condition, msg):
        nonlocal checks_passed, checks_failed
        if condition:
            print(f"\u2713 PASS: {msg}")
            checks_passed += 1
            return True
        else:
            print(f"\u2717 FAIL: {msg}")
            checks_failed += 1
            return False
    cust_ids_set = set(customers_df["customer_id"])
    alert_ids_set = set(alerts_df["alert_id"])
    txn_ids_set = set(transactions_df["transaction_id"])
    check(customers_df["customer_id"].is_unique, "No duplicate customer_id")
    check(transactions_df["transaction_id"].is_unique, "No duplicate transaction_id")
    check(alerts_df["alert_id"].is_unique, "No duplicate alert_id")
    check(cases_df["case_id"].is_unique, "No duplicate case_id")
    check(scenario_df["scenario_id"].is_unique, "No duplicate scenario_id")
    check(set(transactions_df["customer_id"]).issubset(cust_ids_set), "Every transaction.customer_id exists in customers")
    check(set(alerts_df["customer_id"]).issubset(cust_ids_set), "Every alert.customer_id exists in customers")
    check(set(cases_df["customer_id"]).issubset(cust_ids_set), "Every case_history.customer_id exists in customers")
    check(set(cases_df["previous_alert_id"]).issubset(alert_ids_set), "Every case_history.previous_alert_id exists in alerts")
    check(set(scenario_df["customer_id"]).issubset(cust_ids_set), "Every scenario_metadata.customer_id exists in customers")
    check(set(scenario_df["alert_id"]).issubset(alert_ids_set), "Every scenario_metadata.alert_id exists in alerts")
    try:
        pd.to_datetime(transactions_df["timestamp"])
        pd.to_datetime(alerts_df["created_at"])
        pd.to_datetime(cases_df["created_at"])
        check(True, "Timestamps are valid ISO dates")
    except Exception as e:
        check(False, f"Timestamps valid ({e})")
    check((transactions_df["amount"] > 0).all(), "All transaction amounts > 0")
    has_at = False
    for df in [customers_df, transactions_df, alerts_df, cases_df, scenario_df]:
        for col in df.columns:
            if df[col].dtype == object:
                if df[col].astype(str).str.contains("@", na=False).any():
                    has_at = True
    check(not has_at, "No accidental email-like PII (@ symbol)")
    forbidden_cols = {"email", "phone", "pan", "aadhaar", "address", "name"}
    check(len(forbidden_cols.intersection(set(customers_df.columns))) == 0, "No PII columns in customers.csv")
    check(set(alerts_df["alert_type"]).issubset(set(ALERT_TYPES)), f"Every alert has valid alert_type {ALERT_TYPES}")
    check(alerts_df["trigger_rule"].apply(lambda x: str(x).startswith("RL-")).all(), "Every alert has valid trigger_rule (RL- prefix)")
    check("evidence_transaction_ids" in alerts_df.columns, "alerts.csv has evidence_transaction_ids column")
    evidence_ok = True
    evidence_belongs_ok = True
    for _, alert in alerts_df.iterrows():
        ev_str = str(alert.get("evidence_transaction_ids", ""))
        if not ev_str:
            evidence_ok = False
            break
        ev_ids = [e.strip() for e in ev_str.split("|") if e.strip()]
        if not ev_ids:
            evidence_ok = False
            break
        for eid in ev_ids:
            if eid not in txn_ids_set:
                evidence_ok = False
                break
            txn_row = transactions_df[transactions_df["transaction_id"] == eid]
            if not txn_row.empty:
                if txn_row.iloc[0]["customer_id"] != alert["customer_id"]:
                    evidence_belongs_ok = False
        if not evidence_ok:
            break
    check(evidence_ok, "Evidence transaction IDs reference real transactions")
    check(evidence_belongs_ok, "Evidence transactions belong to alert's customer")
    for alt_id, expected_type in [("ALT-0001", "BASELINE_DEVIATION"), ("ALT-0002", "AMOUNT_CLUSTERING"), ("ALT-0003", "RAPID_IN_OUT")]:
        row = alerts_df[alerts_df["alert_id"] == alt_id]
        check(not row.empty, f"Canonical {alt_id} exists")
        if not row.empty:
            check(row.iloc[0]["alert_type"] == expected_type, f"{alt_id} has expected alert_type {expected_type}")
            check(row.iloc[0]["status"] == "OPEN", f"{alt_id} status is OPEN (before analyst disposition)")
    check(alerts_df[alerts_df["alert_id"]=="ALT-0001"].iloc[0]["priority"]=="LOW" if not alerts_df[alerts_df["alert_id"]=="ALT-0001"].empty else False, "SCN_001 priority = LOW")
    check(alerts_df[alerts_df["alert_id"]=="ALT-0002"].iloc[0]["priority"]=="HIGH" if not alerts_df[alerts_df["alert_id"]=="ALT-0002"].empty else False, "SCN_002 priority = HIGH")
    check(alerts_df[alerts_df["alert_id"]=="ALT-0003"].iloc[0]["priority"]=="HIGH" if not alerts_df[alerts_df["alert_id"]=="ALT-0003"].empty else False, "SCN_003 priority = HIGH")
    for scn_id, expected_ids in evidence_map.items():
        alt_id = {"SCN_001":"ALT-0001","SCN_002":"ALT-0002","SCN_003":"ALT-0003"}[scn_id]
        row = alerts_df[alerts_df["alert_id"]==alt_id]
        if not row.empty:
            ev_str = str(row.iloc[0]["evidence_transaction_ids"])
            ev_set = set(ev_str.split("|"))
            contains_all = all(eid in ev_set for eid in expected_ids)
            check(contains_all, f"{scn_id} evidence contains injected transactions {expected_ids}")
        else:
            check(False, f"{scn_id} evidence check - alert {alt_id} missing")
    scn2_txns = transactions_df[transactions_df["customer_id"] == "CUST-0002"]
    scn2_window = scn2_txns[(scn2_txns["timestamp"] >= pd.Timestamp("2026-03-15 10:00:00")) & (scn2_txns["timestamp"] <= pd.Timestamp("2026-03-16 16:00:00"))]
    scn2_clustered = scn2_window[scn2_window["amount"] >= 40000]
    if len(scn2_clustered) >= 5:
        std = scn2_clustered["amount"].std()
        mean = scn2_clustered["amount"].mean()
        cv = std / mean if mean != 0 else 1
        check(cv < 0.08, f"SCN_002 clustering CV={cv:.4f} < 0.08")
        check(len(scn2_clustered) >= 8, f"SCN_002 has 8 clustered txns (found {len(scn2_clustered)})")
    else:
        check(False, f"SCN_002 clustered check found {len(scn2_clustered)}")
    scn3_txns = transactions_df[transactions_df["customer_id"] == "CUST-0003"]
    scn3_window = scn3_txns[(scn3_txns["timestamp"] >= pd.Timestamp("2026-03-20")) & (scn3_txns["timestamp"] <= pd.Timestamp("2026-03-22"))]
    large = scn3_window[scn3_window["amount"] >= 200000]
    check(len(large) >= 3, f"SCN_003 has >=3 large txns (found {len(large)})")
    counterparties = pd.concat([scn3_window["sender_id"], scn3_window["receiver_id"]]).nunique()
    check(counterparties >= 3, f"SCN_003 multiple counterparties {counterparties} >=3")
    hist_ok = True
    for _, case in cases_df.iterrows():
        prev_id = case["previous_alert_id"]
        prev_row = alerts_df[alerts_df["alert_id"] == prev_id]
        if prev_row.empty:
            hist_ok = False
            break
        prev_created = pd.to_datetime(prev_row.iloc[0]["created_at"])
        case_created = pd.to_datetime(case["created_at"])
        if case_created <= prev_created:
            hist_ok = False
            break
    check(hist_ok, "Historical case timestamps logically ordered (case after previous_alert)")
    prev_counts = Counter(cases_df["previous_alert_id"])
    max_reuse = max(prev_counts.values()) if prev_counts else 0
    check(max_reuse <= 2, f"No excessive duplicate historical cases (max reuse {max_reuse} <=2)")
    canonical_ids = {"ALT-0001","ALT-0002","ALT-0003"}
    overlap = set(cases_df["previous_alert_id"]).intersection(canonical_ids)
    check(len(overlap) == 0, f"Historical cases do NOT reference current canonical alerts (overlap {overlap})")
    customers_with_alerts = alerts_df["customer_id"].nunique()
    customers_without_alerts = len(customers_df) - customers_with_alerts
    check(customers_with_alerts > 0 and customers_without_alerts > 0, f"Both alert and non-alert customers exist ({customers_with_alerts} with, {customers_without_alerts} without)")
    check(transactions_df["amount"].std() > 1000, "Transaction amount variance exists")
    tx_dates = pd.to_datetime(transactions_df["timestamp"])
    weekdays = tx_dates.dt.weekday < 5
    weekday_ratio = weekdays.mean()
    check(weekday_ratio > 0.6, f"Weekday bias implemented: {weekday_ratio:.2%} weekdays (>60%)")
    print(f"\n--- Summary ---")
    print(f"customers generated: {len(customers_df)}")
    print(f"transactions generated: {len(transactions_df)}")
    print(f"alerts generated: {len(alerts_df)} (with evidence)")
    print(f"cases generated: {len(cases_df)} (with previous_alert_id)")
    print(f"scenario records generated: {len(scenario_df)}")
    print(f"validation checks: {checks_passed} passed / {checks_failed} failed")
    print(f"========================================\n")
    return checks_failed == 0

def main():
    parser = argparse.ArgumentParser(description="FinGuard Synthetic Dataset Generator V2")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed for reproducibility")
    parser.add_argument("--customers", type=int, default=NUM_CUSTOMERS, help="Number of customers")
    parser.add_argument("--transactions", type=int, default=NUM_TRANSACTIONS, help="Number of transactions")
    parser.add_argument("--alerts", type=int, default=NUM_ALERTS, help="Number of alerts")
    parser.add_argument("--cases", type=int, default=NUM_CASES, help="Number of case history records")
    parser.add_argument("--output", type=str, default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()
    set_seeds(args.seed)
    print(f"FinGuard Synthetic Dataset Generator V2")
    print(f"Seed: {args.seed} | Customers: {args.customers} | Transactions: {args.transactions} | Alerts: {args.alerts} | Cases: {args.cases}")
    print(f"Monitoring Rules: RL-01 velocity>{RL01_MULTIPLIER}x/{RL01_WINDOW_HOURS}h, RL-02 baseline>{RL02_MULTIPLIER}x & >{RL02_MIN_AMOUNT}, RL-03 cluster CV<{RL03_CV_THRESHOLD}, RL-04 in>= {RL04_INBOUND_MIN}/out>= {RL04_OUTBOUND_MIN} in {RL04_WINDOW_HOURS}h, RL-05 counterparties>= {RL05_MIN_COUNTERPARTIES}")
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    print("Generating customers...")
    customers_df = generate_customers(args.customers)
    normal_target = max(0, args.transactions - SCENARIO_EXTRA_TOTAL)
    print(f"Generating {normal_target} normal transactions (with weekday bias)...")
    transactions_normal_df = generate_transactions(customers_df, normal_target)
    print("Injecting canonical scenarios (SCN_001, SCN_002, SCN_003)...")
    transactions_df, evidence_map = inject_scenario_transactions(transactions_normal_df, customers_df)
    print(f"  SCN_001 evidence: {evidence_map['SCN_001']}")
    print(f"  SCN_002 evidence: {evidence_map['SCN_002']}")
    print(f"  SCN_003 evidence: {evidence_map['SCN_003']}")
    print("Running deterministic monitoring rules over transactions...")
    candidates = run_monitoring_rules(transactions_df, customers_df)
    print(f"  Found {len(candidates)} raw rule hits")
    deduped = deduplicate_candidates([c for c in candidates if ALERT_START_DATE <= pd.to_datetime(c['created_at']) <= END_DATE])
    print(f"  After dedup and date filter: {len(deduped)} candidate alerts")
    print(f"Generating {args.alerts} evidence-backed alerts...")
    alerts_df = generate_alerts_from_rules(candidates, customers_df, evidence_map, num_alerts=args.alerts)
    print(f"Generating {args.cases} historical case records with previous_alert_id...")
    cases_df = generate_case_history_v2(alerts_df, customers_df, args.cases)
    print("Generating scenario metadata V2...")
    scenario_df = generate_scenario_metadata()
    print(f"Saving to {output_path}/ ...")
    customers_df.to_csv(output_path / "customers.csv", index=False)
    transactions_df.to_csv(output_path / "transactions.csv", index=False)
    alerts_df.to_csv(output_path / "alerts.csv", index=False)
    cases_df.to_csv(output_path / "case_history.csv", index=False)
    scenario_df.to_csv(output_path / "scenario_metadata.csv", index=False)
    validate_datasets_v2(customers_df, transactions_df, alerts_df, cases_df, scenario_df, evidence_map)
    print(f"Done. Files saved in {output_path.resolve()}")

if __name__ == "__main__":
    main()
