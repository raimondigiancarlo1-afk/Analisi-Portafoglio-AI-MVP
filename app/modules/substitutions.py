
import pandas as pd

def prepare_universals_funds(df_uni):
    # expect columns: isin, name, category, k1,v1,k2,v2,k3,v3,k4,v4 where k2="retro_mbps", k3="rating_ms", k4="quartile"
    rows = []
    for _,r in df_uni.iterrows():
        d = {"isin":r["isin"],"name":r["name"],"category":r["category"]}
        for kf in [("k1","v1"),("k2","v2"),("k3","v3"),("k4","v4")]:
            k = str(r[kf[0]])
            v = r[kf[1]]
            if k and k != "nan":
                d[k]=v
        rows.append(d)
    return pd.DataFrame(rows)

def suggest_substitutions(df_port, df_uni, min_margin_improvement_bps=20, require_same_category=True):
    uni = prepare_universals_funds(df_uni)
    out = []
    for _,pos in df_port.iterrows():
        if pos.get("type","").lower() not in ("fondo","fondi","gestione"):
            continue
        cat = pos.get("asset_class","")
        if require_same_category and cat:
            pool = uni[uni["category"]==cat].copy()
        else:
            pool = uni.copy()
        # current metrics
        cur_margin = float(pos.get("retro_mbps",0))
        cur_rating = float(pos.get("rating_ms",0)) if "rating_ms" in pos else None
        cur_quart = float(pos.get("quartile",99)) if "quartile" in pos else None
        # score: prefer higher margin and rating, lower quartile
        def score(row):
            margin = float(row.get("retro_mbps",0))
            rating = float(row.get("rating_ms",0))
            quart = float(row.get("quartile",3))
            return (margin, rating, -quart)
        pool["__score"] = pool.apply(score, axis=1)
        pool = pool.sort_values(by="__score", ascending=False)
        if pool.empty:
            continue
        best = pool.iloc[0].to_dict()
        # Check improvement threshold
        if float(best.get("retro_mbps",0)) >= cur_margin + min_margin_improvement_bps:
            out.append({
                "current_name": pos.get("name"),
                "current_cat": cat,
                "current_margin_bps": cur_margin,
                "suggested_isin": best.get("isin"),
                "suggested_name": best.get("name"),
                "suggested_margin_bps": float(best.get("retro_mbps",0)),
                "rating_ms": best.get("rating_ms",None),
                "quartile": best.get("quartile",None),
                "est_annual_margin_delta_eur": (float(best.get("retro_mbps",0)) - cur_margin)/10000.0 * float(pos.get("market_value",0))
            })
    return pd.DataFrame(out)
