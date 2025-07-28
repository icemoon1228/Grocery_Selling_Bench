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
        self.max_time = 480  # 每天最大分钟数
        self.n_goods = N_GOODS
        self.max_total_inventory = MAX_TOTAL_INVENTORY
        self.day = 1
        self.cash = 10000
        self.inventory = [INITIAL_ITEM_NUMBER for _ in range(self.n_goods)]
        self.order_manager = OrderManager(total_orders=1000, total_amount=10000, min_per_order=5, max_per_order=15)
        self.time_left = self.max_time
        self.day = 1
        self.done = False
        self.today_orders = self.get_today_order()
        self.pending_deliveries = []
        self.buy_order_counter = 1 
        self.reset()

    def reset(self):
        self.cash = 10000
        self.inventory = [INITIAL_ITEM_NUMBER for _ in range(self.n_goods)]
        self.order_manager = OrderManager(total_orders=1000, total_amount=10000, min_per_order=5, max_per_order=15)
        self.time_left = self.max_time
        self.day = 1
        self.done = False
        self.today_orders = self.get_today_order()
        self.pending_deliveries = []
        self.buy_order_counter = 1 
        return self._get_obs()

    def step(self, action, params=None):
        if self.done:
            return self._get_obs(), self.done, {}
        time_cost = self._get_time_cost(action)
        self.time_left -= time_cost
        action_res = None
        if action == 'view_orders':  # 查看订单
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
        if self.time_left <= 0:
            self._settle_day()
            self.time_left = self.max_time
            self.day += 1
        return self._get_obs(), self.done, action_res,

    def get_orders_id(self):
        return [o['order_id'] for o in self.today_orders]

    def get_today_order(self):
        """
        每7天为周期, 前5天订单数8-12随机, 后2天20-30随机, 返回今日订单列表
        """
        day_in_week = (self.day - 1) % 7 + 1
        if 1 <= day_in_week <= 5:
            n = random.randint(20, 30)
        else:
            n = random.randint(50, 66)
        return self.order_manager.pop(n)
    
    def _get_time_cost(self, action):
        time_costs = {
            'view_orders': 10,
            'buy_goods': 60,
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
            return {
                'status': 'failed',
                'reason': '参数错误'
            }
        total_buy = [0 for _ in range(self.n_goods)]
        total_cost = 0
        for order in params['orders']:
            gid = order['id']
            num = order['num']
            if gid < 0 or gid >= self.n_goods or num <= 0:
                continue
            total_buy[gid] += num
            total_cost += GOODS_LIST[gid]['buy_price'] * num
        if self.cash < total_cost:
            return {
                'status': 'failed',
                'reason': '余额不足'
            }
        if sum(self.inventory[i] + total_buy[i] for i in range(self.n_goods)) > self.max_total_inventory:
            return {
                'status': 'failed',
                'reason': '库存不足'
            }
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
        # params: {'order_id': int}
        if not params or 'order_id' not in params:
            return {
                'status': 'failed',
                'reason': '参数错误'
            }
        order_id = int(params['order_id'])
        # 查找订单
        order = None
        # 由于订单是每日pop出来的，建议你在环境中保存今日订单列表
        for o in self.today_orders:
            if o['order_id'] == order_id:
                order = o
                break
        if order is None:
            return {
                'status': 'failed',
                'reason': '未找到当前订单',
                # 'meta': {
                #     'order_ids': self.get_orders_id(),
                # }
            }
        for item in order['items']:
            gid = item['id']
            num = item['num']
            if self.inventory[gid] < num:
                return {
                    'status': 'failed',
                    'reason': '库存不足',
                    # 'meta': {
                    #     'order_ids': self.get_orders_id(),
                    # }
                }
        # 扣减库存并加钱
        for item in order['items']:
            gid = item['id']
            num = item['num']
            self.inventory[gid] -= num
            self.cash += GOODS_LIST[gid]['sell_price'] * num

        self.today_orders.remove(order)

        return {
            'status': 'success'
        }

    def _wait_time(self, params=None):
        pass

    def _view_orders(self, params=None):
        return self.today_orders
    
    def _view_cash(self, params=None):
        return self.cash
    
    def _view_inventory(self, params=None):
        return self.inventory
    
    def _view_incoming_goods(self, params=None):
        return self.pending_deliveries, self.day

    def _view_goods_price_list(self, params=None):
        return GOODS_LIST

    def _settle_day(self):
        self.cash -= RENT
        for i in range(self.n_goods):
            loss = int(self.inventory[i] * LOSS_RATE)
            self.inventory[i] -= loss

        # 处理到货
        new_pending = []
        for delivery in self.pending_deliveries:
            if delivery['arrival_day'] <= self.day:
                for i in range(self.n_goods):
                    self.inventory[i] += delivery['goods'][i]
            else:
                new_pending.append(delivery)
        self.pending_deliveries = new_pending

        self.today_orders = self.get_today_order()
        if self.cash < 0:
            self.done = True

    def _get_obs(self):
        return {
            'time_left': float(self.time_left),
            'day': self.day,
        }

    def _view_inventory(self):
        """
        返回当前库存信息, 每个商品包含id、name、库存数量
        """
        return [
            {
                'id': g['id'],
                'name': g['name'],
                'num': self.inventory[g['id']]
            }
            for g in GOODS_LIST
        ] 

    def _debug_obs(self):
        return {
            'cash': float(self.cash),
            'inventory': self.inventory[:],
            'time_left': float(self.time_left),
            'day': self.day,
            'orders': self.today_orders,
            'pending_deliveries': self.pending_deliveries,
        }