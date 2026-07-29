# 📊 Yi-Jing Agent Benchmarks

> Performance baselines for core operations.
> Run locally with: `pytest tests/benchmarks/ --benchmark-only -v`

## Current Baselines (v0.1.0)

| Benchmark | Operations | Avg Time | Notes |
|:----------|:----------:|:--------:|:------|
| `test_step_forward_10k` | 10,000 state transitions | **14.7ms** | Pure Python, near-instant |
| `test_trigger_moving_yao_all_positions` | 6 moving yao triggers | **22µs** | Includes XOR flip + hexagram lookup |
| `test_hexagram_path_generation` | 1,000 path gens (full history) | **1.25ms** | String formatting + lookups |
| `test_all_64_name_lookups` | 64 hexagram name lookups | **8µs** | Dict lookup, O(1) |
| `test_all_64_strategy_lookups` | 64 strategy lookups | **14µs** | Dict lookup + fallback logic |
| `test_unknown_code_fallback` | 5 unknown code lookups | **1.8µs** | Fallback with bit counting |
| `test_full_lifecycle_empty_input` | Full lifecycle (fast-fail) | **137µs** | Returns at 初爻 |
| `test_full_lifecycle_happy_path` | Full lifecycle (all 6 stages) | **290µs** | Simulated execution |
| `test_full_lifecycle_with_llm` | Full lifecycle (fake LLM) | **360µs** | Includes LLM callback overhead |
| `test_express_mode_lifecycle` | Express mode lifecycle | **131µs** | Skips 3 stages |
| `test_full_reflection_all_codes` | 3D reflection (5 codes) | **5µs** | Prompt generation only |
| `test_interlocking_analysis` | 100x 互卦 analysis | **32µs** | String operations |
| `test_opposite_analysis` | 100x 錯卦 analysis | **27µs** | String operations |

> **Note:** These benchmarks measure pure Python logic speed.
> Real-world performance depends on LLM latency (usually 1-5s per call).

## CI Benchmark Gate

Benchmarks run on every push via GitHub Actions.
Results are uploaded as build artifacts for regression tracking.

## Coverage Gate

Current target: **>90% code coverage** (measured by `pytest-cov`).
Gate enforced in CI pipeline.

## Future: A/B Comparison (v0.2.0)

Planned comparison with standard LangGraph ReAct agent:

| Metric | LangGraph ReAct | Yi-Jing Agent (v0.2.0) |
|:-------|:---------------:|:----------------------:|
| Task Completion Rate (TCR) | — | — |
| Target Drift Rate | — | — |
| Self-Healing Success Rate | — | — |
| Token Efficiency | — | — |
| Avg Latency per Task | — | — |

---

*Last updated: 2026-07-28 · Yi-Jing Agent v0.1.0*
