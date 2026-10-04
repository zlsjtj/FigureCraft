# DEMO topology, arithmetic, and operating record

## Objects and connections

There are exactly three source branches: roof A (west, 20 L/min), roof B (central, 30 L/min), and roof C (service, 10 L/min). There are exactly two storage tanks, W and E. A feeds W. C feeds E. A single lossless diverter takes all of B's flow and sends fraction alpha to W and fraction 1-alpha to E. B is not duplicated, independently controllable on its two outgoing sides, or a stored reservoir. W and E have separate loads and separate spill drains; there is no W→E or E→W transfer.

Source-to-tank flow mapping, with rows [W,E] and columns [A,B,C]:

M(alpha) = [[1, alpha, 0], [0, 1-alpha, 1]]. **Source Eq. T1**

Tank inflow vector = M(alpha) * [20,30,10]^T L/min. The entries of M are dimensionless routing fractions; each column sums to 1. Its row sums are not volume or flow. At alpha=1/3, the physical branch flows are A→W=20, B→W=10, B→E=20, C→E=10 L/min. At alpha=0.10 they are 20,3,27,10 L/min in the same order.

W capacity=200 L; E capacity=300 L. Initial volumes are 180 and 250 L respectively. Load withdrawals are 18 and 24 L/min respectively, always served. Runoff, withdrawal, and alpha are constant within each one-minute interval. Flow transit time and pipe storage are neglected. No evaporation, leakage, rainfall change, water quality restriction, unavailable demand, or change of tank capacity is modeled.

For tank k and interval duration Delta=1 min, raw net volume gain g_k=(inflow_k-load_k)*Delta. Stored ending volume V_next=min(capacity_k,V_now+g_k); spill=max(0,V_now+g_k-capacity_k). **Source Eq. T2**. This formula is valid here because all raw net gains are positive and no tank empties. It is not a general simulator for unsatisfied demand.

For the entire event, initial stored volume + total source inflow = final stored volume + delivered load + total spill. **Source Eq. T3**. Initial stored volume is 430 L, four-minute source inflow is 240 L, and four-minute delivered load is 168 L. Volume changes occur continuously; records report interval totals and exact interval endpoints. A fractional first overflow time can be derived from free volume divided by positive net inflow, but it should not be rounded to the first whole-minute report.

## Preserved schedules

* FIXED_THIRD: alpha=1/3 in minutes [0,1),[1,2),[2,3),[3,4).
* DELAYED_TENTH: alpha=1/3 in [0,1), then alpha=0.10 in [1,4). The setting changes at exactly 60 s.
* FIXED_TENTH: alpha=0.10 throughout [0,4), selected before runoff starts.

These are schedule labels, not algorithms with unrecorded sensor readings. All schedules start independently at W=180 L and E=250 L. No switching penalty is included. The historical and preselected settings may use different prior knowledge in a real deployment; this DEMO supplies no evidence about that knowledge or its reliability.

## CSV column definitions and provenance

`interval_results.csv` has 3 schedules x 4 intervals x 2 tanks =24 rows. Key=(policy,interval_start_min,tank). `alpha_to_west` is a dimensionless central-branch fraction. `inflow_lpm`, `load_lpm`, and `net_gain_lpm` are rates. `start_l`, `capacity_l`, `raw_net_gain_l`, `spill_l`, and `end_l` are volumes. `interval_duration_min` converts rates to volumes. `spill_l` is the current interval's spill rather than cumulative spill. Both unsuccessful storage cases and favorable cases remain present.

Internal sources are only this declared model, the original prose fragments, and the deterministic arithmetic in `construct_transfer.py`. Every table row is explicitly marked CONSTRUCTED_DEMO. No real building, supplier, installation, measurement, or source publication is represented.
