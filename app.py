"""
Interface de démonstration — à lancer pour montrer vos résultats au jury / au public.

    streamlit run app.py

Vous n'avez pas à recoder toute l'interface : concentrez-vous sur detect_fraud.
Vous pouvez personnaliser ce fichier en bonus (graphiques, couleurs, explications).
"""

from pathlib import Path

import streamlit as st

from fraud_detection import detect_fraud, load_transactions

SAMPLE_CSV = Path(__file__).parent / "data" / "sample_transactions.csv"


st.set_page_config(
    page_title="Détection de fraude — Hackathon INTELO2026",
    page_icon="🛡️",
    layout="wide",
)

st.title("Détection de fraude financière")
st.caption(
    "Hackathon INTELO2026 — visualisation des résultats produits par votre moteur `detect_fraud`."
)

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Données")
    source = st.radio(
        "Source des transactions",
        ["Fichier d'exemple (fourni)", "Importer un CSV"],
        horizontal=True,
    )

    transactions = []
    if source.startswith("Fichier"):
        transactions = load_transactions(str(SAMPLE_CSV))
        st.success(f"{len(transactions)} transactions chargées depuis `data/sample_transactions.csv`.")
    else:
        uploaded = st.file_uploader("Fichier CSV (même format que l'épreuve)", type=["csv"])
        if uploaded:
            tmp = Path(".streamlit_upload.csv")
            tmp.write_bytes(uploaded.getvalue())
            transactions = load_transactions(str(tmp))
            tmp.unlink(missing_ok=True)
            st.success(f"{len(transactions)} transactions importées.")

with col_right:
    st.subheader("Aperçu des transactions")
    if transactions:
        st.dataframe(transactions, use_container_width=True, height=280)
    else:
        st.info("Chargez des transactions pour commencer.")

st.divider()

if st.button("Analyser les transactions", type="primary", disabled=not transactions):
    try:
        results = detect_fraud(transactions)
    except NotImplementedError:
        st.error(
            "La fonction `detect_fraud` n'est pas encore implémentée. "
            "Complétez `fraud_detection.py`, puis relancez cette page."
        )
        st.stop()
    except Exception as exc:
        st.error(f"Erreur lors de l'analyse : {exc}")
        st.stop()

    if len(results) != len(transactions):
        st.warning(
            f"Attention : {len(results)} résultat(s) pour {len(transactions)} transaction(s). "
            "Vérifiez que vous renvoyez un verdict par transaction."
        )

    suspicious = [r for r in results if r.get("is_suspicious")]
    scores = [r.get("fraud_score", 0) for r in results if isinstance(r.get("fraud_score"), (int, float))]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Transactions analysées", len(results))
    m2.metric("Alertes fraude", len(suspicious))
    m3.metric("Transactions OK", len(results) - len(suspicious))
    m4.metric(
        "Score moyen",
        f"{(sum(scores) / len(scores)):.2f}" if scores else "—",
        help="Moyenne des fraud_score (0 = sûr, 1 = très suspect)",
    )

    st.subheader("Résultats détaillés")
    st.caption("Lignes en rouge = transaction signalée comme suspecte.")

    rows = []
    tx_by_id = {t.get("transaction_id"): t for t in transactions}
    for r in results:
        tid = r.get("transaction_id")
        t = tx_by_id.get(tid, {})
        rows.append({
            "ID": tid,
            "Client": t.get("user_id"),
            "Montant": t.get("amount"),
            "Pays": t.get("country"),
            "Commerçant": t.get("merchant"),
            "Score fraude": r.get("fraud_score"),
            "Suspect ?": "OUI" if r.get("is_suspicious") else "non",
            "Explication": r.get("reason", ""),
        })

    def _highlight(row):
        if row["Suspect ?"] == "OUI":
            return ["background-color: #3d1515; color: #ffe0e0"] * len(row)
        return ["background-color: #14261a; color: #d8ffe8"] * len(row)

    try:
        import pandas as pd

        df = pd.DataFrame(rows)
        st.dataframe(
            df.style.apply(_highlight, axis=1),
            use_container_width=True,
            height=400,
        )
    except ImportError:
        st.dataframe(rows, use_container_width=True, height=400)

    with st.expander("Voir le détail technique (JSON)"):
        st.json(results)

st.markdown("---")
st.markdown(
    "**Pour le jury :** lancez `streamlit run app.py` sur le poste du participant. "
    "**Pour la note :** seuls les tests automatiques (`pytest` / CI) comptent ; "
    "l'interface sert à rendre la démo compréhensible."
)
