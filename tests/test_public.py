"""
Tests PUBLICS — visibles par les participants et exécutés en CI.

pytest tests/
"""

from fraud_detection import detect_fraud


def _index(results):
    return {r["transaction_id"]: r for r in results}


def tx(tid, user="U1", amount=50.0, country="FR", ts="2025-06-01T10:00:00Z",
       currency="EUR", merchant="Cafe", card_present=True):
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


# NIVEAU 1 — Format
def test_retourne_une_liste():
    res = detect_fraud([tx("T1")])
    assert isinstance(res, list)


def test_un_resultat_par_transaction():
    res = detect_fraud([tx("T1"), tx("T2"), tx("T3")])
    assert len(res) == 3


def test_cles_presentes():
    res = detect_fraud([tx("T1")])[0]
    for cle in ("transaction_id", "fraud_score", "is_suspicious", "reason"):
        assert cle in res, f"clé manquante: {cle}"


def test_score_entre_0_et_1():
    for r in detect_fraud([tx("T1"), tx("T2", amount=-5)]):
        assert 0.0 <= r["fraud_score"] <= 1.0, (
            f"attendu un score entre 0 et 1, reçu {r['fraud_score']}"
        )


def test_types_de_sortie():
    r = detect_fraud([tx("T1")])[0]
    assert isinstance(r["fraud_score"], (int, float))
    assert isinstance(r["is_suspicious"], bool)
    assert isinstance(r["reason"], str) and len(r["reason"]) > 0


def test_identifiant_preserve():
    res = _index(detect_fraud([tx("ABC-123")]))
    assert "ABC-123" in res


# NIVEAU 1 — Anomalies évidentes
def test_montant_negatif_suspect():
    res = _index(detect_fraud([tx("T1", amount=-100.0)]))
    assert res["T1"]["is_suspicious"] is True


def test_montant_nul_suspect():
    res = _index(detect_fraud([tx("T1", amount=0.0)]))
    assert res["T1"]["is_suspicious"] is True


def test_ne_plante_pas_sur_champ_manquant():
    incomplete = tx("T1")
    incomplete["amount"] = None
    incomplete["country"] = None
    res = detect_fraud([incomplete])
    assert len(res) == 1


# NIVEAU 2 (aperçu public)
def test_transaction_normale_non_suspecte():
    historique = [tx(f"H{i}", amount=50.0, ts=f"2025-05-0{i}T10:00:00Z")
                  for i in range(1, 6)]
    courante = tx("T1", amount=55.0, ts="2025-06-01T10:00:00Z")
    res = _index(detect_fraud(historique + [courante]))
    assert res["T1"]["is_suspicious"] is False


def test_montant_tres_eleve_suspect():
    historique = [tx(f"H{i}", amount=50.0, ts=f"2025-05-0{i}T10:00:00Z")
                  for i in range(1, 6)]
    enorme = tx("T1", amount=5000.0, ts="2025-06-01T10:00:00Z")
    res = _index(detect_fraud(historique + [enorme]))
    assert res["T1"]["is_suspicious"] is True
