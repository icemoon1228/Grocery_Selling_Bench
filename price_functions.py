import math

def periodic_price_function(day: int, base_value: float, period: int) -> float:
    """
    正弦波模拟周期波动。
    波动范围：[0.8 * base_value, 1.2 * base_value]
    """
    amplitude = 0.2 * base_value  # 幅度为20%
    offset = base_value           # 平移中心为base_value
    radians = (2 * math.pi * day) / period
    return max(0, offset + amplitude * math.sin(radians))
    

def triangle_wave(day: int, base_value: float, period: int) -> float:
    """
    三角波模拟周期波动：先线性上升，再线性下降。
    波动范围：[base_value, base_value * 1.3]
    """
    half = period / 2
    phase = day % period
    if phase < half:
        return base_value + (0.3 * base_value) * (phase / half)
    else:
        return base_value + (0.3 * base_value) * ((period - phase) / half)


def exponential_fluctuation(day: int, base_value: float, period: int) -> float:
    """
    指数抖动模拟周期波动，整体偏增长趋势。
    波动范围：[base_value, base_value * 1.2]
    """
    fluct = (math.sin(2 * math.pi * day / period) + 1) / 2  # [0, 1]
    return base_value * (1 + 0.2 * math.pow(fluct, 2))      # 波动偏向高值