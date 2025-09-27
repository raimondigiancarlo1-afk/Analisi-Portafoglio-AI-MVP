
import pandas as pd

def basic_checks(df_port, client):
    notes = []
    # Example rule: liquidità < 20% se profilo non Prudente
    cash_pct = df_port.loc[df_port["asset_class"].str.lower().eq("liquidità") | df_port["type"].str.lower().eq("conto"), "market_value"].sum() / df_port["market_value"].sum()
    if client.get("risk_profile","").lower() != "prudente" and cash_pct > 0.20:
        notes.append(f"Liquidità al {cash_pct:.1%} superiore al 20% per profilo non prudente.")
    # Example rule: peso azionario entro limiti
    eq_pct = df_port.loc[df_port["asset_class"].str.contains("Azionario", case=False, na=False),"market_value"].sum()/df_port["market_value"].sum()
    if client.get("risk_profile","").lower() in ("prudente","conservativo") and eq_pct > 0.40:
        notes.append(f"Azionario al {eq_pct:.1%} eccessivo per profilo {client.get('risk_profile')}.")
    return notes

def margin_estimate(row, universali_margini):
    cat = row.get("asset_class","")
    match = universali_margini.loc[universali_margini["category"]==cat]
    if not match.empty:
        return float(match["value"].iloc[0]) / 10000.0  # convert bps to fraction
    # fallback to provided retro_mbps if present
    try:
        return float(row.get("retro_mbps",0))/10000.0
    except:
        return 0.0
