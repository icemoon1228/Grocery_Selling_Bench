# 商品常量定义
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
INITIAL_ITEM_NUMBER = 20


RENT = 500
LOSS_RATE = 0.1
DEPRECIATION_RATE = 0.6