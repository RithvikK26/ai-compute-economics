-- Deduplicate within exact region, configuration and billing/product boundary.
WITH ranked AS (
 SELECT o.*, s.url, s.license_note,
        row_number() OVER (PARTITION BY configuration_id, region, pricing_kind, raw_unit
                           ORDER BY observed_at DESC, offer_id) AS recency
 FROM offers o JOIN sources s USING(source_id)
 WHERE CAST(observed_at AS TIMESTAMPTZ)::DATE <= CAST($cutoff AS DATE)
   AND region=$region AND currency='USD' AND pricing_kind='on_demand'
   AND raw_unit='USD/node-hour' AND price_component='complete_node'
   AND node_hour_price IS NOT NULL AND admission_status IN ('eligible','conditional')
   AND o.artifact_hash <> ''
)
SELECT r.*, c.family, c.gpu_count AS configuration_gpu_count,
       date_diff('day', CAST(observed_at AS TIMESTAMPTZ)::DATE, CAST($cutoff AS DATE))>30 AS stale
FROM ranked r JOIN configurations c USING(configuration_id)
WHERE recency=1 AND ($historical OR $acknowledged OR
 date_diff('day', CAST(observed_at AS TIMESTAMPTZ)::DATE, CAST($cutoff AS DATE))<=30)
ORDER BY configuration_id
