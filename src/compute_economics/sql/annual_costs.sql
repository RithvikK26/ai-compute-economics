-- Financial formulas live in Python. SQL reconciles the emitted category ledger.
SELECT policy_id, CASE WHEN period=0 THEN 1 ELSE CAST(ceil(period/12.0) AS INTEGER) END AS model_year,
       category,sum(cash_usd) AS cash_usd,sum(pv_usd) AS pv_usd,
       sum(CASE WHEN flow_kind='operating' THEN cash_usd ELSE 0 END) AS operating_cash_usd
FROM ledger
GROUP BY policy_id,model_year,category
ORDER BY policy_id,model_year,category
