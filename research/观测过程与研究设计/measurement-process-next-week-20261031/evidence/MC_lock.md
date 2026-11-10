# mp_benchmark_v1 (BRITS / mTAND / Raindrop, wangyiming) plan lock
locked_at: 2026-10-21 20:50:01 +0800

## plan documents
f11083548358180fc53eab6cc9bb2b997a16f8a65a20ca6f47e5a2b85c06427d  六模型观测删减敏感性实验_任务说明_正式版.md
8c6e45ea9b7a7f483b23a8abb4c1264ab2e0c279346ff5a7505086a9d0b14d28  mp_benchmark_v1_三模型执行方案_wangyiming_20261021.md

## configs
53ff85d4d47ac6f41866c0b744ac0b45df709b2660ba1be7d4b2e74a365b46dc  configs/brits.json
b0a716194fd5613235a4c5d55400ecd98740cd9d2af9460d59c966f331267ce2  configs/mtand.json
65e7d6ccc2244ca47e34b6d2bd447419b49f45be5ecc460e9d7e48abcf8085ae  configs/raindrop.json

## code
c5479a0924629e57cdefef45528c7a1a24c891823d995134d6dfb5ca03b08fee  run_model.py
e0d87ed15180ac12541e61535cf5374108633c5a5865c1f30b6db56947fc5ccb  engine.py
d311bec2527cd13f80e9d661704ae8639240f84fbc84c56b71bf1108a797003e  inputs.py
b01d937a7dc66e6ad6fdb4d013109f726d879002fd61dde39900670839a3e11b  models/brits.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  models/__init__.py
fd13f71bbbfd447e05e51cda95953746749ca3dc305029f3d49c7fdb378e1e55  models/mtand.py
72293a4d1f50549741208995abaf09730b201759da0543a01bf1c5315d027adf  models/raindrop.py
bce105ca76711eca5e9c9a4a1e647592e7b22b72ef76631dff89f3581167c372  common/benchmark.py
3864483d7187ca3c19b30869788095336b0edac5313bbc1af3011f6d46634904  common/__init__.py
711805636000f3526bc0cc47158449733cc2a680afdc502be8ef2f48ef1c4210  common/metrics.py
0706660049a8b9a879fe8d8ac4e4443827855cd91ef06757892390ff5ccf872d  profile_benchmark.py
45dfcaa5dd3787c629838da1715075254a2deea852beec4ac0933da85e301ae6  tests/test_mp_benchmark_v1.py

## common provenance (copied verbatim from liangruiying measurement_policy_models/common)
bce105ca76711eca5e9c9a4a1e647592e7b22b72ef76631dff89f3581167c372  benchmark.py
711805636000f3526bc0cc47158449733cc2a680afdc502be8ef2f48ef1c4210  metrics.py
3864483d7187ca3c19b30869788095336b0edac5313bbc1af3011f6d46634904  __init__.py

## frozen benchmark
dir: /home/ud202482579/liangruiying/MC-BEC-Reproduction/outputs/measurement_policy_benchmark_v1
9fbdc602f9e7a965df757f4f4ead22c1e8aac886cffaeb728596c3d19abbbebc  /home/ud202482579/liangruiying/MC-BEC-Reproduction/outputs/measurement_policy_benchmark_v1/DATA_CHECKSUMS.sha256
manifest_final.parquet: OK
train_observations_original.parquet: OK
val_observations_original.parquet: OK
test_observations_original.parquet: OK
test_observations_drop20.parquet: OK
test_observations_drop40.parquet: OK
test_observations_continuous5min.parquet: OK
benchmark_v1_config.json: OK

## pre-run checks
unit tests: 10 passed, 4 warnings in 9.14s
smoke: brits/mtand/raindrop exit 0 (logs/2026-10-21/mp_*_smoke.log)
seeds: 2026 primary; 2027, 2028 pre-registered additional
82d20865d95a7dd7ed2c29fa89502474550a5d5c911c5c4d32ffa9dde50d1d79  run_seeds.sh  (driver, added before launch)
59cc4c5758dfd2e455c3b46a786c12192cc0da537c3d5ef37d5da1209fcdf95f  run_seeds.sh  (driver v2: rc captured before date; replaces v1 above, relaunch 20:5x)
b6499b8cf87c5307119bea6660b453187b27b35af0b3cf90a01f6a6aeb0a98fe  summarize.py  (aggregation script, added after launch and before any result was read)

## 2026-10-21 22:01:04 post-hoc supplementary metrics (added AFTER results were read)
# Reason: LSTM branch extended common/metrics.py at 20:25 (prediction_correlation; Brier CI; delta_brier).
# Applied to the frozen pred_*.csv only; no retraining, no re-scoring, no threshold/checkpoint change.
# The script refuses to write unless the stored bootstrap CIs are reproduced exactly.
140d637156b50f84cae32b7a1927fb81a2a0b4565bf8a527c7f402df1c731dd8  /home/ud202482579/wangyiming/basemodel/experiments/mp_benchmark_v1/supplement_metrics.py
45eb8dba57d6fd6cde721db7d159148ce424e8937cac65d2cf152dd6efefcb6d  /home/ud202482579/wangyiming/basemodel/experiments/mp_benchmark_v1/common/metrics_v2.py
# metrics_v2.py = verbatim copy of LSTM-branch common/metrics.py (mtime 20:25) taken 2026-10-21 22:01:04; PROVENANCE line kept sha256sum -c compatible
# 2026-10-21 22:07:19 post-hoc descriptive diagnostics (written AFTER results were read; no effect on checkpoints/thresholds/predictions)
3a07fc565b5d8562c9466571e45416216cc9e5b8ba596937038cb5e2e6c2dde6  /home/ud202482579/wangyiming/basemodel/experiments/mp_benchmark_v1/posthoc_diagnostics.py
# 2026-10-21 22:19:05 HTML result page data export (aggregates only; after results were read; no effect on runs)
a7156b902d75ff19e03587d89e7e8da2d24257ef71318285c27945e2b7df70bb  /home/ud202482579/wangyiming/basemodel/experiments/mp_benchmark_v1/export_report_data.py

## 2026-10-22 16:46:21 addendum: align seeds/format with LSTM/GRU-D branch (researcher decision 2026-10-22, plan §8; registered BEFORE these runs)
# seeds 2029, 2030 added for brits/mtand/raindrop; seeds 2026-2028 untouched; code/configs unchanged (verified against hashes above)
fc6704123e57989efdd2b46066580d6ae101e20a3ec95b6129afd832f44d69bf  /home/ud202482579/wangyiming/docs/basemodel/plan/week04/mp_benchmark_v1_三模型执行方案_wangyiming_20261021.md
87a26d160cc495de7745757a4f038543c7edc36e3407bfa19e42db3f1c0883fc  /home/ud202482579/wangyiming/basemodel/experiments/mp_benchmark_v1/run_seeds.sh  (driver v3: log dir = logs/<run date>; otherwise identical to v2)
# logs: logs/2026-10-22/
# 2026-10-22 16:56:00 five-seed export / model-comparison script (plan §8 items 2-3); written and hashed BEFORE the 2029/2030 runs finished and before any five-model number was computed
# reads this branch's frozen pred_*.csv (cross-checked against each results.json, tol 1e-9) + the LSTM/GRU-D branch's aggregate five_seed_all_results.csv and epoch counts of its training logs; writes aggregates only
3e73e84d8e076182d0f1ec88049461235f6a4316bdf6fab8ef4234289cf3b210  /home/ud202482579/wangyiming/basemodel/experiments/mp_benchmark_v1/export_five_seed.py
# 2026-10-22 17:11:38 runs 2029/2030 finished (logs/2026-10-22/mp_benchmark_v1_runs.txt, all exit=0); summarize -> docs/.../week04/mp_benchmark_v1_wangyiming_20261022.{json,tables.md}: 15 runs, no failing §19 check
# supplement_metrics for the 6 new runs: supplement_metrics.main refuses when any target exists, so supplement_metrics.supplement() was called inline only for runs without the file (script unchanged; all stored CIs reproduced)
# posthoc_diagnostics (unchanged) -> logs/2026-10-22/mp_benchmark_v1_posthoc_diagnostics.json; export_five_seed (hash above) -> docs/.../week04/mp_benchmark_v1_five_seed_summary/
