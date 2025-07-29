# 商品常量定义
from collections import defaultdict


GOODS_LIST = [
    {"id": 0, "name": "小麦（中等）", "buy_price": 3.19, "sell_price": 5.9, "cate": "粮食"},
    {"id": 1, "name": "玉米（中等）", "buy_price": 2.52, "sell_price": 4.62, "cate": "粮食"},
    {"id": 2, "name": "大豆（中等）", "buy_price": 7.22, "sell_price": 12.2, "cate": "粮食"},
    {"id": 3, "name": "籼米（中等）", "buy_price": 5.25, "sell_price": 7, "cate": "粮食"},
    {"id": 4, "name": "猪肉（去骨统肉）", "buy_price": 24.67, "sell_price": 32.2, "cate": "畜禽产品"},
    {"id": 5, "name": "牛肉（去骨统肉）", "buy_price": 69.29, "sell_price": 95, "cate": "畜禽产品"},
    {"id": 6, "name": "羊肉（去骨统肉）", "buy_price": 68.29, "sell_price": 85, "cate": "畜禽产品"},
    {"id": 7, "name": "鸡肉（去骨统肉）", "buy_price": 21.22, "sell_price": 28.2, "cate": "畜禽产品"},
    {"id": 8, "name": "鸡蛋（普通鲜蛋）", "buy_price": 9, "sell_price": 12, "cate": "蛋类"},
    {"id": 9, "name": "草鱼（1-2公斤）", "buy_price": 20.51, "sell_price": 26.2, "cate": "海鲜"},
    {"id": 10, "name": "鲤鱼（中等）", "buy_price": 16.15, "sell_price": 18, "cate": "海鲜"},
    {"id": 11, "name": "鲢鱼（中等）", "buy_price": 13.15, "sell_price": 20.1, "cate": "海鲜"},
    {"id": 12, "name": "大白菜（中等）", "buy_price": 2.73, "sell_price": 6, "cate": "蔬菜"},
    {"id": 13, "name": "黄瓜", "buy_price": 4.71, "sell_price": 8.5, "cate": "蔬菜"},
    {"id": 14, "name": "西红柿", "buy_price": 7.1, "sell_price": 12, "cate": "蔬菜"},
    {"id": 15, "name": "红富士苹果（中等）", "buy_price": 12.5, "sell_price": 14.4, "cate": "水果"},
    {"id": 16, "name": "香蕉（中等）", "buy_price": 7.5, "sell_price": 15.2, "cate": "水果"},
    {"id": 17, "name": "橙子（中等）", "buy_price": 10.88, "sell_price": 16.4, "cate": "水果"},
]
N_GOODS = len(GOODS_LIST)
MAX_TOTAL_INVENTORY = 1000  # 所有商品共享的最大库存总量 
INITIAL_ITEM_NUMBER = 30

QUANTITY_LIST = [
    500,  # 小麦（中等） - 主粮，需求大
    450,  # 玉米（中等） - 主粮，家畜饲料常用
    300,  # 大豆（中等） - 用途广，但价格较高
    400,  # 籼米（中等） - 主粮，常用
    150,  # 猪肉 - 消耗大，保鲜期短
    60,   # 牛肉 - 单价高，需求相对少
    60,   # 羊肉 - 同上
    200,  # 鸡肉 - 性价比高，需求适中
    250,  # 鸡蛋 - 常用食材，需求大
    180,  # 草鱼 - 普通海鲜，适中需求
    120,  # 鲤鱼 - 常见海鲜，适中
    130,  # 鲢鱼 - 相对廉价，适中
    300,  # 大白菜 - 冬季常用菜，便宜
    220,  # 黄瓜 - 应季蔬菜
    220,  # 西红柿 - 常见日常食材
    160,  # 红富士苹果 - 水果但相对耐放
    180,  # 香蕉 - 热门水果，但易坏
    170   # 橙子 - 应季水果，适中
]

cate_quantity = defaultdict(int)

for i in range(N_GOODS):
    cate = GOODS_LIST[i]["cate"]
    qty = QUANTITY_LIST[i]
    cate_quantity[cate] += qty

# 计算总库存
total_qty = sum(QUANTITY_LIST)

# 按比例归一化
CATE_RATIO = {cate: round(qty / total_qty, 6) for cate, qty in cate_quantity.items()}

RENT = 1000
LOSS_RATE = 0.1
DEPRECIATION_RATE = 0.6