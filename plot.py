import math
import numpy as np
import os
import json
import matplotlib.pyplot as plt
from collections import defaultdict, Counter

# 路径配置：替换为你的step文件夹路径
STEP_DIR = 'game_logs/20250728_173040'

# 初始化记录容器
steps = []
cash_list = []
time_left_list = []
sell_count_list = []
buy_count_list = []
orders_count_list = []
total_asset_list = []

item_order_counter = Counter()

# 遍历所有 step 文件
for filename in sorted(os.listdir(STEP_DIR)):
    if not filename.endswith(".json"):
        continue

    with open(os.path.join(STEP_DIR, filename), 'r', encoding='utf-8') as f:
        data = json.load(f)
        game_state = data.get("game_state", {})

        steps.append(filename.replace(".json", ""))
        cash_list.append(game_state.get("cash", 0))
        time_left_list.append(game_state.get("time_left", 0))
        sell_count_list.append(game_state.get("sell_count", 0))
        buy_count_list.append(game_state.get("buy_count", 0))
        total_asset_list.append(game_state.get("total_asset", 0))
        orders = game_state.get("orders", [])
        orders_count_list.append(len(orders))

        # 统计每种商品在所有订单中的出现次数
        for order in orders:
            for item in order.get("items", []):
                item_id = item["id"]
                item_order_counter[item_id] += item["num"]


L = len(steps)
max_xticks = 20  # 最大允许刻度数量（你可以设为 15 或 25）

# 计算合理的步长 N，使得显示的 xticks 不超过 max_xticks
N = max(1, math.ceil(L / max_xticks))


# 绘图：每步 cash、time_left、sell_count、buy_count、orders 数量
plt.figure()
plt.plot(steps, cash_list, label="Cash")
plt.xticks(np.arange(0, L, N), steps[::N], rotation=45)
plt.title("Cash over Steps")
plt.xlabel("Step")
plt.ylabel("Cash")
plt.legend()
plt.tight_layout()
plt.show()


plt.figure()
plt.plot(steps, sell_count_list, label="Sell Count", color="green")
plt.xticks(np.arange(0, L, N), steps[::N], rotation=45)
plt.title("Sell Count over Steps")
plt.xlabel("Step")
plt.ylabel("Sell Count")
plt.legend()
plt.tight_layout()
plt.show()

plt.figure()
plt.plot(steps, buy_count_list, label="Buy Count", color="red")
plt.xticks(np.arange(0, L, N), steps[::N], rotation=45)
plt.title("Buy Count over Steps")
plt.xlabel("Step")
plt.ylabel("Buy Count")
plt.legend()
plt.tight_layout()
plt.show()

plt.figure()
plt.plot(steps, total_asset_list, label="Buy Count", color="red")
plt.xticks(np.arange(0, L, N), steps[::N], rotation=45)
plt.title("Buy Count over Steps")
plt.xlabel("Step")
plt.ylabel("Buy Count")
plt.legend()
plt.tight_layout()
plt.show()
