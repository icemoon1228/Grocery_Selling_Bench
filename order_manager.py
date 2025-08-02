import random
from settings import GOODS_LIST

class OrderManager:
    def __init__(
        self,
        total_orders=1000,
        cate_ratio=None,
        total_amount=None,
        min_per_order=1,
        max_per_order=10,
        use_item_ratio=True,  # 新增：是否直接使用商品级采样比例
    ):
        """
        cate_ratio: list[float], 每个商品的采样权重（长度等于 GOODS_LIST）
        total_amount: int, 所有订单商品数量之和（严格等于）
        min_per_order, max_per_order: 每单最小/最大商品总数
        use_item_ratio: bool, 是否启用按商品比例采样（否则按类别采样）
        """
        self.orders = []
        self._generate_orders(
            total_orders, cate_ratio, total_amount, min_per_order, max_per_order, use_item_ratio
        )

    def _generate_orders(self, total_orders, cate_ratio, total_amount, min_per_order, max_per_order, use_item_ratio):
        order_id = 0
        N = len(GOODS_LIST)

        if not use_item_ratio:
            # == 原始类别逻辑（按 cate 分类后生成）
            all_cates = list(set(g['cate'] for g in GOODS_LIST))
            if cate_ratio is None:
                cate_ratio = {c: 1 / len(all_cates) for c in all_cates}
            cate_order_num = {c: int(total_orders * cate_ratio.get(c, 0)) for c in all_cates}
            remain = total_orders - sum(cate_order_num.values())
            for i in range(remain):
                cate_order_num[all_cates[i % len(all_cates)]] += 1
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
            return

        # == 新逻辑：按商品级别采样 ==
        if cate_ratio is None:
            cate_ratio = [1 / N for _ in range(N)]
        else:
            assert len(cate_ratio) == N, "cate_ratio 的长度必须等于商品数"

        goods_ids = list(range(N))

        if total_amount is not None:
            # 分配每个订单的总商品数量
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
        else:
            order_amounts = [random.randint(min_per_order, max_per_order) for _ in range(total_orders)]

        for order_idx in range(total_orders):
            amount = order_amounts[order_idx]
            n_items = random.randint(1, min(10, amount))
            sampled_ids = random.choices(goods_ids, weights=cate_ratio, k=n_items)
            unique_ids = list(set(sampled_ids))
            n_unique = len(unique_ids)

            base_num = amount // n_unique
            left_num = amount - base_num * n_unique
            nums = [base_num] * n_unique
            for i in range(left_num):
                nums[i] += 1

            order = {
                'order_id': order_id,
                'items': [
                    {'id': gid, 'num': nums[i]}
                    for i, gid in enumerate(unique_ids)
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

# 示例测试代码
if __name__ == '__main__':
    ratio = [1 for _ in range(len(GOODS_LIST))]
    ratio[0] = 5   # 强化第一个商品权重
    ratio[1] = 3
    om = OrderManager(
        total_orders=10,
        total_amount=100,
        min_per_order=3,
        max_per_order=15,
        cate_ratio=ratio,
        use_item_ratio=True
    )
    print(f'总订单数: {om.left()}')
    orders = om.pop(5)
    print('弹出5个订单:')
    for idx, order in enumerate(orders, 1):
        print(f'订单{idx} (order_id={order["order_id"]}):')
        for item in order['items']:
            good = GOODS_LIST[item['id']]
            print(f"  商品: {good['name']} (类别: {good['cate']}), 数量: {item['num']}")
    print(f'剩余订单数: {om.left()}')

    all_orders = orders + om.pop(om.left())
    total = sum(item['num'] for order in all_orders for item in order['items'])
    print(f'所有订单商品数量总和: {total}')