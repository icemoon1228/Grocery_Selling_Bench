from pathlib import Path
import time
from format import format_game_state, format_game_state_total
from llm_response import get_llm_response, get_llm_response_tool_call, client
import json

# shop_env_tools: MCP风格工具描述，供LLM tool_call使用
shop_env_tools = [
    {
        "type": "function",
        "function": {
            "name": "view_orders",
            "description": "查看当前所有订单信息，消耗10分钟。",
            "parameters": {
                "properties": {},
                "required": [],
                "type": "object"
            }
        }
    },
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
                            "required": ["id", "num", "arrive"]
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
    {
        "type": "function",
        "function": {
            "name": "view_inventory",
            "description": "查看当前库存状况, 展示所有商品的库存数量。消耗20分钟。",
            "parameters": {
                "properties": {},
                "required": [],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "view_cash",
            "description": "查看当前剩余的现金。消耗1分钟。",
            "parameters": {
                "properties": {},
                "required": [],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "view_incoming_goods",
            "description": "查看所有尚未到货的进货订单，包括商品id、数量、预计到货时间。消耗5分钟。",
            "parameters": {
                "properties": {},
                "required": [],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "view_goods_price_list",
            "description": "查看所有商品的基本信息，包括名称、进价、售价和类别。用于分析利润空间。",
            "parameters": {
                "properties": {},
                "required": [],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait_time",
            "description": "等待今日时间流逝",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },

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
            result_str = f"✅ 已售出订单 ID {arguments.get('order_id')}。"
        else:
            result_str = f"❌ 售出订单 ID {arguments.get('order_id')} 失败, 原因为{tool_res['reason']}。"

    elif name == 'view_goods_price_list':
        result_str = "📦 货品价格列表：\n" + "\n".join(
            [f"- {item['name']}：进价￥{item['buy_price']:.2f}, 售价￥{item['sell_price']:.2f}" for item in tool_res]
        )
    
    elif name == 'wait_time':
        result_str = '✅ 已等待时间流逝.'

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

user_prompt_template = f"""你是门店的智能经营管家，请根据过去的经营历史与当前的门店状态, 判断当前应执行的最优操作：

【门店状态】
{{game_state}}

请你基于上述信息做出判断，并输出明确、可执行的下一步行动建议。若需要使用工具，请说明用途及调用方式，并且每一次只能调用一次工具。不要输出与任务无关的内容。
"""

def main():
    env = ShopEnv()
    obs = env.reset()
    print('游戏开始！当前状态:', obs)
    
    history = []
    step_count = 1  # 步数编号

    timestamp_str = time.strftime('%Y%m%d_%H%M%S')
    save_dir = Path(f"./game_logs/{timestamp_str}")
    save_dir.mkdir(parents=True, exist_ok=True)
    history_file = save_dir / "history.jsonl"  # 每条写一行的JSON记录

    def save_message_to_file(msg):
        with open(history_file, "a", encoding="utf-8") as f:
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

    while not env.done and env.day < 15:
        # history_text = "\n".join([f"[{msg['role']}]: {msg['content']}" for msg in history[-50:]])

        obs, _, _ = env._get_obs(), env.done, {}

        game_state = format_game_state(obs, GOODS_LIST)

        print(f"当前游戏状态: {game_state}")

        user_prompt = user_prompt_template.format(game_state=game_state)

        current_message = (
            [{"role": "system", "content": system_prompt}] +
            history[:50] +
            [{"role": "user", "content": user_prompt}]
        )

        reasoning_content, answer_content, tool_infos = get_llm_response_tool_call(
            client,
            messages=current_message,
            stream=True,
            model_name="qwen3-32b",
            tools=shop_env_tools,
        )

        new_message = {
            "role": "assistant",
            "content": (
                f"🧠 **LLM 推理内容**：\n{reasoning_content}\n\n"
                f"🔧 **工具调用信息**：\n{json.dumps(tool_infos, ensure_ascii=False, indent=2)}"
            )
        }

        history.append(new_message)

        save_message_to_file({
            # 'game_state': format_game_state_total(env._debug_obs(), GOODS_LIST),
            **new_message
        })

        print("LLM推理过程:", reasoning_content)
        print("LLM工具调用:", tool_infos)

        if len(tool_infos) > 0:
            result_str = execute_tool_call_with_output(env, tool_infos[0])

            new_message = {
                "role": "user", "content": result_str,
            }

            history.append(new_message)

            save_message_to_file({
                # 'game_state': format_game_state_total(env._debug_obs(), GOODS_LIST),
                **new_message
            })

        save_message_to_file_step(history, step_count)

        step_count += 1




if __name__ == '__main__':
    main() 
