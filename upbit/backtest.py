import pyupbit
import numpy as np
import trading_settings
import pandas as pd

symbol = trading_settings.symbol
k = trading_settings.k
expected_rate_p = trading_settings.expected_rate_p
partial_sell_rate = trading_settings.partial_sell_rate
emergency_sell_rate_p = trading_settings.emergency_sell_rate_p
candle_interval = trading_settings.candle_interval

# symbol="ETH"
# k = 0.4
# expected_rate_p = 3.0
# partial_sell_rate = 1.0 # 익절시 매도비율
# emergency_sell_rate_p = 3
# # candle_interval="minute60"
# candle_interval="minute240"

test_days=70
if candle_interval=="day":
    test_term=test_days
if candle_interval=="minute240":
    test_term=test_days*6
if candle_interval=="minute60":
    test_term=test_days*24
if candle_interval=="minute10":
    test_term=test_days*24*6
if candle_interval=="minute5":
    test_term=test_days*24*12
if candle_interval=="minute1":
    test_term=test_days*24*60

market="KRW-{}".format(symbol)
emergency_sell_rate = 1 - (emergency_sell_rate_p / 100)

def diff_percent(n):
    return round((n - 1) * 100, 2)

def get_middle(value1, value2, rate=0.5):
    return value1 + (value2 - value1) * rate

# OHLCV(open, high, low, close, volume)로 당일 시가, 고가, 저가, 종가, 거래량에 대한 데이터
df = pyupbit.get_ohlcv(market, interval=candle_interval, count=test_term)

df['low_rate'] = round((df['open'] - df['low']) / df['open'] * 100, 2)
df['high_rate'] = round((df['high'] - df['open']) / df['open'] * 100, 2)

# 변동폭 * k 계산, (고가 - 저가) * k값
df['range'] = (df['high'] - df['low']) * k

# target(매수가), range 컬럼을 한칸씩 밑으로 내림(.shift(1))
df['target'] = df['close'].shift(1) + df['range'].shift(1)
df['target_p'] = diff_percent(df['target']/df['open'])

df['target_to_high'] = df['high'] - df['target']
df['target_to_high_p'] = diff_percent(df['target_to_high'] / df['target'] + 1)

df['target_to_low'] = df['low'] - df['target']
df['target_to_low_p'] = diff_percent(df['target_to_low'] / df['target'] + 1)

# ror(수익률), np.where(조건문, 참일때 값, 거짓일때 값)
df['ror'] = np.where(df['high'] > df['target'],
                     df['close'] / df['target'] - 0.001,
                     1)
df['ror_origin'] = df['ror']

# 손절 로직 반영
df['ror'] = np.where(df['ror'] > emergency_sell_rate, df['ror'], emergency_sell_rate)

# 익절 로직 반영
df['ror'] = np.where(df['target_to_high_p'] > expected_rate_p, get_middle(df['ror'], (expected_rate_p / 100 + 1), partial_sell_rate), df['ror'])

df['ror_origin_p'] = diff_percent(df['ror_origin'])
df['ror_p'] = diff_percent(df['ror'])

# 누적 곱 계산(cumprod) => 누적 수익률
df['hpr'] = df['ror'].cumprod()

df['hpr_percent'] = diff_percent(df['hpr'])

# df = df.drop(columns=['volume'])
df = df.drop(columns=['value'])
df = df.drop(columns=['ror'])
df = df.drop(columns=['ror_origin'])
df = df.drop(columns=['hpr'])
df = df.drop(columns=['target_to_low'])
df = df.drop(columns=['target_to_high'])
pd.set_option('display.max_rows', 1000)
# pd.set_option('display.max_columns', 80)

# print(df)
print("----------")
print(df)
# print(df.loc[(df['ror_p'] != 0)])
print("----- 익절조건 -----")
print(df.loc[(df.target_to_high_p > expected_rate_p), :])

print("시작가 :",df.iloc[0].name, df.iloc[0]['open'])
print("종료가 :",df.iloc[-1].name, df.iloc[-1]['open'])

increased_rate = diff_percent(df.iloc[-1]['open'] / df.iloc[0]['open'])
print("자연상승률 :",increased_rate)
print("-----")
print(df.tail(1))