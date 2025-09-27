
import pandas as pd

def naive_target_allocation(risk_profile:str):
    # Simple target by profile
    rp = risk_profile.lower()
    if rp in ("prudente","conservativo"):
        return {"Azionario":0.25,"Obbligazionario":0.55,"Liquidità":0.20}
    if rp in ("bilanciato","moderato"):
        return {"Azionario":0.50,"Obbligazionario":0.40,"Liquidità":0.10}
    return {"Azionario":0.70,"Obbligazionario":0.25,"Liquidità":0.05}

def aggregate_allocation(df_port):
    def bucket(row):
        if "azionario" in row["asset_class"].lower(): return "Azionario"
        if "obbligazionario" in row["asset_class"].lower() or "btp" in row["name"].lower(): return "Obbligazionario"
        if "conto" in row["type"].lower() or "liquid" in row["asset_class"].lower(): return "Liquidità"
        if "polizza" in row["type"].lower(): return "Stabilizzanti"
        if "pensione" in row["type"].lower(): return "Previdenza"
        if "gestione" in row["type"].lower(): return "Gestione"
        return "Altro"
    df = df_port.copy()
    df["bucket"] = df.apply(bucket, axis=1)
    agg = df.groupby("bucket")["market_value"].sum()
    total = agg.sum()
    return (agg/total).to_dict()

def rebalance_suggestions(current_alloc:dict, target_alloc:dict, total_value:float, threshold=0.03):
    actions = []
    keys = set(current_alloc.keys()) | set(target_alloc.keys())
    for k in keys:
        cur = current_alloc.get(k,0.0)
        tar = target_alloc.get(k,0.0)
        gap = tar - cur
        if abs(gap) >= threshold:
            euro = gap * total_value
            actions.append({"bucket":k,"delta_pct":gap,"delta_eur":euro})
    return actions
