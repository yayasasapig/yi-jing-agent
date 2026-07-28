"""
䷀ Yi-Jing Agent — 完整使用範例集
===================================

呢個檔案示範 yi-jing-agent 嘅各種用法，由淺入深。
可以直接 `python examples/complete_usage.py` 執行。
"""

import sys
import os
import asyncio

from yi_jing_agent.yao_positions import YaoPosition, AuthorizationLevel
from yi_jing_agent.agent_state import YiJingAgentState, TaskGraph
from yi_jing_agent.executor import YiJingAgentExecutor
from yi_jing_agent.hexagram_table import get_hexagram_name, get_strategy_for_hexagram, STRATEGIES
from yi_jing_agent.reflection import ThreeDimensionalReflection

print("=" * 70)
print("䷀ Yi-Jing Agent — 完整使用範例")
print("=" * 70)


# ═══════════════════════════════════════════
# 範例 1：基本六爻生命週期
# ═══════════════════════════════════════════
print("\n" + "─" * 70)
print("📌 範例 1：基本六爻生命週期（模擬執行）")
print("─" * 70)

async def demo_basic_lifecycle():
    print("啟動六爻執行器...")
    executor = YiJingAgentExecutor(session_id="demo-basic")

    # 用「分析網站定價策略」做測試任務
    result = await executor.execute("分析網站定價策略")

    print(f"\n狀態: {result['status']}")
    print(f"卦象路徑: {result['hexagram_path']}")
    print(f"Session: {result['session_id']}")
    print(f"執行步驟: {len(result['execution_log'])} 步")

    if result['hexagram_history']:
        for t in result['hexagram_history']:
            print(f"  變卦: {t['original']} → {t['new']} ({t['name']})")
            print(f"  策略: {t['strategy']}")

asyncio.run(demo_basic_lifecycle())


# ═══════════════════════════════════════════
# 範例 2：64 卦查表
# ═══════════════════════════════════════════
print("\n" + "─" * 70)
print("📌 範例 2：64 卦查表 — 異常容錯策略")
print("─" * 70)

demo_scenarios = [
    ("111111", "一切順利"),
    ("111011", "五爻 API Timeout"),
    ("110111", "部分成果可用"),
    ("011110", "Token 超限"),
    ("010010", "反覆失敗"),
    ("000000", "全面崩潰"),
    ("010001", "Context 不足"),
    ("100101", "安全檢查失敗"),
]

for code, scenario in demo_scenarios:
    name = get_hexagram_name(code)
    strategy = get_strategy_for_hexagram(code)
    print(f"  {code} {name:　<10} ← {scenario:　<12} → {strategy}")


# ═══════════════════════════════════════════
# 範例 3：三維反思引擎
# ═══════════════════════════════════════════
print("\n" + "─" * 70)
print("📌 範例 3：三維反思引擎（錯綜互卦）")
print("─" * 70)

reflection = ThreeDimensionalReflection("111111")

# 互卦分析
interlocking = reflection.analyze_interlocking("幫我寫爬蟲程式")
print(f"\n🔍 互卦（隱含動機）:")
print(f"   表面任務: {interlocking['surface_task']}")
print(f"   內互卦 {interlocking['inner_trigram']} + 外互卦 {interlocking['outer_trigram']}")
print(f"   反思 Prompt: {interlocking['reflection_prompt'][:80]}...")

# 錯卦分析
opposite = reflection.analyze_opposite("用 requests 直接爬 target.com")
print(f"\n⚔️ 錯卦（對抗思維）:")
print(f"   原始卦象: {opposite['original_code']}")
print(f"   錯卦（反轉）: {opposite['opposite_code']}")
print(f"   反思 Prompt: {opposite['reflection_prompt'][:80]}...")

# 綜卦分析
reversed_view = reflection.analyze_reversed("直接輸出 JSON 格式")
print(f"\n👁️ 綜卦（用戶視角）:")
print(f"   原始卦象: {reversed_view['original_code']}")
print(f"   綜卦（倒轉）: {reversed_view['reversed_code']}")
print(f"   反思 Prompt: {reversed_view['reflection_prompt'][:80]}...")


# ═══════════════════════════════════════════
# 範例 4：手動操作 Agent State
# ═══════════════════════════════════════════
print("\n" + "─" * 70)
print("📌 範例 4：手動操作 Agent State + 動爻變卦")
print("─" * 70)

state = YiJingAgentState()

# 正常執行
print("\n正常執行流程:")
state.task_graph = TaskGraph(
    task_id="T-manual",
    original_intent="翻譯文件成繁體中文",
    constraints=["使用正式書面語"],
)
print(f"  初爻 ✅ Task Graph: {state.task_graph.original_intent}")
state.step_forward()  # 到二爻
state.step_forward()  # 到三爻
print(f"  三爻 ✅ 當前位: {state.current_yao.chinese_name}")

# 模擬異常 — 五爻 API Timeout
print("\n模擬異常 — 五爻 API Timeout:")
state.step_forward()  # 到四爻
state.step_forward()  # 到五爻

transition = state.trigger_moving_yao(5)  # 五爻動爻
print(f"  觸發動爻: bit5 flip")
print(f"  原始: {transition.original_code}")
print(f"  變卦: {transition.new_code} ({transition.transition_name})")
print(f"  策略: {transition.strategy}")

# 降級執行
print(f"\n降級執行:")
state.step_backward(YaoPosition.SECOND_FIELD)
print(f"  回溯至: {state.current_yao.chinese_name}")
state.step_forward()
state.step_forward()
state.step_forward()
print(f"  重新執行: {state.current_yao.chinese_name}")

# 最終卦象路徑
print(f"\n最終卦象路徑:")
print(f"  {state.get_hexagram_path()}")


# ═══════════════════════════════════════════
# 範例 5：搜尋特定卦象
# ═══════════════════════════════════════════
print("\n" + "─" * 70)
print("📌 範例 5：搜尋特定卦象（按策略分類）")
print("─" * 70)

# 分類所有卦象
happy_paths = []
error_recovery = []
multi_agent = []
resource = []

for code, strategy in STRATEGIES.items():
    name = get_hexagram_name(code)
    if "Happy" in strategy or "順利" in strategy:
        happy_paths.append((code, name, strategy))
    elif "人類接管" in strategy or "降級" in strategy or "重新" in strategy:
        error_recovery.append((code, name, strategy))
    elif "協作" in strategy or "團隊" in strategy:
        multi_agent.append((code, name, strategy))
    else:
        resource.append((code, name, strategy))

print(f"\n✅ Happy Paths ({len(happy_paths)}):")
for code, name, _ in happy_paths[:5]:
    print(f"  {code} {name}")

print(f"\n🛡️ Error/Recovery ({len(error_recovery)}):")
for code, name, _ in error_recovery[:5]:
    print(f"  {code} {name}")

print(f"\n🤝 Multi-agent ({len(multi_agent)}):")
for code, name, _ in multi_agent:
    print(f"  {code} {name}")

print(f"\n📊 Resource/Timing ({len(resource)}):")
for code, name, _ in resource[:3]:
    print(f"  {code} {name}")


# ═══════════════════════════════════════════
# 總結
# ═══════════════════════════════════════════
print("\n" + "=" * 70)
print("✅ 所有範例執行完畢！")
print("=" * 70)
print("""
更多用法：
  from agent_state import YiJingAgentState, YaoPosition
  from executor import YiJingAgentExecutor
  from hexagram_table import get_hexagram_name, get_strategy_for_hexagram
  from reflection import ThreeDimensionalReflection
  
See also:
  examples/six-yao-lifecycle-demo.md  (真實試跑記錄)
  docs/architecture-overview.md       (英文架構摘要)
  docs/六爻AI-Agent架構設計書.md        (原創設計藍圖 37KB)
""")
