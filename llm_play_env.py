import argparse
from pathlib import Path
import random
import time
from format import format_game_state, format_game_state_total
from llm_response import get_llm_response, get_llm_response_tool_call, client, get_llm_response_tool_call_model_server
import json


## sk-8731fd401be741939f62f46662510509


# shop_env_tools: MCP风格工具描述，供LLM tool_call使用
shop_env_tools = [
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "view_orders",
    #         "description": "查看当前所有订单信息，消耗10分钟。",
    #         "parameters": {
    #             "properties": {},
    #             "required": [],
    #             "type": "object"
    #         },
    #     }
    # },
    {
        "type": "function",
        "function": {
            "name": "buy_goods",
            "description": "进货指定商品。支持批量进货,每个商品需指定商品id、数量。消耗60分钟。",
            "parameters": {
                "properties": {
                    "orders": {
                        "description": "进货订单数组,每个元素包含商品id、数量",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"description": "商品id(整数)", "type": "integer"},
                                "num": {"description": "进货数量", "type": "integer"},
                            },
                            "required": ["id", "num"]
                        }
                    }
                },
                "required": ["orders"],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sell_order",
            "description": "售出指定订单。参数为订单id(order_id), 只能售出一个订单。消耗10分钟。",
            "parameters": {
                "properties": {
                    "order_id": {
                        "description": "要售出的订单id(整数)",
                        "type": "integer"
                    }
                },
                "required": ["order_id"],
                "type": "object"
            }
        }
    },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "view_inventory",
    #         "description": "查看当前库存状况, 展示所有商品的库存数量。消耗20分钟。",
    #         "parameters": {
    #             "properties": {},
    #             "required": [],
    #             "type": "object"
    #         },
    #     }
    # },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "view_cash",
    #         "description": "查看当前剩余的现金。消耗1分钟。",
    #         "parameters": {
    #             "properties": {},
    #             "required": [],
    #             "type": "object"
    #         },
    #     }
    # },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "view_incoming_goods",
    #         "description": "查看所有尚未到货的进货订单，包括商品id、数量、预计到货时间。消耗5分钟。",
    #         "parameters": {
    #             "properties": {},
    #             "required": [],
    #             "type": "object"
    #         },
    #     }
    # },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "view_goods_price_list",
    #         "description": "查看所有商品的基本信息，包括名称、进价、售价和类别。用于分析利润空间。",
    #         "parameters": {
    #             "properties": {},
    #             "required": [],
    #             "type": "object"
    #         },
    #     }
    # },
    {
        "type": "function",
        "function": {
            "name": "wait_time",
            "description": "等待今日时间流逝",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
        }
    },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "view_history",
    #         "description": "查看过去所有天数的门店信息记录，供复盘与长期决策使用。消耗10分钟。",
    #         "parameters": {
    #                 "properties": {},
    #                 "required": [],
    #                 "type": "object"
    #             },
    #         }
    # }
]

from settings import GOODS_LIST
from shop_env import ShopEnv
import os
from http import HTTPStatus

def execute_tool_call_with_output(env, tool_call):
    name = tool_call['name']
    arguments = tool_call.get('arguments', {})

    tool_res = None
    result_str = ""

    _, _, tool_res = env.step(action=name, params=arguments)

    if name == 'view_orders':
       
        result_str = "📦 当前订单列表：\n" + "\n".join(
            [f"- 订单ID {o['order_id']}：" + "；".join(
                [f"{item['num']}件 {GOODS_LIST[item['id']]['name']}" for item in o['items']]
            ) for o in tool_res]
        ) if tool_res else "暂无订单信息。"

    elif name == 'view_cash':
        result_str = f"💰 当前现金：￥{tool_res:.2f}"

    elif name == 'view_inventory':
        result_str = "📦 当前库存：\n" + "\n".join(
            [f"-货品id_{item['id']}, 货品名称_{item['name']}：{item['num']}件" for item in tool_res]
        )

    elif name == 'view_incoming_goods':
        deliveries, today = tool_res
        if not deliveries:
            result_str = "📦 没有待到货商品。"
        else:
            result_str = "🚚 待到货商品：\n"
            for delivery in deliveries:
                arrival = delivery['arrival_day']
                lines = [f"  - {GOODS_LIST[i]['name']}：{qty}件"
                         for i, qty in enumerate(delivery['goods']) if qty > 0]
                result_str += f"🗓 到货日为第{arrival}天：\n" + "\n".join(lines) + "\n"

    elif name == 'buy_goods':
        if tool_res['status'] == 'success':
            result_str = f"✅ 已提交订货订单 {tool_res['meta']['order_id']}, 预计第{tool_res['meta']['arrival_day']}天到达。"
        else:
            result_str = f"❌ 提交订货订单, 原因为{tool_res['reason']}。"

    elif name == 'sell_order':
        if tool_res['status'] == 'success':
            result_str = f"✅ 已售出订单 ID {arguments.get('order_id')}, 收银 {tool_res['meta']['money']:.2f}元"
        else:
            result_str = f"❌ 售出订单 ID {arguments.get('order_id')} 失败, 原因为{tool_res['reason']}。"

    elif name == 'view_goods_price_list':
        result_str = "📦 货品价格列表：\n" + "\n".join(
            [f"- {item['name']}：进价￥{item['current_buy_price']:.2f}, 售价￥{item['current_sell_price']:.2f}" for item in tool_res]
        )
    
    elif name == 'wait_time':
        result_str = '✅ 已等待时间流逝.'
    # elif name == 'view_history':
    #     if not tool_res:
    #         result_str = "📘 暂无历史记录。"
    #     else:
    #         result_str = "📘 历史记录：\n"
    #         for day_idx, day_obs in enumerate(tool_res, start=1):
    #             cash = day_obs.get("cash", 0.0)
    #             inventory = day_obs.get("inventory", [])
    #             orders = day_obs.get("orders", [])

    #             # 处理库存信息
    #             if isinstance(inventory, list) and all(isinstance(x, (int, float)) for x in inventory):
    #                 inventory_summary = ", ".join(
    #                     f"{GOODS_LIST[i]['name']}:{int(num)}件"
    #                     for i, num in enumerate(inventory) if num > 0
    #                 ) or "无库存"
    #             else:
    #                 inventory_summary = "库存信息异常"

    #             # 处理订单信息
    #             if isinstance(orders, list) and orders:
    #                 order_summary = ""
    #                 for o in orders:
    #                     order_id = o.get('order_id', '?')
    #                     items = o.get('items', [])
    #                     item_str = "；".join(
    #                         f"{item['num']}件 {GOODS_LIST[item['id']]['name']}" for item in items
    #                     )
    #                     order_summary += f"    - 订单ID {order_id}：{item_str}\n"
    #             else:
    #                 order_summary = "    - 无订单记录\n"

    #             result_str += (
    #                 f"🗓 第{day_idx}天：\n"
    #                 f"💰 现金：￥{cash:.2f}\n"
    #                 f"📦 库存：{inventory_summary}\n"
    #                 f"📋 订单：\n{order_summary}"
    #             )
    else:
        result_str = f"⚠️ 未知工具调用：{name}"

    return result_str

system_prompt = """你是一个专业的零售店经营管家，专注于帮助门店提升运营效率、优化商品管理、提高销售额。你拥有以下能力：

- 能够根据历史上下文判断用户的目标与任务进度；
- 能理解门店的实时数据（如库存、销售、客流）和可用工具的功能；
- 能做出清晰、理性的下一步行动建议，包括：调用工具、分析数据、生成提醒或建议用户输入更多信息；
- 拥有长期规划能力，能够结合当前现金、库存、销量、供货周期，制定跨天策略；
- 善于提前预判未来几天的供需变化（如库存消耗、订单增长），优先规划关键商品的采购与售卖；
- 所有建议应具体、明确，并能被执行；
- 保持简洁、专业、面向目标，不输出与任务无关的内容。

你的目标是：根据上下文与工具状态判断当前最优操作，并推动任务向长期收益最大化的方向稳步前进。
"""

user_prompt_template = """请根据以下门店状态，判断最优的经营操作，并**务必调用一个工具（只能一个）**。

【过去经营门店日志】
{dairies}

【门店状态】
{game_state}

【今日已执行的操作记录】
{history_records}

经营规则：
- 每日房租固定为 ¥2000，日终扣除；
- 所有库存商品每天会有自然损耗；
- 每天可使用 480 分钟，不同操作耗时不同；
- **如果现金余额为 0 或为负，门店将直接倒闭，游戏失败！你必须时刻关注现金余额，避免倒闭风险。**

你的任务：

当调用工具的时候，请严格使用以下格式输出工具调用内容：
<tool_call>
{{
  "name": "工具名称（字符串，例如 view_inventory）",
  "arguments": 参数对象（如无参数请写 {{}}）
}}
</tool_call>

现在请你完成本轮决策。
"""

def parse_args():
    """
    解析命令行参数
    :return: 解析后的参数对象
    """
    parser = argparse.ArgumentParser(description="解答智能体")

    # 添加参数
    parser.add_argument(
        "--model",
        type=str,
        default="aliyun_qwen3-32b",
        help="使用的模型"
    )

    parser.add_argument(
        "--enable_thinking",
        action="store_true",
        help="是否启用思考模式"
    )

    return parser.parse_args()

def main():
    args = parse_args()
    print("参数:", args)
    env = ShopEnv()
    obs = env.reset()
    print('游戏开始！当前状态:', obs)
    
    history = []
    step_count = 1  # 步数编号

    timestamp_str = time.strftime('%Y%m%d_%H%M%S')
    save_dir = Path(f"./new_game_logs/{timestamp_str}")
    save_dir.mkdir(parents=True, exist_ok=True)
    history_file = save_dir / "history.jsonl"  # 每条写一行的JSON记录


    def save_message_to_file(msg, filename=None):
        if filename is None:
            with open(history_file, "a", encoding="utf-8") as f:
                json_str = json.dumps(msg, ensure_ascii=False, indent=2)  # 加 indent
                f.write(json_str + "\n\n")  # 分隔每条记录，便于阅读
                f.write("\n")  # 每条记录占一行
        else:
            with open(save_dir / filename, "a", encoding="utf-8") as f:
                json_str = json.dumps(msg, ensure_ascii=False, indent=2)  # 加 indent
                f.write(json_str + "\n\n")  # 分隔每条记录，便于阅读
                f.write("\n")  # 每条记录占一行


    def save_message_to_file_step(msg, step):
        file_path = save_dir / f"step_{step:03d}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(msg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 写入 {file_path} 失败: {e}")

    MAX_RETRY = 3

    current_day = env.day

    while not env.done and env.day < 30:
        obs, _, _ = env._get_obs(), env.done, {}

        game_state = format_game_state(obs, GOODS_LIST)

        print(f"当前游戏状态: {game_state}")

        formatted_history = "\n".join([f"{m['role']}: {m['content']}" for m in history])

        user_prompt = user_prompt_template.format(
            game_state=game_state,
            dairies=env.format_history(),
            history_records=formatted_history
        )

        current_message = (
            [{"role": "system", "content": system_prompt}] +
            # history +
            [{"role": "user", "content": user_prompt}]
        )

        for retry_i in range(MAX_RETRY):
            try:
                reasoning_content, _, tool_infos = get_llm_response_tool_call(
                    client,
                    messages=current_message,
                    stream=True,
                    model_name=args.model,
                    tools=shop_env_tools,
                    extra_body={
                        "enable_thinking": args.enable_thinking,
                        "top_k": 50,
                    },
                    seed=42,
                    # stream_options={
                    #     'include_usage': False,
                    # },
                    temperature=0.9,
                    top_p=0.9,
                )

                if len(tool_infos) == 0:
                    raise Exception("没有进行正确格式的工具调用!")

                break  # 成功就跳出 retry 循环
            except Exception as e:
                print(f"⚠️ 第 {retry_i+1} 次调用 LLM 失败：{e}")
                if retry_i == MAX_RETRY - 1:
                    print("❌ 达到最大重试次数，跳过本步")
                    reasoning_content = "调用LLM失败"
                    answer_content = ""
                    tool_infos = []
                    break

        reasoning_content, answer_content, tool_infos = get_llm_response_tool_call(
            client,
            messages=current_message,
            stream=True,
            model_name="qwen3-32b",
            tools=shop_env_tools,
        )

        save_message_to_file(
            {
                'reasoning_content': reasoning_content,
                'answer_content': answer_content,
                'tool_infos': tool_infos[0] if len(tool_infos) > 0 else '',
                'message': current_message,
            },
            f"{step_count + 1}_llm_call_and_response.json"
        )

        if len(tool_infos) == 0:
            continue

        new_message = {
            "role": "assistant",
            "content": (
                # f"🧠 **LLM 推理内容**：\n{reasoning_content}\n\n"
                f"🔧 **工具调用信息**：\n{json.dumps(tool_infos, ensure_ascii=False, indent=2)}"
            )
        }

        if env.day == current_day:
            history.append(new_message)
        else:
            history = []
            current_day = env.day

        save_message_to_file({
            'game_state': env._debug_obs(),
            'reason_content': reasoning_content,
            **new_message,
        })

        print("LLM推理过程:", reasoning_content)
        print("LLM工具调用:", tool_infos)

        if len(tool_infos) > 0:
            result_str = execute_tool_call_with_output(env, tool_infos[0])

            new_message = {
                "role": "user", "content": result_str,
            }

            if env.day == current_day:
                history.append(new_message)
            else:
                history = []
                current_day = env.day

            save_message_to_file({
                'game_state': env._debug_obs(),
                **new_message,
            })

        save_message_to_file_step(
            {
                'history': history,
                'game_state': env._debug_obs(),
                'args': {
                    'model': args.model,
                    'enable_thinking': args.enable_thinking,
                },
            },
            step_count,
        )

        step_count += 1




if __name__ == '__main__':
    random.seed(42)  # 设置全局随机种子
    main() 
