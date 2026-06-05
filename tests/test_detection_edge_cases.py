from fraud_detection import detect_fraud


def tx(
    tid,
    user="U1",
    amount=50.0,
    country="FR",
    ts="2025-06-01T10:00:00Z",
    currency="EUR",
    merchant="Cafe",
    card_present=True,
):
    return {
        "transaction_id": tid,
        "timestamp": ts,
        "user_id": user,
        "amount": amount,
        "currency": currency,
        "merchant": merchant,
        "country": country,
        "card_present": card_present,
    }


def by_id(results):
    return {result["transaction_id"]: result for result in results}


def test_montant_non_numerique_est_signale_sans_crash():
    result = detect_fraud([tx("T1", amount="erreur")])[0]

    assert result["is_suspicious"] is True
    assert result["fraud_score"] > 0
    assert "amount" in result["reason"]


def test_devise_en_minuscules_garde_le_profil_client():
    transactions = [
        tx(f"H{i}", amount=40.0, currency="eur", ts=f"2025-05-0{i}T10:00:00Z")
        for i in range(1, 5)
    ]
    transactions.append(tx("T1", amount=1000.0, currency="EUR"))

    result = by_id(detect_fraud(transactions))

    assert result["T1"]["is_suspicious"] is True


def test_changement_de_pays_ignore_la_casse():
    transactions = [
        tx("T1", country="fr", ts="2025-06-01T10:00:00Z"),
        tx("T2", country="FR", ts="2025-06-01T10:30:00Z"),
    ]

    result = by_id(detect_fraud(transactions))

    assert result["T1"]["is_suspicious"] is False
    assert result["T2"]["is_suspicious"] is False


def test_frequence_de_transactions_rapprochees_est_signalee():
    transactions = [
        tx("T1", ts="2025-06-01T10:00:00Z"),
        tx("T2", ts="2025-06-01T10:03:00Z"),
        tx("T3", ts="2025-06-01T10:06:00Z"),
        tx("T4", ts="2025-06-01T10:09:00Z"),
    ]

    result = by_id(detect_fraud(transactions))

    assert result["T1"]["is_suspicious"] is True
    assert result["T4"]["is_suspicious"] is True


def test_voyage_legitime_apres_plusieurs_jours_non_suspect():
    transactions = [
        tx("T1", country="FR", ts="2025-06-01T10:00:00Z"),
        tx("T2", country="US", ts="2025-06-05T10:00:00Z"),
    ]

    result = by_id(detect_fraud(transactions))

    assert result["T1"]["is_suspicious"] is False
    assert result["T2"]["is_suspicious"] is False


def test_identifiant_duplique_est_signale():
    result = detect_fraud([tx("DUP-1"), tx("DUP-1", ts="2025-06-02T10:00:00Z")])

    assert result[0]["is_suspicious"] is True
    assert result[1]["is_suspicious"] is True
