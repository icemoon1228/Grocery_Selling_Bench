import random
from settings import GOODS_LIST

class OrderManager:
    def __init__(self, total_orders=1000, cate_ratio=None, total_amount=None, min_per_order=1, max_per_order=10):
        """
        cate_ratio: dict, 各类商品订单比例
        total_amount: int, 所有订单商品数量之和（严格等于）
        min_per_order, max_per_order: 每个订单商品数量的最小/最大值
        """
        self.orders = []
        self._generate_orders(total_orders, cate_ratio, total_amount, min_per_order, max_per_order)

    def _generate_orders(self, total_orders, cate_ratio, total_amount, min_per_order, max_per_order):
        all_cates = list(set(g['cate'] for g in GOODS_LIST))
        if cate_ratio is None:
            cate_ratio = {c: 1/len(all_cates) for c in all_cates}
        cate_order_num = {c: int(total_orders * cate_ratio.get(c, 0)) for c in all_cates}
        remain = total_orders - sum(cate_order_num.values())
        for i in range(remain):
            cate_order_num[all_cates[i % len(all_cates)]] += 1
        order_id = 0
        if total_amount is not None:
            order_amounts = [min_per_order] * total_orders
            left = total_amount - min_per_order * total_orders
            max_add = [max_per_order - min_per_order for _ in range(total_orders)]
            idxs = list(range(total_orders))
            while left > 0 and idxs:
                i = random.choice(idxs)
                if max_add[i] > 0:
                    order_amounts[i] += 1
                    max_add[i] -= 1
                    left -= 1
                if max_add[i] == 0:
                    idxs.remove(i)
            order_idx = 0
            for cate, num in cate_order_num.items():
                goods_in_cate = [g for g in GOODS_LIST if g['cate'] == cate]
                for _ in range(num):
                    n_items = random.randint(1, min(10, len(goods_in_cate), order_amounts[order_idx]))
                    items = random.sample(goods_in_cate, n_items)
                    base_num = order_amounts[order_idx] // n_items
                    left_num = order_amounts[order_idx] - base_num * n_items
                    nums = [base_num] * n_items
                    for i in range(left_num):
                        nums[i] += 1
                    order = {
                        'order_id': order_id,
                        'items': [
                            {'id': g['id'], 'num': nums[i]}
                            for i, g in enumerate(items)
                        ]
                    }
                    self.orders.append(order)
                    order_id += 1
                    order_idx += 1
                    if order_idx >= total_orders:
                        break
                if order_idx >= total_orders:
                    break
        else:
            for cate, num in cate_order_num.items():
                goods_in_cate = [g for g in GOODS_LIST if g['cate'] == cate]
                for _ in range(num):
                    n_items = random.randint(1, 10)
                    items = random.sample(goods_in_cate, min(n_items, len(goods_in_cate)))
                    order = {
                        'order_id': order_id,
                        'items': [
                            {'id': g['id'], 'num': random.randint(1, 10)}
                            for g in items
                        ]
                    }
                    self.orders.append(order)
                    order_id += 1
        random.shuffle(self.orders)

    def pop(self, n=1):
        res = self.orders[:n]
        self.orders = self.orders[n:]
        return res

    def left(self):
        return len(self.orders)

if __name__ == '__main__':
    om = OrderManager(total_orders=10, total_amount=100, min_per_order=3, max_per_order=15)
    print(f'总订单数: {om.left()}')
    orders = om.pop(5)
    print('弹出5个订单:')
    for idx, order in enumerate(orders, 1):
        print(f'订单{idx} (order_id={order["order_id"]}):')
        for item in order['items']:
            good = next(g for g in GOODS_LIST if g['id'] == item['id'])
            print(f"  商品: {good['name']} (类别: {good['cate']}), 数量: {item['num']}")
    print(f'剩余订单数: {om.left()}')
    # 验证总和
    all_orders = orders + om.pop(om.left())
    total = sum(item['num'] for order in all_orders for item in order['items'])
    print(f'所有订单商品数量总和: {total}') 

    

    