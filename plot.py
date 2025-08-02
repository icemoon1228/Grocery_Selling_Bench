# import math
# import numpy as np
# import os
# import json
# import matplotlib.pyplot as plt
# from collections import defaultdict, Counter

# # 路径配置：替换为你的step文件夹路径
# STEP_DIR = 'game_logs/20250728_173040'

# # 初始化记录容器
# steps = []
# cash_list = []
# time_left_list = []
# sell_count_list = []
# buy_count_list = []
# orders_count_list = []
# total_asset_list = []

# item_order_counter = Counter()

# # 遍历所有 step 文件
# for filename in sorted(os.listdir(STEP_DIR)):
#     if not filename.endswith(".json"):
#         continue

#     with open(os.path.join(STEP_DIR, filename), 'r', encoding='utf-8') as f:
#         data = json.load(f)
#         game_state = data.get("game_state", {})

#         steps.append(filename.replace(".json", ""))
#         cash_list.append(game_state.get("cash", 0))
#         time_left_list.append(game_state.get("time_left", 0))
#         sell_count_list.append(game_state.get("sell_count", 0))
#         buy_count_list.append(game_state.get("buy_count", 0))
#         total_asset_list.append(game_state.get("total_asset", 0))
#         orders = game_state.get("orders", [])
#         orders_count_list.append(len(orders))

#         # 统计每种商品在所有订单中的出现次数
#         for order in orders:
#             for item in order.get("items", []):
#                 item_id = item["id"]
#                 item_order_counter[item_id] += item["num"]


# L = len(steps)
# max_xticks = 20  # 最大允许刻度数量（你可以设为 15 或 25）

# # 计算合理的步长 N，使得显示的 xticks 不超过 max_xticks
# N = max(1, math.ceil(L / max_xticks))


# # 绘图：每步 cash、time_left、sell_count、buy_count、orders 数量
# plt.figure()
# plt.plot(steps, cash_list, label="Cash")
# plt.xticks(np.arange(0, L, N), steps[::N], rotation=45)
# plt.title("Cash over Steps")
# plt.xlabel("Step")
# plt.ylabel("Cash")
# plt.legend()
# plt.tight_layout()
# plt.show()


# plt.figure()
# plt.plot(steps, sell_count_list, label="Sell Count", color="green")
# plt.xticks(np.arange(0, L, N), steps[::N], rotation=45)
# plt.title("Sell Count over Steps")
# plt.xlabel("Step")
# plt.ylabel("Sell Count")
# plt.legend()
# plt.tight_layout()
# plt.show()

# plt.figure()
# plt.plot(steps, buy_count_list, label="Buy Count", color="red")
# plt.xticks(np.arange(0, L, N), steps[::N], rotation=45)
# plt.title("Buy Count over Steps")
# plt.xlabel("Step")
# plt.ylabel("Buy Count")
# plt.legend()
# plt.tight_layout()
# plt.show()

# plt.figure()
# plt.plot(steps, total_asset_list, label="Buy Count", color="red")
# plt.xticks(np.arange(0, L, N), steps[::N], rotation=45)
# plt.title("Buy Count over Steps")
# plt.xlabel("Step")
# plt.ylabel("Buy Count")
# plt.legend()
# plt.tight_layout()
# plt.show()





import os
import json
import math
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

# ✅ 多个日志文件夹路径
STEP_DIRS = [
    'new_game_logs/20250730_141804',
    'new_game_logs/20250730_141807',
    'new_game_logs/20250730_141809',
    'new_game_logs/20250730_141811',
]

# ✅ 存储每个文件夹下的指标序列
metrics_by_dir = {}

for dir_path in STEP_DIRS:
    days = []
    cash_list = []
    time_left_list = []
    sell_count_list = []
    buy_count_list = []
    orders_count_list = []
    total_asset_list = []
    item_order_counter = Counter()
    args = None

    for filename in sorted(os.listdir(dir_path)):
        if not filename.endswith(".json"):
            continue

            

        with open(os.path.join(dir_path, filename), 'r', encoding='utf-8') as f:
            data = json.load(f)
            game_state = data.get("game_state", {})

            day = game_state.get("day")
            if day is None:
                print(f"[警告] {filename} 缺失 day 字段，跳过")
                continue
            days.append(day)

            if args is None and 'args' in data:
                args = data['args']

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

    steps = list(range(len(days)))  # 索引作为 step

    metrics_by_dir[dir_path] = {
        "days": days,
        "steps": steps,
        "cash": cash_list,
        "sell_count": sell_count_list,
        "buy_count": buy_count_list,
        "orders_count": orders_count_list,
        "total_asset": total_asset_list,
        "time_left": time_left_list,
        "item_order_counter": item_order_counter,
        "args": args
    }

# ✅ 控制最多横轴标签数量
max_xticks = 20

# ✅ 通用绘图函数（新增 use_day_as_x 控制横轴）
def plot_metric_across_dirs(metric_name: str, title: str, ylabel: str, use_day_as_x: bool = True):
    plt.figure()

    # 🔹统一收集所有横轴值（无论是 day 还是 step）
    x_key = "days" if use_day_as_x else "steps"
    all_x_values = sorted(set(x for metrics in metrics_by_dir.values() for x in metrics[x_key]))

    # 🔹计算合理 xtick 显示步长
    L = len(all_x_values)
    N = max(1, math.ceil(L / max_xticks))
    xtick_positions = all_x_values[::N]

    for dir_path, metrics in metrics_by_dir.items():
        x_vals = metrics[x_key]
        y_vals = metrics[metric_name]

        # 仅绘制该文件夹实际的数据（不会强制补齐）
        print(metrics)

        enable_thinking = metrics['args']['enable_thinking']
        plt.plot(x_vals, y_vals, label=f"{metrics['args']['model']}{'_enable_think' if enable_thinking else ''}")

    plt.title(title)
    plt.xlabel("Day" if use_day_as_x else "Step")
    plt.ylabel(ylabel)
    plt.legend()

    # 🔹仅设置稀疏的 xtick
    plt.xticks(xtick_positions, rotation=45)
    plt.tight_layout()
    plt.show()

# ✅ 调用方式：可以切换 use_day_as_x
plot_metric_across_dirs("cash", "Cash Over Time", "Cash", use_day_as_x=True)
plot_metric_across_dirs("sell_count", "Sell Count Over Time", "Sell Count", use_day_as_x=True)
plot_metric_across_dirs("buy_count", "Buy Count Over Time", "Buy Count", use_day_as_x=True)
plot_metric_across_dirs("total_asset", "Total Asset Over Time", "Total Asset", use_day_as_x=True)
# plot_metric_across_dirs("orders_count", "Order Count Over Time", "Order Count", use_day_as_x=True)

# 如果你想用 step 来绘图（对齐方便）：
# plot_metric_across_dirs("cash", "Cash Over Step", "Cash", use_day_as_x=False)