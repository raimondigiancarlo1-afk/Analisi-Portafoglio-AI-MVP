
import streamlit as st
import pandas as pd
from pathlib import Path
import yaml

from modules.rules import basic_checks, margin_estimate
from modules.optimizer import naive_target_allocation, aggregate_allocation, rebalance_suggestions
from modules.report import render_text_report, save_markdown_report
from modules.substitutions import suggest_substitutions
from modules.bonds import approx_ytm_simple, parse_maturity_from_name, net_of_tax
from modules.pdf import build_pdf

st.set_page_config(page_title="Analisi Portafoglio AI – MVP", layout="wide")

st.title("Analisi Portafoglio AI – MVP")

# Config
cfg_path = Path(__file__).parents[1] / "config" / "settings.yaml"
with open(cfg_path, "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)

col1, col2 = st.columns(2)
with col1:
    port_file = st.file_uploader("Portafoglio (Excel)", type=["xlsx"])
with col2:
    client_file = st.file_uploader("Profilo Cliente (Excel)", type=["xlsx"])

st.subheader("Universali")
u1 = st.file_uploader("Universali Fondi (Excel)", type=["xlsx"], key="u1")
u2 = st.file_uploader("Universali Gestioni (Excel)", type=["xlsx"], key="u2")
u3 = st.file_uploader("Universali Margini (Excel)", type=["xlsx"], key="u3")

if st.button("Usa dati di esempio"):
    sample_dir = Path(__file__).parents[1] / "data" / "samples"
    port_file = open(sample_dir / "portafoglio_sample.xlsx","rb")
    client_file = open(sample_dir / "cliente_sample.xlsx","rb")
    u1 = open(sample_dir / "universali_fondi.xlsx","rb")
    u2 = open(sample_dir / "universali_gestioni.xlsx","rb")
    u3 = open(sample_dir / "universali_margini.xlsx","rb")

if not (port_file and client_file and u3):
    st.info("Carica almeno Portafoglio, Profilo Cliente e Universali Margini.")
    st.stop()

df_port = pd.read_excel(port_file)
df_client = pd.read_excel(client_file).iloc[0].to_dict()
uni_margini = pd.read_excel(u3)

st.success("File caricati.")

# Marginalità stimata
df_port["advisor_margin_est"] = df_port.apply(lambda r: margin_estimate(r, uni_margini), axis=1)
df_port["advisor_margin_eur"] = df_port["advisor_margin_est"] * df_port["market_value"]

# Controlli base
issues = basic_checks(df_port, df_client)

# Allocazioni e suggerimenti
alloc_cur = aggregate_allocation(df_port)
alloc_tar = naive_target_allocation(df_client.get("risk_profile","Bilanciato"))
total_value = float(df_port["market_value"].sum())
actions = rebalance_suggestions(alloc_cur, alloc_tar, total_value)

st.subheader("Riepilogo chiave")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Totale Portafoglio", f"€ {total_value:,.0f}")
m2.metric("Margine stimato", f"€ {df_port['advisor_margin_eur'].sum():,.0f}")
m3.metric("Azionario attuale", f"{alloc_cur.get('Azionario',0)*100:.1f}%")
m4.metric("Obbligaz. attuale", f"{alloc_cur.get('Obbligazionario',0)*100:.1f}%")

st.subheader("Anomalie e Note di Compliance")
if issues:
    for n in issues:
        st.error(n)
else:
    st.write("Nessuna anomalia rilevata con le regole base.")

st.subheader("Suggerimenti di Ribilanciamento (bucket)")
st.dataframe(pd.DataFrame(actions))

st.subheader("Dettaglio posizioni")
st.dataframe(df_port)

# Report markdown esportabile
summary = {
    "Cliente": df_client.get("client_name"),
    "Profilo Rischio": df_client.get("risk_profile"),
    "Valore Totale": f"€ {total_value:,.0f}",
    "Margine Stimato": f"€ {df_port['advisor_margin_eur'].sum():,.0f}",
    "Allocazione Attuale": str(alloc_cur),
    "Allocazione Target": str(alloc_tar),
    "N° Note Compliance": len(issues)
}
md = render_text_report(summary)
out_dir = Path(__file__).parents[1] / "outputs"
out_dir.mkdir(exist_ok=True, parents=True)
md_path = out_dir / "report_portafoglio_MVP.md"
save_markdown_report(md_path, md)
st.download_button("Scarica report (Markdown)", data=open(md_path,"rb"), file_name="report_portafoglio_MVP.md", mime="text/markdown")


st.subheader("Sostituzioni automatiche (stessa categoria)")
u1_df = None
if u1:
    import pandas as pd
    u1_df = pd.read_excel(u1)
    subs = suggest_substitutions(df_port, u1_df, min_margin_improvement_bps=20, require_same_category=True)
    if not subs.empty:
        st.dataframe(subs)
    else:
        st.write("Nessuna sostituzione con miglioramento di margine rilevante.")

st.subheader("YTM Obbligazioni (stima netta)")
import numpy as np
bond_rows = []
for _, r in df_port.iterrows():
    if str(r.get("type","")).lower() in ("obbligazione","btp","bond") or "btp" in str(r.get("name","")).lower() or "obblig" in str(r.get("asset_class","")).lower():
        price_pct = float(r.get("price",0))  # se 'price' è in %, usa direttamente, altrimenti valuta input
        coupon = 0.0
        # prova a leggere 'coupon_pct' colonna opzionale, altrimenti parse dal nome "x.y%"
        if "coupon_pct" in df_port.columns:
            coupon = float(r.get("coupon_pct",0))
        else:
            name = str(r.get("name",""))
            if "%" in name:
                try:
                    token = name.split("%")[0].split()[-1].replace(",",".")
                    coupon = float(token)
                except:
                    coupon = 0.0
        mat = parse_maturity_from_name(str(r.get("name",""))) or None
        years = np.nan
        if mat is not None:
            from datetime import datetime
            years = max(0.0, (mat - datetime.today()).days/365.25)
        else:
            if "years_to_maturity" in df_port.columns:
                years = float(r.get("years_to_maturity",0))
        if years and years>0 and price_pct>0:
            ytm_gross = approx_ytm_simple(price_pct, coupon, years)
            is_gov = "btp" in str(r.get("name","")).lower()
            ytm_net = net_of_tax(ytm_gross, gov=is_gov)
            bond_rows.append({
                "name": r.get("name"),
                "coupon_pct": coupon,
                "price_pct": price_pct,
                "years_to_maturity": years,
                "ytm_gross_pct": ytm_gross*100 if ytm_gross is not None else None,
                "ytm_net_pct": ytm_net*100 if ytm_gross is not None else None,
                "gov_tax_12_5": is_gov
            })

if bond_rows:
    st.dataframe(pd.DataFrame(bond_rows))

# PDF export
st.subheader("Esporta PDF")
if st.button("Genera PDF riepilogo"):
    pdf_items = [
        f"Cliente: {df_client.get('client_name')}",
        f"Profilo rischio: {df_client.get('risk_profile')}",
        f"Valore totale: € {total_value:,.0f}",
        f"Margine stimato: € {df_port['advisor_margin_eur'].sum():,.0f}",
        f"Allocazione attuale: {alloc_cur}",
        f"Allocazione target: {alloc_tar}",
        f"Note compliance: {len(issues)}"
    ]
    if 'subs' in locals() and subs is not None and not subs.empty:
        pdf_items.append("Sostituzioni suggerite:")
        for _, rr in subs.iterrows():
            pdf_items.append(f"- {rr['current_name']} -> {rr['suggested_name']} (+{rr['suggested_margin_bps']-rr['current_margin_bps']:.0f} bps)")

    out_pdf = out_dir / "report_portafoglio_MVP.pdf"
    build_pdf(out_pdf, "Report Portafoglio – MVP", pdf_items)
    st.success("PDF generato.")
    st.download_button("Scarica PDF", data=open(out_pdf,"rb"), file_name="report_portafoglio_MVP.pdf", mime="application/pdf")

st.caption("MVP con sostituzioni, YTM netto e PDF.")
