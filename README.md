
# Analisi Portafoglio AI – MVP

Obiettivo: caricare portafoglio + profilo cliente + universali margini e ottenere:
- Controlli base rispetto al profilo
- Stima marginalità promotore
- Allocazione attuale vs target per profilo
- Suggerimenti di ribilanciamento
- Report markdown scaricabile

## Avvio rapido (Streamlit Cloud o locale)

**Locale**
```bash
pip install -r requirements.txt
streamlit run app/app.py
```

**Streamlit Cloud**
- Crea nuovo repo GitHub con questa struttura.
- In "Advanced settings" imposta `main file path`: `app/app.py`.

## Input attesi

- `portafoglio_sample.xlsx`: colonne minime:
  - security_id, type, asset_class, name, currency, qty, price, market_value, account, retro_mbps, cost_mbps, risk_bucket
- `cliente_sample.xlsx`: singola riga con:
  - client_id, client_name, risk_profile, horizon, loss_capacity, saving_capacity, goals, max_drawdown_tolerance, themes, country
- `universali_margini.xlsx`: colonne:
  - category, type, metric, value

## Estensioni previste
- Rating e quartili Morningstar per fondi.
- YTM, duration, rating per obbligazioni.
- Analisi tecnica base (RSI, momentum) per azioni.
- Modulo **sostituzioni** con filtro per marginalità >= soglia e stessa categoria.
- Generazione **PDF** formattato e **Excel** con proposta vs attuale.
- Modulo **compliance** AML/MiFID con regole avanzate.
- Motore di **stress test** e scenario macro.
- Job di **monitoraggio periodico** con alert.

## Licenza
Uso interno MVP.
