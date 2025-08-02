from settings import N_GOODS, MAX_TOTAL_INVENTORY, GOODS_LIST, RENT, LOSS_RATE, DEPRECIATION_RATE, INITIAL_ITEM_NUMBER
import random
from order_manager import OrderManager


class ShopEnv:
    """
    经营类游戏环境：每天480分钟，不同动作消耗不同时间。
    动作：查看订单、进货、售出订单、收银。
    状态：现金、库存、剩余时间、日期。
    """
    def __init__(self):
        self.max_time = 480
        self.n_goods = N_GOODS
        self.max_total_inventory = MAX_TOTAL_INVENTORY
        self.day = 1
        self.reset()

    def reset(self):
        self.cash = 10000
        self.inventory = [INITIAL_ITEM_NUMBER for _ in range(self.n_goods)]
        
        self.time_left = self.max_time
        self.day = 1
        self.done = False
        self.update_goods_state_by_day(self.day)  # 初始化每日价格
        self.update_order_state_by_day(self.day)
        
        self.pending_deliveries = []
        self.buy_order_counter = 0
        self.sell_order_count = 0
        

        self._init_action_stats()
        self.history = []
        return self._get_obs()


    def update_goods_state_by_day(self, day):
        today_supply = []
        for g in GOODS_LIST:
            ctx = {"day": day}
            g["current_buy_price"] = g["buy_price_function"](ctx)
            g["current_sell_price"] = g["sell_price_function"](ctx)
            g["today_supply_strength"] = g["require_function"](ctx)
            today_supply.append(g['today_supply_strength'])

        self.supply_ratio = [supply / sum(today_supply) for supply in today_supply]

        self.supply_order_count = self.get_today_order_count()

        self.supply_count = self.supply_order_count * 25

    def update_order_state_by_day(self, day):
        self.order_manager = OrderManager(
            cate_ratio=self.supply_ratio,
            total_orders=self.supply_order_count,
            total_amount=self.supply_count,
            use_item_ratio=True,
            min_per_order=10,
            max_per_order=50,
        )
        self.today_orders = self.order_manager.pop(self.supply_count)

        self.today_total_order = self.today_orders.copy()

    def _init_action_stats(self):
        self.action_stats = {
            'view_orders': {'total': 0},
            'buy_goods': {'total': 0, 'success': 0, 'fail': 0},
            'sell_order': {'total': 0, 'success': 0, 'fail': 0},
            'view_cash': {'total': 0},
            'view_inventory': {'total': 0},
            'view_incoming_goods': {'total': 0},
            'view_goods_price_list': {'total': 0},
            'wait_time': {'total': 0},
            'view_history': {'total': 0},
        }

    def step(self, action, params=None):
        if self.done:
            return self._get_obs(), self.done, {}
        time_cost = self._get_time_cost(action)
        self.time_left -= time_cost
        action_res = None
        if action == 'view_orders':
            action_res = self._view_orders(params)
        elif action == 'buy_goods':
            action_res = self._buy_goods(params)
        elif action == 'sell_order':
            action_res = self._sell_order(params)
        elif action == 'view_cash':
            action_res = self._view_cash()
        elif action == 'view_inventory':
            action_res = self._view_inventory()
        elif action == 'view_incoming_goods':
            action_res = self._view_incoming_goods()
        elif action == 'view_goods_price_list':
            action_res = self._view_goods_price_list()
        elif action == 'wait_time':
            action_res = self._wait_time()
        elif action == 'view_history':
            action_res = self._view_history()

        self.action_stats[action]['total'] += 1

        if isinstance(action_res, dict) and 'status' in action_res:
            if action_res['status'] == 'success':
                self.action_stats[action]['success'] += 1
            else:
                self.action_stats[action]['fail'] += 1

        if self.time_left <= 0:
            self._settle_day()
            self.day += 1

            self.update_goods_state_by_day(self.day)
            self.update_order_state_by_day(self.day)

            self.time_left = self.max_time
        return self._get_obs(), self.done, action_res,

    def get_orders_id(self):
        return [o['order_id'] for o in self.today_orders]

    def get_today_order_count(self):
        day_in_week = (self.day - 1) % 7 + 1
        if 1 <= day_in_week <= 5:
            n = random.randint(20, 30)
        else:
            n = random.randint(50, 66)
        return n

    def _get_time_cost(self, action):
        time_costs = {
            'view_orders': 10,
            'buy_goods': 20,
            'sell_order': 10,
            'view_cash': 1,
            'view_inventory': 20,
            'view_incoming_goods': 5,
            'view_goods_price_list': 10,
            'wait_time': 600,
        }
        return time_costs.get(action, 0)

    def _buy_goods(self, params=None):
        if not params or 'orders' not in params:
            return {'status': 'failed', 'reason': '参数错误'}
        total_buy = [0 for _ in range(self.n_goods)]
        total_cost = 0
        for order in params['orders']:
            gid = order['id']
            num = order['num']
            if gid < 0 or gid >= self.n_goods or num <= 0:
                continue
            total_buy[gid] += num
            total_cost += GOODS_LIST[gid]['current_buy_price'] * num
        if self.cash < total_cost:
            return {'status': 'failed', 'reason': '余额不足'}
        if sum(self.inventory[i] + total_buy[i] for i in range(self.n_goods)) > self.max_total_inventory:
            return {'status': 'failed', 'reason': '库存不足'}

        for i in range(self.n_goods):
            self.inventory[i] += total_buy[i]
        self.cash -= total_cost
        order_id = self.buy_order_counter
        self.buy_order_counter += 1

        delay = random.randint(3, 5)
        arrival_day = self.day + delay
        self.pending_deliveries.append({
            'order_id': order_id,
            'arrival_day': arrival_day,
            'goods': total_buy
        })

        return {
            'status': 'success',
            'meta': {
                'order_id': order_id,
                'arrival_day': arrival_day,
                'goods': total_buy
            }
        }

    def _sell_order(self, params=None):
        if not params or 'order_id' not in params:
            return {'status': 'failed', 'reason': '参数错误'}
        order_id = int(params['order_id'])
        order = next((o for o in self.today_orders if o['order_id'] == order_id), None)
        if order is None:
            return {'status': 'failed', 'reason': '未找到当前订单'}
        for item in order['items']:
            gid = item['id']
            num = item['num']
            if self.inventory[gid] < num:
                return {'status': 'failed', 'reason': '库存不足'}
        for item in order['items']:
            gid = item['id']
            num = item['num']
            self.inventory[gid] -= num
            self.cash += GOODS_LIST[gid]['current_sell_price'] * num
        self.today_orders.remove(order)
        self.sell_order_count += 1
        return {'status': 'success'}

    
    def _settle_day(self):
        self.cash -= RENT
        for i in range(self.n_goods):
            loss = self.inventory[i] * LOSS_RATE
            self.inventory[i] -= loss
        new_pending = []
        for delivery in self.pending_deliveries:
            if delivery['arrival_day'] <= self.day:
                for i in range(self.n_goods):
                    self.inventory[i] += delivery['goods'][i]
            else:
                new_pending.append(delivery)
        self.pending_deliveries = new_pending
        if self.cash < 0:
            self.done = True

        self.history.append({
            **self._debug_obs(),
            'orders': self.today_total_order,
        })

    def _wait_time(self, params=None):
        return {}

    def _view_orders(self, params=None):
        return self.today_orders

    def _view_cash(self, params=None):
        return self.cash

    def _view_inventory(self, params=None):
        return [
            {
                'id': g['id'],
                'name': g['name'],
                'num': self.inventory[g['id']]
            } for g in GOODS_LIST
        ]

    def _view_incoming_goods(self, params=None):
        return self.pending_deliveries, self.day

    def _view_goods_price_list(self, params=None):
        return GOODS_LIST

    def view_goods_today_state(self):
        return [
            {
                'id': g['id'],
                'name': g['name'],
                'buy_price': round(g['current_buy_price'], 2),
                'sell_price': round(g['current_sell_price'], 2),
                'supply_strength': round(g['today_supply_strength'], 3),
            } for g in GOODS_LIST
        ]

    def _view_history(self, params=None):
        return self.history


    def _get_obs(self):
        return {
            'time_left': float(self.time_left),
            'day': self.day,
        }

    def _debug_obs(self):
        inventory_value = sum(
            self.inventory[i] * GOODS_LIST[i]['current_buy_price']
            for i in range(self.n_goods)
        )

        goods_list = [
            {
                'id': goods['id'],
                'name': goods['name'],
                'current_buy_price': goods['current_buy_price'],
                'current_sell_price': goods['current_sell_price'],
                'cate': goods['cate'],
            }
            for goods in GOODS_LIST
        ]

        total_asset = self.cash + inventory_value * DEPRECIATION_RATE
        return {
            'goods_list': goods_list,
            'cash': float(self.cash),
            'inventory': self.inventory[:],
            'time_left': float(self.time_left),
            'day': self.day,
            'orders': self.today_orders,
            'pending_deliveries': self.pending_deliveries,
            'sell_count': self.sell_order_count,
            'buy_count': self.buy_order_counter,
            'total_asset': total_asset,
            'action_stats': self.action_stats,
        }

    # def format_history(self):
    #     lines = []
    #     for _, snapshot in enumerate(self.history, start=1):
    #         day = snapshot['day']
    #         lines.append(f"=== 第 {day} 天 经营日志 ===")

    #         # 1. 现金 & 资产
    #         lines.append(f"该日最后现金余额结余: ¥{snapshot['cash']:.2f}")
    #         lines.append(f"该日最后资产总值结余: ¥{snapshot['total_asset']:.2f}")
    #         lines.append(f"截止当日总买入订单数: {snapshot['buy_count']}，总卖出订单数: {snapshot['sell_count']}")

    #         # 2. 库存信息（非0）
    #         inventory_strs = []
    #         for item, count in zip(snapshot['goods_list'], snapshot['inventory']):
    #             if count > 0:
    #                 inventory_strs.append(f"{item['name']} x {int(count)}")
    #         lines.append("截止当日当日库存: " + (", ".join(inventory_strs) if inventory_strs else "无"))

    #         # 3. 当日订单概览（只列 order_id 和商品项数）
    #         order_strs = [
    #             f"订单ID {o['order_id']}（共 {len(o['items'])} 项）"
    #             for o in snapshot['orders']
    #         ]
    #         lines.append("当日订单: " + (", ".join(order_strs) if order_strs else "无"))

    #         # 4. 待收货项
    #         delivery_strs = []
    #         for d in snapshot['pending_deliveries']:
    #             goods_list = [
    #                 f"{GOODS_LIST[i]['name']} x {int(num)}"
    #                 for i, num in enumerate(d['goods']) if num > 0
    #             ]
    #             delivery_strs.append(
    #                 f"订单ID {d['order_id']}，到达日: 第{d['arrival_day']}天，内容: {', '.join(goods_list)}"
    #             )
    #         lines.append("截止当日待收货订单:")
    #         if delivery_strs:
    #             lines.extend(["  - " + line for line in delivery_strs])
    #         else:
    #             lines.append("  无")

    #         lines.append("")  # 空行分隔每天

    #     return "\n".join(lines)
    def format_history(self):
        lines = []
        for _, snapshot in enumerate(self.history, start=1):
            day = snapshot['day']
            lines.append(f"=== 第 {day} 天 经营日志 ===")

            # 1. 现金 & 资产
            lines.append(f"该日最后现金余额结余: ¥{snapshot['cash']:.2f}")
            lines.append(f"该日最后资产总值结余: ¥{snapshot['total_asset']:.2f}")
            lines.append(f"截止当日总买入订单数: {snapshot['buy_count']}，总卖出订单数: {snapshot['sell_count']}")

            # 2. 商品价格概览
            lines.append("当日商品价格（进价/售价）:")
            for goods in GOODS_LIST:
                lines.append(
                    f"  - {goods['name']}: 进价 ¥{goods['current_buy_price']:.2f} / 售价 ¥{goods['current_sell_price']:.2f}"
                )

            # 3. 库存信息（非0）
            inventory_strs = []
            for item, count in zip(snapshot['goods_list'], snapshot['inventory']):
                if count > 0:
                    inventory_strs.append(f"{item['name']} x {count:.2f}")
            lines.append("截止当日库存: " + (", ".join(inventory_strs) if inventory_strs else "无"))

            # 4. 当日订单概览
            order_list = snapshot['orders']
            lines.append(f"当日订单总数: {len(order_list)}")

            # 统计每种商品在所有订单中的总需求数量
            total_goods_ordered = [0 for _ in range(self.n_goods)]
            for order in order_list:
                for item in order["items"]:
                    total_goods_ordered[item["id"]] += item["num"]

            # 输出订单信息
            # order_strs = [
            #     f"订单ID {o['order_id']}（共 {len(o['items'])} 项）"
            #     for o in order_list
            # ]
            # lines.append("订单简要列表: " + (", ".join(order_strs) if order_strs else "无"))

            # 输出商品统计
            lines.append("订单中各商品需求总量:")
            for i, count in enumerate(total_goods_ordered):
                if count > 0:
                    lines.append(f"  - {GOODS_LIST[i]['name']} x {int(count)}")

            # 5. 待收货项
            delivery_strs = []
            for d in snapshot['pending_deliveries']:
                goods_list = [
                    f"{GOODS_LIST[i]['name']} x {int(num)}"
                    for i, num in enumerate(d['goods']) if num > 0
                ]
                delivery_strs.append(
                    f"订单ID {d['order_id']}，到达日: 第{d['arrival_day']}天，内容: {', '.join(goods_list)}"
                )
            lines.append("截止当日待收货订单:")
            if delivery_strs:
                lines.extend(["  - " + line for line in delivery_strs])
            else:
                lines.append("  无")

            lines.append("")  # 空行分隔每天

        return "\n".join(lines)