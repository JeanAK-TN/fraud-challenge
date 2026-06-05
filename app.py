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

# Palette par niveau de risque : vert (sûr) -> ambre (à surveiller) -> rouge (alerte).
LEVEL_COLORS = {
    "Faible": "#22c55e",
    "Moyen": "#f59e0b",
    "Élevé": "#ef4444",
}
LEVEL_EMOJI = {"Faible": "🟢", "Moyen": "🟠", "Élevé": "🔴"}

# Variables CSS adaptées au thème actif. Les couleurs de marque et de risque
# restent identiques (elles tiennent sur fond clair comme sombre) ; seules les
# surfaces, lignes et couleurs de texte changent.
_THEME_VARS = {
    "light": {
        "elev": "#ffffff",
        "soft": "#f1f5f9",
        "ink": "#0f172a",
        "ink-soft": "#64748b",
        "line": "#e2e8f0",
        "track": "#e9eef5",
        "shadow": "0 12px 28px -22px rgba(15, 23, 42, 0.55)",
    },
    "dark": {
        "elev": "#161b27",
        "soft": "#0f1420",
        "ink": "#f1f5f9",
        "ink-soft": "#94a3b8",
        "line": "#283142",
        "track": "#1f2738",
        "shadow": "0 12px 28px -18px rgba(0, 0, 0, 0.7)",
    },
}


def _transactions_key(transactions: list[dict]) -> tuple:
    key = []
    for transaction in transactions:
        if not isinstance(transaction, dict):
            key.append(("invalid",))
            continue

        key.append(
            (
                transaction.get("transaction_id"),
                transaction.get("timestamp"),
                transaction.get("user_id"),
                transaction.get("amount"),
                transaction.get("currency"),
                transaction.get("merchant"),
                transaction.get("country"),
                transaction.get("card_present"),
            )
        )

    return tuple(key)


def _theme_type() -> str:
    """Renvoie 'light' ou 'dark' selon le thème Streamlit actif (toggle in-app)."""
    try:
        detected = st.context.theme.get("type")
    except Exception:
        detected = None
    return detected if detected in ("light", "dark") else "light"


def _vars_block(theme: str) -> str:
    return "".join(f"--{name}:{value};" for name, value in _THEME_VARS[theme].items())


def _inject_styles() -> None:
    """Identité visuelle : surfaces theme-aware, cartes, dégradés, badges."""
    detected = _theme_type()
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&display=swap');

        /* Base claire, puis surcharge sombre selon l'OS, puis valeur autoritaire
           detectee cote Python (suit le toggle clair/sombre de Streamlit). */
        :root {{ {_vars_block("light")} }}
        @media (prefers-color-scheme: dark) {{ :root {{ {_vars_block("dark")} }} }}
        :root {{ {_vars_block(detected)} }}

        :root {{
            --brand: #7c3aed;
            --brand-2: #4f46e5;
            --radius: 16px;
        }}

        .block-container {{ padding-top: 1.4rem; max-width: 1160px; }}

        /* Eyebrow + titres : police geometrique pour l'identite. */
        .eyebrow {{
            font-family: 'Space Grotesk', system-ui, sans-serif;
            text-transform: uppercase; letter-spacing: 2px;
            font-size: 0.72rem; font-weight: 600; color: var(--brand);
            display: flex; align-items: center; gap: 8px; margin: 4px 0 10px;
        }}
        .eyebrow::before {{ content: ""; width: 22px; height: 3px; border-radius: 3px;
            background: linear-gradient(90deg, var(--brand), var(--brand-2)); }}

        /* En-tête héro. */
        .hero {{
            position: relative; overflow: hidden;
            background: linear-gradient(120deg, #4f46e5 0%, #7c3aed 52%, #6366f1 100%);
            border-radius: 22px; padding: 28px 32px; color: #fff;
            box-shadow: 0 22px 50px -24px rgba(79, 70, 229, 0.75);
        }}
        .hero::after {{
            content: ""; position: absolute; top: -60%; right: -10%;
            width: 320px; height: 320px; border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.22), transparent 65%);
        }}
        .hero h1 {{ font-family: 'Space Grotesk', system-ui, sans-serif;
            margin: 0; font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }}
        .hero p {{ margin: 8px 0 0; opacity: 0.94; font-size: 1rem; max-width: 640px; }}
        .hero .pill {{
            display: inline-block; margin-top: 16px; padding: 6px 15px;
            background: rgba(255, 255, 255, 0.16); border: 1px solid rgba(255,255,255,0.28);
            border-radius: 999px; font-size: 0.78rem; font-weight: 600; letter-spacing: 0.3px;
        }}

        /* Cartes d'indicateurs (KPI). */
        .kpi {{
            background: var(--elev); border: 1px solid var(--line);
            border-left: 4px solid var(--accent, var(--brand));
            border-radius: var(--radius); padding: 18px 20px; height: 100%;
            box-shadow: var(--shadow);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        .kpi:hover {{ transform: translateY(-3px); box-shadow: 0 20px 34px -22px rgba(79,70,229,0.45); }}
        .kpi .label {{ color: var(--ink-soft); font-size: 0.78rem; font-weight: 600;
            text-transform: uppercase; letter-spacing: 0.6px; display: flex; gap: 7px; align-items: center; }}
        .kpi .value {{ font-family: 'Space Grotesk', system-ui, sans-serif;
            color: var(--ink); font-size: 2.05rem; font-weight: 700; line-height: 1.1; margin-top: 8px; }}
        .kpi .sub {{ color: var(--ink-soft); font-size: 0.78rem; margin-top: 4px; }}

        /* Barres de répartition du risque. */
        .dist-row {{ display: flex; align-items: center; gap: 12px; margin: 9px 0; }}
        .dist-name {{ width: 92px; font-weight: 600; font-size: 0.9rem; color: var(--ink); }}
        .dist-track {{ flex: 1; background: var(--track); border-radius: 999px; height: 13px; overflow: hidden; }}
        .dist-fill {{ height: 100%; border-radius: 999px; transition: width 0.45s ease; }}
        .dist-count {{ width: 40px; text-align: right; font-weight: 700; color: var(--ink);
            font-variant-numeric: tabular-nums; }}

        /* Cartes d'alerte. */
        .alert-card {{
            background: var(--elev); border: 1px solid var(--line);
            border-left: 5px solid var(--accent, #ef4444);
            border-radius: 14px; padding: 16px 18px; margin-bottom: 12px;
            box-shadow: var(--shadow);
        }}
        .alert-head {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }}
        .alert-id {{ font-family: 'Space Grotesk', system-ui, sans-serif;
            font-weight: 700; color: var(--ink); font-size: 1.05rem; }}
        .alert-meta {{ color: var(--ink-soft); font-size: 0.85rem; margin-top: 2px; }}
        .alert-reason {{ margin-top: 9px; color: var(--ink); font-size: 0.92rem; }}
        .score-badge {{
            color: #fff; font-weight: 700; padding: 4px 13px; border-radius: 999px;
            font-size: 0.85rem; white-space: nowrap;
            font-family: 'Space Grotesk', system-ui, sans-serif;
        }}
        .gauge-track {{ background: var(--track); border-radius: 999px; height: 7px; margin-top: 11px; overflow: hidden; }}
        .gauge-fill {{ height: 100%; border-radius: 999px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _eyebrow(text: str) -> None:
    st.markdown(f'<div class="eyebrow">{text}</div>', unsafe_allow_html=True)


def _risk_accent(score: float) -> str:
    if score >= 0.7:
        return LEVEL_COLORS["Élevé"]
    if score >= 0.4:
        return LEVEL_COLORS["Moyen"]
    return LEVEL_COLORS["Faible"]


def _kpi_card(label: str, value: str, icon: str, sub: str, accent: str) -> str:
    return (
        f'<div class="kpi" style="--accent:{accent}">'
        f'<div class="label">{icon} {label}</div>'
        f'<div class="value">{value}</div>'
        f'<div class="sub">{sub}</div>'
        f"</div>"
    )


def _risk_distribution(df: pd.DataFrame) -> None:
    _eyebrow("Répartition du risque")
    total = max(len(df), 1)
    counts = df["niveau"].value_counts()
    for level in ("Élevé", "Moyen", "Faible"):
        count = int(counts.get(level, 0))
        pct = count / total * 100
        color = LEVEL_COLORS[level]
        st.markdown(
            f'<div class="dist-row">'
            f'<div class="dist-name">{LEVEL_EMOJI[level]} {level}</div>'
            f'<div class="dist-track"><div class="dist-fill" '
            f'style="width:{pct:.0f}%;background:{color}"></div></div>'
            f'<div class="dist-count">{count}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )


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
    alert_rate = suspicious / total * 100 if total else 0.0

    # --- Indicateurs clés -------------------------------------------------
    _eyebrow("Vue d'ensemble")
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(
        _kpi_card("Transactions", f"{total}", "🧾", "analysées dans ce lot", "#4f46e5"),
        unsafe_allow_html=True,
    )
    k2.markdown(
        _kpi_card("Alertes", f"{suspicious}", "🚨", f"{alert_rate:.0f}% du volume", "#ef4444"),
        unsafe_allow_html=True,
    )
    k3.markdown(
        _kpi_card("Risque moyen", f"{average_score:.2f}", "📊", "score moyen /1.00", "#f59e0b"),
        unsafe_allow_html=True,
    )
    k4.markdown(
        _kpi_card("Risque maximum", f"{top_score:.2f}", "🔺", "transaction la plus risquée", _risk_accent(top_score)),
        unsafe_allow_html=True,
    )

    st.write("")
    _risk_distribution(df)
    st.divider()

    # --- Filtres ----------------------------------------------------------
    _eyebrow("Explorer les transactions")
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

    chart_col, reason_col = st.columns([1.15, 1])
    with chart_col:
        st.markdown("##### Risque par transaction")
        chart_df = filtered[["transaction_id", "fraud_score"]].set_index("transaction_id")
        st.bar_chart(chart_df, width="stretch", color="#7c3aed")
    with reason_col:
        st.markdown("##### Principales raisons")
        reason_counts = filtered["reason"].value_counts().rename_axis("raison").reset_index(name="nombre")
        st.dataframe(
            reason_counts,
            width="stretch",
            hide_index=True,
            column_config={
                "raison": st.column_config.TextColumn("Raison détectée"),
                "nombre": st.column_config.NumberColumn("Occurrences", format="%d"),
            },
        )

    # --- Détail des alertes en cartes lisibles ----------------------------
    alerts = filtered[filtered["is_suspicious"]].sort_values("fraud_score", ascending=False)
    if not alerts.empty:
        _eyebrow("Alertes prioritaires")
        st.caption("Les transactions les plus risquées, expliquées en clair.")
        for alert in alerts.head(6).to_dict("records"):
            score = float(alert.get("fraud_score", 0.0))
            color = _risk_accent(score)
            amount = alert.get("amount")
            amount_txt = (
                f"{amount:,.2f} {alert.get('currency') or ''}".strip()
                if isinstance(amount, (int, float))
                else "—"
            )
            merchant = alert.get("merchant") or "Marchand inconnu"
            country = alert.get("country") or "??"
            st.markdown(
                f'<div class="alert-card" style="--accent:{color}">'
                f'<div class="alert-head">'
                f'<span class="alert-id">{alert.get("transaction_id")}</span>'
                f'<span class="score-badge" style="background:{color}">Score {score:.2f}</span>'
                f"</div>"
                f'<div class="alert-meta">👤 Client <b>{alert.get("user_id")}</b> · '
                f'💳 {amount_txt} · 🏬 {merchant} · 🌍 {country}</div>'
                f'<div class="alert-reason">⚠️ {alert.get("reason", "Raison non disponible")}</div>'
                f'<div class="gauge-track"><div class="gauge-fill" '
                f'style="width:{score * 100:.0f}%;background:{color}"></div></div>'
                f"</div>",
                unsafe_allow_html=True,
            )

    # --- Tableau détaillé -------------------------------------------------
    _eyebrow("Toutes les transactions analysées")
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
    table = filtered[existing_columns].sort_values("fraud_score", ascending=False)
    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        column_config={
            "transaction_id": st.column_config.TextColumn("ID"),
            "user_id": st.column_config.TextColumn("Client"),
            "timestamp": st.column_config.TextColumn("Horodatage"),
            "amount": st.column_config.NumberColumn("Montant", format="%.2f"),
            "currency": st.column_config.TextColumn("Devise"),
            "merchant": st.column_config.TextColumn("Marchand"),
            "country": st.column_config.TextColumn("Pays"),
            "card_present": st.column_config.CheckboxColumn("Carte présente"),
            "fraud_score": st.column_config.ProgressColumn(
                "Score de risque", min_value=0.0, max_value=1.0, format="%.2f"
            ),
            "niveau": st.column_config.TextColumn("Niveau"),
            "is_suspicious": st.column_config.CheckboxColumn("Suspecte"),
            "reason": st.column_config.TextColumn("Explication", width="large"),
        },
    )

    csv_bytes = table.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Exporter les résultats (CSV)",
        data=csv_bytes,
        file_name="resultats_fraude.csv",
        mime="text/csv",
    )


def main() -> None:
    st.set_page_config(
        page_title="Détection de fraude - Hackathon INTELO2026",
        page_icon="🛡️",
        layout="wide",
    )
    _inject_styles()

    st.markdown(
        """
        <div class="hero">
            <h1>🛡️ Sentinelle anti-fraude</h1>
            <p>Détection intelligente des transactions financières suspectes — claire, visuelle et explicable.</p>
            <span class="pill">Hackathon INTELO2026 · interface participant · évaluée par le jury</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    with st.sidebar:
        st.header("⚙️ Source de données")
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
        st.markdown("##### 🧭 Comment lire les scores ?")
        st.markdown(
            f"{LEVEL_EMOJI['Faible']} **Faible** — conforme au profil (0.00 – 0.39)  \n"
            f"{LEVEL_EMOJI['Moyen']} **Moyen** — à surveiller (0.40 – 0.69)  \n"
            f"{LEVEL_EMOJI['Élevé']} **Élevé** — alerte forte (0.70 – 1.00)"
        )
        st.divider()
        st.caption(
            "Jury : évaluez l'ergonomie et la clarté de l'écran principal, "
            "pas seulement le score des tests."
        )

    if not transactions:
        st.info("👈 Chargez des transactions dans la barre latérale, puis lancez l'analyse.")
        st.session_state.pop("analysis_key", None)
        st.session_state.pop("analysis_results", None)
        return

    current_key = _transactions_key(transactions)
    cta_col, _ = st.columns([1, 3])
    with cta_col:
        run = st.button("🔍 Analyser les transactions", type="primary", width="stretch")

    if run:
        try:
            results = detect_fraud(transactions)
        except NotImplementedError:
            st.error("Implémentez d'abord `detect_fraud` dans `fraud_detection.py`.")
            return
        except Exception as exc:
            st.error(f"Erreur : {exc}")
            return

        st.session_state["analysis_key"] = current_key
        st.session_state["analysis_results"] = results

    saved_key = st.session_state.get("analysis_key")
    saved_results = st.session_state.get("analysis_results")

    if saved_key == current_key and saved_results is not None:
        render_interface(transactions, saved_results)
    else:
        st.info("Cliquez sur **Analyser les transactions** pour afficher les résultats.")


if __name__ == "__main__":
    main()
