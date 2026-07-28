"""䷀ 六爻時位定義 — Six Lines / Yao Position Definitions"""
from enum import Enum


class YaoPosition(Enum):
    """六爻時位：Agent 嘅 6 階執行生命週期"""
    FIRST_HIDDEN = 1   # 初爻：潛龍勿用 — 脈絡構建，嚴禁動作
    SECOND_FIELD = 2   # 二爻：見龍在田 — 沙盒試探，局部驗證
    THIRD_ALERT = 3    # 三爻：終日乾乾 — 三維反思，安全審查
    FOURTH_LEAP = 4    # 四爻：或躍在淵 — 人機協同，授權決策
    FIFTH_FLYING = 5   # 五爻：飛龍在天 — 全力執行，並行輸出
    SIXTH_REGRET = 6   # 上爻：亢龍有悔 — 復盤歸檔，記憶壓縮

    @property
    def chinese_name(self) -> str:
        names = {
            1: ("初爻", "潛龍勿用"),
            2: ("二爻", "見龍在田"),
            3: ("三爻", "終日乾乾"),
            4: ("四爻", "或躍在淵"),
            5: ("五爻", "飛龍在天"),
            6: ("上爻", "亢龍有悔"),
        }
        num, desc = names[self.value]
        return f"{num} {desc}"

    @property
    def emoji(self) -> str:
        emojis = {1: "🐉", 2: "🌾", 3: "⚔️", 4: "🐉", 5: "🐲", 6: "🌧️"}
        return emojis[self.value]


class AuthorizationLevel(Enum):
    """四爻授權級別"""
    AUTO = 0       # Level 0: 完全自動 — 唯讀操作，無副作用
    NOTIFY = 1     # Level 1: 通知人類 — 修改本地檔案，中等風險
    CONFIRM = 2    # Level 2: 必需確認 — 寫入外部系統，高風險
    HUMAN_EXEC = 3  # Level 3: 人類執行 — API Key/刪除/金錢，極高風險
