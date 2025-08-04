import math
import numpy as np
import os
import json
import matplotlib.pyplot as plt
from collections import defaultdict, Counter

# 配置路径：日志路径和图片输出路径

## qwen3-30b-a3b-thinking-2507 'new_game_logs/20250802_235605'
## qwen3-32b thinking 20250802_225901
STEP_DIR = 'new_game_logs/20250802_225901'
OUTPUT_DIR = 'figures'
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    if len(filename) > 15 or not filename.endswith(".json"):
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

        for order in orders:
            for item in order.get("items", []):
                item_id = item["id"]
                item_order_counter[item_id] += item["num"]

# 图表辅助配置
L = len(steps)
max_xticks = 20  # 最大允许的横坐标刻度数
N = max(1, math.ceil(L / max_xticks))  # 步长

# 通用保存图像函数
def save_plot(y_data, label, title, filename, color="blue"):
    plt.figure()
    plt.plot(steps, y_data, label=label, color=color)
    plt.xticks(np.arange(0, L, N), steps[::N], rotation=45)
    plt.title(title)
    plt.xlabel("Step")
    plt.ylabel(label)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()

# 绘制并保存图像
save_plot(cash_list, "Cash", "Cash over Steps", "cash_over_steps.png", color="blue")
save_plot(sell_count_list, "Sell Count", "Sell Count over Steps", "sell_count_over_steps.png", color="green")
save_plot(buy_count_list, "Buy Count", "Buy Count over Steps", "buy_count_over_steps.png", color="red")
save_plot(total_asset_list, "Total Asset", "Total Asset over Steps", "total_asset_over_steps.png", color="purple")

print(f"✅ 所有图表已保存到：{os.path.abspath(OUTPUT_DIR)}")