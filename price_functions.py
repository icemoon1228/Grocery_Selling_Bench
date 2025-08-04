import math

def periodic_price_function(day: int, base_value: float, period: int) -> float:
    """
    正弦波模拟周期波动。
    波动范围：[0.2 * base_value, 1.8 * base_value]，幅度为 ±0.8 * base_value
    """
    amplitude = 0.8 * base_value
    offset = base_value
    radians = (2 * math.pi * day) / period
    return max(0, offset + amplitude * math.sin(radians))


def triangle_wave(day: int, base_value: float, period: int) -> float:
    """
    三角波模拟周期波动。
    波动范围：[0.2 * base_value, 1.8 * base_value]
    """
    half = period / 2
    phase = day % period
    if phase < half:
        return base_value * 0.2 + (1.6 * base_value) * (phase / half)
    else:
        return base_value * 0.2 + (1.6 * base_value) * ((period - phase) / half)


def exponential_fluctuation(day: int, base_value: float, period: int) -> float:
    """
    指数抖动模拟周期波动，整体偏增长趋势。
    波动范围：[0.2 * base_value, 1.8 * base_value]
    """
    # 原 fluct ∈ [0, 1]，使用指数函数映射为 [0.2, 1.8]
    fluct = (math.sin(2 * math.pi * day / period) + 1) / 2  # ∈ [0, 1]
    scale = 0.2 + 1.6 * math.pow(fluct, 2)  # ∈ [0.2, 1.8]
    return base_value * scale