# 商品常量定义
from collections import defaultdict
import random
from tracemalloc import start
from price_functions import periodic_price_function, triangle_wave, exponential_fluctuation
from config import ENABLE_SELL_PRICE_CIRCLE, ENABLE_BUY_PRICE_CIRCLE, ENABLE_REQUIRE_CIRCLE, ENABLE_BUY_REQUIRE_SAME_CIRCLE

### 销量上去 ====> 价格上去  进货4-5 天
## TODO: 过去很重要场景 !销量 价格 ===> 变化 最大库存限制  ===> 订货决策  insight 
## TODO: 
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

val_functions = [
    periodic_price_function,
    triangle_wave,
    exponential_fluctuation,
]

def sell_price_function(obj, base_value=0):
    day = obj["day"]
    period = random.randint(8, 10)

    start_position = random.randint(0, period)
    price_fc = val_functions[random.randint(0, 2)]

    return price_fc(day + start_position, base_value, period)

def buy_price_function(obj, base_value=0):
    day = obj["day"]
    period = random.randint(8, 10)
    start_position = random.randint(0, period)
    price_fc = val_functions[random.randint(0, 2)]

    return price_fc(day + start_position, base_value, period)

def require_function(obj, base_value=0):
    day = obj["day"]
    period = random.randint(8, 10)
    start_position = random.randint(0, period)
    price_fc = val_functions[random.randint(0, 2)]
    return price_fc(day + start_position, base_value, period)

# 添加统一的 lambda price_function
for item in GOODS_LIST:
    if ENABLE_BUY_PRICE_CIRCLE:
        item["sell_price_function"] = lambda obj: round(sell_price_function(obj, base_value=obj["sell_price"]), 2) 
    else:
        item["sell_price_function"] = lambda obj: obj["sell_price"]
    
    if ENABLE_SELL_PRICE_CIRCLE:
        item["buy_price_function"] = lambda obj: round(buy_price_function(obj, base_value=obj["buy_price"]), 2) 
    else:
        item["buy_price_function"] = lambda obj: obj["buy_price"]

    if ENABLE_REQUIRE_CIRCLE:
        item["require_function"] = lambda obj: round(require_function(obj, base_value=1), 2)
    else:
        item["require_function"] = lambda obj: 1

    if ENABLE_BUY_REQUIRE_SAME_CIRCLE:
        item["require_function"] = lambda obj: round(sell_price_function(obj, base_value=1), 2) 
        item["sell_price_function"] = lambda obj: round(sell_price_function({"day": obj["day"] + 2, **obj}, base_value=obj["sell_price"]), 2) 

N_GOODS = len(GOODS_LIST)
MAX_TOTAL_INVENTORY = 1000  # 所有商品共享的最大库存总量 
INITIAL_ITEM_NUMBER = 30


# 按比例归一化

RENT = 3000
LOSS_RATE = 0.3
DEPRECIATION_RATE = 0.6