"""
䷀ 完整 64 卦模擬表 — 用「摘日資訊提取」做統一情景

由 111111 ䷀ 乾為天 (Happy Path) 出發，
展示每個卦象對應嘅唔同 failure/situation mode，
以及喺摘日任務中嘅具體表現。
"""

import sys; sys.path.insert(0, 'src')
from yi_jing_agent.hexagram_table import HEXAGRAM_NAMES, STRATEGIES

# 摘日任務嘅16個常見 scenarios, mapped to hexagrams
scenarios = {
    # ── Happy Path ──
    "111111": "一切順利，網站存取正常，數據完整提取 ✅",

    # ── 初爻相關 (理解/Context) ──
    "010100": "用戶 send「摘日」兩個字，無講邊日 → Context 不足",
    "001010": "用戶 send「睇運程」— 太模糊，唔知邊個網站",
    "111010": "用戶話「我要今日摘日」但之前話過「唔好再用摘日網站」— 邏輯矛盾",

    # ── 二爻相關 (沙盒/工具) ──
    "011111": "curl 測試網站成功但只拎到部分 data（emoji 顯示唔到）",
    "111110": "curl HTTP 500 error — server error，要降級用 browser",
    "110111": "browser 開到網站但 right panel 顯示空白 — 部分數據 missing",
    "100000": "沙盒測試發現網站 loading 好慢（>10s）— 要等耐啲",
    "000100": "curl fail → browser fail → 全部 tool 唔 work → 從頭嚟過",
    "000001": "curl rate limited — 降低請求頻率",
    "101111": "一個 tool 唔夠，要同時用 curl + browser 分工",

    # ── 三爻相關 (安全/反思) ──
    "100101": "發現網站有反爬機制 — 強制安全檢查",
    "110111": "三維反思發現用戶其實想比較「今日」同「聽日」嘅分別",
    "001101": "raw data 太亂，要 reformat 做靚啲嘅表格",
    "001000": "逐步失敗 — 拎到日期但拎唔到宜忌",
    "001011": "context window 開始有舊 session 嘅殘留 data — 要 cleanup",

    # ── 四爻相關 (授權) ──
    "000110": "需要決定係咪自動 send 俾 Telegram — 關鍵決策點",
    "111001": "建議唔好而家 run（夜晚 11 點）— 延遲到聽朝",
    "111011": "發現今日原來有關稅 deadline — 收錄呢個重要資訊等陣處理",

    # ── 五爻相關 (執行) ──
    "010111": "browser loading 好慢，等緊 DOM ready",
    "110010": "Token 消耗接近上限（剩 500 tokens）",
    "010011": "執行中途發現今日係「金神七煞日」— 順便做埋系統 check",
    "100010": "之前 browser 成日 timeout，換咗 agent-browser 之後順咗",
    "001110": "Token cost 超出預期 — 要轉用較平嘅方案",
    "011100": "任務超額完成 — 拎到埋藏曆同神明聖誕資訊",
    "100111": "多咗好多 system resource（memory/context space）可以加大個 report",
    "110101": "用戶突然話「不如改睇聽日」— 要 pivot 個 plan",
    "101011": "發現摘日網站有 API — 試下用 API 代替 browser scraping",
    "100100": "Extract data 途中網站突然改 layout — 緊急處理",
    "001001": "網站太多 animation 睇到眼花 — 停低唞唞",
    "011001": "一步一步慢慢 extract，逐個 field 確認",
    "100110": "多個 sources 嘅數據要 merge 埋一齊",
    "100101": "數據好豐富，要 summarize 唔好太長",
    "101001": "啱啱由另一個 project 轉過嚟，context 要 reset",
    "011011": "網站有 JS render，要等佢慢慢 load",
    "110110": "用戶收到份 report 話「正呀！」— 可以再送多個 bonus",
    "011010": "Context window 就快滿 — 強制壓縮",
    "010110": "Token 用咗 8K/10K — 要計住 budget",
    "011110": "確認用戶仲係咪睇緊今日 — 雙重驗證",
    "100001": "一個欄位嘅日期格式錯咗 — 小問題繼續",
    "010101": "任務完成，準備上爻復盤",
    "101010": "所有 data 拎晒，但差最後一步整理表格 — retry 授權",

    # ── 上爻相關 (記憶) ──
    "011000": "累積咗好多次摘日提取經驗，可以壓縮成 pattern",
    "000011": "Context 好充足，可以進入深層分析（對比過去 7 日）",
    "110011": "output 太長（50 行）— 可能 over-engineering",
    "000000": "全部嘢炒晒 — website down + memory full + token out — 人類接管",
    "111000": "用戶 feedback「份 report 好有用」— 繼續用同一個 pattern",
    "101000": "進度好順，可以加速自動化排程",
    "000101": "Extract data 時網站突然多咗 paywall — 換免費網站替代",
    "110000": "多個來源嘅數據（摘日 + 六壬 + 奇門）匯聚完畢",
    "011101": "將呢個 extract logic 分享俾其他 internal agent 用",
    "101110": "兩個 extract method 出嘅 data 有出入 — 要投票決定信邊個",
    "011000": "觀察 mode — 今日嘅 data pattern 同昨日有咩唔同",
    "001110": "用戶 feedback「我想要埋聽日」— 轉 interactive 模式",
    "000011": "可以分析更深 — 睇埋今個月嘅吉日分佈",
    "110100": "用戶話「改為每朝自動 send 俾我」— 順勢跟隨",
    "010001": "extract 速度好慢 — 睇下有冇 bottleneck",
    "110110": "用戶 like 咗個 report — 可以考慮每日自動出",
    "110101": "要由「摘日」轉做「奇門」分析 — 大幅 pivot",
    "101011": "試下用 Gemini Vision 直接睇網站 screenshot",
    "100011": "呢個每日摘日係長週期任務 — 加 checkpoint",
    "111111": "一切順利嘅 Happy Path ✅",
}

print('=' * 70)
print('䷀ 完整 64 卦模擬：摘日任務 failure/situation mode')
print('=' * 70)
print()

# 逐卦列出
for code, (symbol, name) in sorted(HEXAGRAM_NAMES.items()):
    strategy = STRATEGIES.get(code, '—')
    scenario = scenarios.get(code, '—')
    seen = code in ['111111', '011111', '101111', '110111', '111011', '111101', '111110']
    marker = '🔥' if seen else '  '
    
    print(f'{marker} {symbol} {code} {name:　<10}')
    print(f'  ├─ 策略: {strategy}')
    print(f'  └─ 情境: {scenario}')
    print()
