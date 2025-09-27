
import math
from datetime import datetime

def parse_maturity_from_name(name:str):
    # naive parse "YYYY" at end, else None
    if not isinstance(name,str): return None
    for token in name.split():
        if token.isdigit() and len(token)==4:
            try:
                y=int(token)
                if 1900<y<2100:
                    return datetime(y,12,31)
            except:
                pass
    return None

def approx_ytm_simple(price_pct, coupon_pct, years_to_maturity):
    # Bond price in % of par, coupon in %, YTM approx formula
    # YTM ≈ (C + (100 - P)/n) / ((100 + P)/2)
    if years_to_maturity <= 0:
        return None
    return (coupon_pct + (100.0 - price_pct)/years_to_maturity) / ((100.0 + price_pct)/2.0)

def net_of_tax(gross_yield, gov=True):
    tax = 0.125 if gov else 0.26
    return gross_yield * (1 - tax)
