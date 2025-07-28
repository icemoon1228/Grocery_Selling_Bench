def format_goods_list(goods_list):
    lines = ["【商品列表】每项包括：编号｜名称｜进价｜售价｜类别"]
    for item in goods_list:
        line = f"{item['id']:>2}｜{item['name']}｜进价：{item['buy_price']}｜售价：{item['sell_price']}｜{item['cate']}"
        lines.append(line)
    return "\n".join(lines)

def format_game_state(obs, goods_list):
    # cash = obs['cash']
    time_left = obs['time_left']
    day = obs['day']
    # inventory = obs['inventory']

    # inventory_lines = ["【当前库存】每项包括：编号｜名称｜库存数量"]
    # for i, qty in enumerate(inventory):
    #     name = goods_list[i]['name']
    #     inventory_lines.append(f"{i:>2}｜{name}｜{qty}件")

    return (
        f"【当前游戏状态】\n"
        f"- 第 {day} 天\n"
        # f"- 当前资金：￥{cash:.2f}\n"
        f"- 剩余时间：{time_left:.1f} 分钟\n"
        # + "\n".join(inventory_lines)
    )

def format_game_state_total(obs, goods_list):
    cash = obs['cash']
    time_left = obs['time_left']
    day = obs['day']
    inventory = obs['inventory']
    orders = obs.get('orders', [])
    pending_deliveries = obs.get('pending_deliveries', [])

    # 当前库存
    inventory_lines = ["【当前库存】每项包括：编号｜名称｜库存数量"]
    for i, qty in enumerate(inventory):
        name = goods_list[i]['name']
        inventory_lines.append(f"{i:>2}｜{name}｜{qty}件")

    # 客户订单（待售）
    order_lines = ["【客户订单】每项包括：订单ID｜商品名称×数量"]
    if orders:
        for o in orders:
            order_id = o['order_id']
            items_str = "，".join([
                f"{goods_list[item['id']]['name']}×{item['num']}" for item in o['items']
            ])
            order_lines.append(f"订单 {order_id}｜{items_str}")
    else:
        order_lines.append("暂无客户订单。")

    # 待到货订单（购物订单）
    delivery_lines = ["【待到货订单】每项包括：订单ID｜预计到货日｜商品名称×数量"]
    if pending_deliveries:
        for d in pending_deliveries:
            order_id = d.get('order_id', '—')  # 若未设置order_id也能展示
            arrival_day = d['arrival_day']
            goods_str = "，".join([
                f"{goods_list[i]['name']}×{qty}" for i, qty in enumerate(d['goods']) if qty > 0
            ])
            delivery_lines.append(f"订单 {order_id}｜第 {arrival_day} 天｜{goods_str}")
    else:
        delivery_lines.append("暂无待到货订单。")

    # 拼接整体输出
    return (
        f"【当前游戏状态】\n"
        f"- 第 {day} 天\n"
        f"- 当前资金：￥{cash:.2f}\n"
        f"- 剩余时间：{time_left:.1f} 分钟\n\n"
        + "\n".join(inventory_lines) + "\n\n"
        + "\n".join(order_lines) + "\n\n"
        + "\n".join(delivery_lines)
    )