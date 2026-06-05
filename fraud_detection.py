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


def detect_fraud(transactions):
    """Analyse une liste de transactions et renvoie un verdict pour chacune.

    Retour : list[dict] avec transaction_id, fraud_score (0-1),
    is_suspicious (bool), reason (str) — un résultat par transaction, même ordre.
    """
    results = []
    transactions = transactions or []
    profiles = _build_profiles(transactions)

    for index, transaction in enumerate(transactions, start=1):
        tx = transaction if isinstance(transaction, dict) else {}
        transaction_id = tx.get("transaction_id") or f"UNKNOWN-{index}"
        amount = tx.get("amount")
        profile = profiles.get((tx.get("user_id"), tx.get("currency")), {})
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
