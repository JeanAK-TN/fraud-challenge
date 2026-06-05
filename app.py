"""
Interface Streamlit - personnalisee pour le jury.

Le jury lancera :  streamlit run app.py

Règles :
  - Ne modifiez pas l'appel à detect_fraud / load_transactions (contrat technique).
  - Personnalisez render_interface() : clarté, intuitivité, compréhension pour un public non technique.
  - L'interface n'est PAS notée par la CI ; elle sert au jury pour repêcher et comparer les candidats.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from fraud_detection import detect_fraud, load_transactions

SAMPLE_CSV = Path(__file__).parent / "data" / "sample_transactions.csv"


def render_interface(transactions: list[dict], results: list[dict]) -> None:
    tx_df = pd.DataFrame(transactions)
    result_df = pd.DataFrame(results)
    if tx_df.empty or result_df.empty:
        st.info("Aucune transaction à afficher.")
        return

    df = pd.concat([tx_df, result_df.drop(columns=["transaction_id"])], axis=1)
    df["fraud_score"] = pd.to_numeric(df["fraud_score"], errors="coerce").fillna(0.0)
    df["niveau"] = pd.cut(
        df["fraud_score"],
        bins=[-0.01, 0.39, 0.69, 1.0],
        labels=["Faible", "Moyen", "Élevé"],
    )

    total = len(df)
    suspicious = int(df["is_suspicious"].sum())
    average_score = float(df["fraud_score"].mean())
    top_score = float(df["fraud_score"].max())

    st.subheader("Vue d'ensemble")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Transactions", total)
    col2.metric("Alertes", suspicious)
    col3.metric("Risque moyen", f"{average_score:.2f}")
    col4.metric("Risque maximum", f"{top_score:.2f}")

    st.divider()

    filter_col, user_col, level_col = st.columns([1, 1, 1])
    with filter_col:
        only_alerts = st.toggle("Afficher seulement les alertes", value=False)
    with user_col:
        users = sorted(str(user) for user in df["user_id"].dropna().unique())
        selected_user = st.selectbox("Client", ["Tous"] + users)
    with level_col:
        selected_level = st.selectbox("Niveau de risque", ["Tous", "Élevé", "Moyen", "Faible"])

    filtered = df.copy()
    if only_alerts:
        filtered = filtered[filtered["is_suspicious"]]
    if selected_user != "Tous":
        filtered = filtered[filtered["user_id"].astype(str) == selected_user]
    if selected_level != "Tous":
        filtered = filtered[filtered["niveau"].astype(str) == selected_level]

    if filtered.empty:
        st.info("Aucune transaction ne correspond aux filtres sélectionnés.")
        return

    chart_col, reason_col = st.columns([1, 1])
    with chart_col:
        st.subheader("Risque par transaction")
        chart_df = filtered[["transaction_id", "fraud_score"]].set_index("transaction_id")
        st.bar_chart(chart_df, use_container_width=True)
    with reason_col:
        st.subheader("Principales raisons")
        reason_counts = filtered["reason"].value_counts().rename_axis("raison").reset_index(name="nombre")
        st.dataframe(reason_counts, use_container_width=True, hide_index=True)

    st.subheader("Transactions analysées")
    display_columns = [
        "transaction_id",
        "user_id",
        "timestamp",
        "amount",
        "currency",
        "merchant",
        "country",
        "card_present",
        "fraud_score",
        "niveau",
        "is_suspicious",
        "reason",
    ]
    existing_columns = [column for column in display_columns if column in filtered.columns]
    st.dataframe(
        filtered[existing_columns].sort_values("fraud_score", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    alerts = filtered[filtered["is_suspicious"]].sort_values("fraud_score", ascending=False)
    if not alerts.empty:
        st.subheader("Détail des alertes")
        for alert in alerts.head(5).to_dict("records"):
            st.markdown(
                f"**{alert.get('transaction_id')}** · client `{alert.get('user_id')}` · "
                f"score `{alert.get('fraud_score'):.2f}`"
            )
            st.caption(alert.get("reason", "Raison non disponible"))


def main() -> None:
    st.set_page_config(
        page_title="Détection de fraude - Hackathon INTELO2026",
        page_icon="🛡️",
        layout="wide",
    )

    st.title("Détection de fraude financière")
    st.caption("Hackathon INTELO2026 - interface participant · évaluée par le jury")

    with st.sidebar:
        st.header("Charger des données")
        use_sample = st.toggle("Utiliser le fichier d'exemple", value=True)
        transactions: list[dict] = []

        if use_sample:
            transactions = load_transactions(str(SAMPLE_CSV))
            st.success(f"{len(transactions)} transactions (exemple)")
        else:
            uploaded = st.file_uploader("Importer un CSV", type=["csv"])
            if uploaded:
                tmp = Path(".streamlit_upload.csv")
                tmp.write_bytes(uploaded.getvalue())
                transactions = load_transactions(str(tmp))
                tmp.unlink(missing_ok=True)
                st.success(f"{len(transactions)} transactions importées")

        st.divider()
        st.markdown(
            "**Jury :** évaluez l'ergonomie et la clarté de l'écran principal, "
            "pas seulement le score des tests."
        )

    if not transactions:
        st.info("Chargez des transactions (barre latérale) puis lancez l'analyse.")
        return

    if st.button("Analyser", type="primary"):
        try:
            results = detect_fraud(transactions)
        except NotImplementedError:
            st.error("Implémentez d'abord `detect_fraud` dans `fraud_detection.py`.")
            return
        except Exception as exc:
            st.error(f"Erreur : {exc}")
            return

        render_interface(transactions, results)


if __name__ == "__main__":
    main()
