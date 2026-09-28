-- Select one exact workload before joining; do not multiply costs by benchmarks.
SELECT c.configuration_id,c.family,o.node_hour_price,b.benchmark_id,b.value AS tokens_s,
       x.match_level,x.differences,
       CASE WHEN c.status='catalog_only' THEN 'catalog_only'
            WHEN o.node_hour_price IS NULL THEN 'missing_price'
            WHEN b.benchmark_id IS NULL THEN 'missing_compatible_performance'
            ELSE 'conditional' END AS evidence_status
FROM configurations c
LEFT JOIN (SELECT * FROM offers WHERE region=$region AND pricing_kind='on_demand'
 AND currency='USD' AND raw_unit='USD/node-hour'
 QUALIFY row_number() OVER(PARTITION BY configuration_id ORDER BY observed_at DESC,offer_id)=1) o
 USING(configuration_id)
LEFT JOIN compatibility x ON x.configuration_id=c.configuration_id AND x.workload_id=$workload
LEFT JOIN benchmarks b ON b.benchmark_id=x.benchmark_id AND b.configuration_id=c.configuration_id
 AND b.release='v6.1' AND b.scenario='Offline' AND b.node_count='1'
ORDER BY c.configuration_id
