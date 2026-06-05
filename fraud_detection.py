"""
Défi — Détection de fraude financière.

Vous devez implémenter la fonction `detect_fraud`.
La fonction `load_transactions` vous est FOURNIE (ne la modifiez pas).
"""

import csv
from datetime import datetime, timezone
from statistics import median


REQUIRED_FIELDS = ("user_id", "amount", "country")


def load_transactions(path):
    """Lit un fichier CSV de transactions et renvoie une liste de dicts."""
    transactions = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append(_clean_row(row))
    return transactions


def _clean_row(row):
    def get(key):
        v = row.get(key)
        return v.strip() if isinstance(v, str) and v.strip() != "" else None

    amount_raw = get("amount")
    try:
        amount = float(amount_raw) if amount_raw is not None else None
    except ValueError:
        amount = None

    card_raw = get("card_present")
    if card_raw is None:
        card_present = None
    else:
        card_present = card_raw.lower() in ("true", "1", "yes", "oui")

    return {
        "transaction_id": get("transaction_id"),
        "timestamp": get("timestamp"),
        "user_id": get("user_id"),
        "amount": amount,
        "currency": get("currency"),
        "merchant": get("merchant"),
        "country": get("country"),
        "card_present": card_present,
    }


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _parse_timestamp(value):
    if not isinstance(value, str) or not value.strip():
        return None

    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None

    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)

    return parsed


def _build_profiles(transactions):
    profiles = {}

    for transaction in transactions:
        if not isinstance(transaction, dict):
            continue

        user_id = transaction.get("user_id")
        amount = transaction.get("amount")
        if not user_id or not _is_number(amount) or amount <= 0:
            continue

        key = (user_id, transaction.get("currency"))
        profile = profiles.setdefault(key, {"amounts": [], "countries": set()})
        profile["amounts"].append(amount)

        country = transaction.get("country")
        if country:
            profile["countries"].add(country)

    return profiles


def _build_timelines(transactions):
    timelines = {}

    for index, transaction in enumerate(transactions):
        if not isinstance(transaction, dict):
            continue

        user_id = transaction.get("user_id")
        timestamp = _parse_timestamp(transaction.get("timestamp"))
        if not user_id or timestamp is None:
            continue

        timelines.setdefault(user_id, []).append(
            {
                "index": index,
                "timestamp": timestamp,
                "country": transaction.get("country"),
            }
        )

    return timelines


def _score_amount_anomaly(amount, profile):
    if not _is_number(amount) or amount <= 0:
        return 0.0, None

    amounts = [
        value
        for value in profile.get("amounts", [])
        if _is_number(value) and value > 0
    ]
    if len(amounts) < 4:
        return 0.0, None

    usual_amount = median(amounts)
    if usual_amount <= 0:
        return 0.0, None

    ratio = amount / usual_amount
    gap = amount - usual_amount

    if ratio >= 8 and gap >= 100:
        return 0.95, "Montant tres superieur a l'habitude du client"
    if ratio >= 4 and gap >= 500:
        return 0.8, "Montant inhabituel pour ce client"

    return 0.0, None


def _score_geography(index, transaction, timelines):
    user_id = transaction.get("user_id")
    country = transaction.get("country")
    timestamp = _parse_timestamp(transaction.get("timestamp"))
    if not user_id or not country or timestamp is None:
        return 0.0, None

    for event in timelines.get(user_id, []):
        if event["index"] == index or not event.get("country"):
            continue
        if event["country"] == country:
            continue

        minutes = abs((timestamp - event["timestamp"]).total_seconds()) / 60
        if minutes <= 120:
            return 0.88, "Deux pays differents en trop peu de temps"

    return 0.0, None


def _score_frequency(index, transaction, timelines):
    user_id = transaction.get("user_id")
    timestamp = _parse_timestamp(transaction.get("timestamp"))
    if not user_id or timestamp is None:
        return 0.0, None

    close_events = 0
    for event in timelines.get(user_id, []):
        minutes = abs((timestamp - event["timestamp"]).total_seconds()) / 60
        if minutes <= 10:
            close_events += 1

    if close_events >= 4:
        return 0.75, "Frequence de transactions inhabituelle"

    return 0.0, None


def detect_fraud(transactions):
    """Analyse une liste de transactions et renvoie un verdict pour chacune.

    Retour : list[dict] avec transaction_id, fraud_score (0-1),
    is_suspicious (bool), reason (str) — un résultat par transaction, même ordre.
    """
    results = []
    transactions = transactions or []
    profiles = _build_profiles(transactions)
    timelines = _build_timelines(transactions)

    for index, transaction in enumerate(transactions, start=1):
        tx = transaction if isinstance(transaction, dict) else {}
        tx_index = index - 1
        transaction_id = tx.get("transaction_id") or f"UNKNOWN-{index}"
        amount = tx.get("amount")
        profile = profiles.get((tx.get("user_id"), tx.get("currency")), {})
        amount_score, amount_reason = _score_amount_anomaly(amount, profile)
        geography_score, geography_reason = _score_geography(tx_index, tx, timelines)
        frequency_score, frequency_reason = _score_frequency(tx_index, tx, timelines)
        missing_fields = [
            field for field in REQUIRED_FIELDS if tx.get(field) in (None, "")
        ]

        if isinstance(amount, (int, float)) and amount <= 0:
            score = 0.9
            is_suspicious = True
            reason = "Montant nul ou negatif"
        elif missing_fields:
            score = 0.85
            is_suspicious = True
            reason = "Champs obligatoires manquants: " + ", ".join(missing_fields)
        else:
            signals = [
                (amount_score, amount_reason),
                (geography_score, geography_reason),
                (frequency_score, frequency_reason),
            ]
            score, reason = max(signals, key=lambda signal: signal[0])
            is_suspicious = True
            if not reason:
                score = 0.0
                is_suspicious = False
                reason = "Transaction conforme au profil du client"

        results.append(
            {
                "transaction_id": transaction_id,
                "fraud_score": score,
                "is_suspicious": is_suspicious,
                "reason": reason,
            }
        )

    return results
