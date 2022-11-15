import pyupbit
import numpy as np
import pandas as pd
import datetime
import yaml

config_file = "trading_config.yml"
def load_config():
    global symbol,k,expected_rate_p,max_buy_limit_p,ignore_k_buy_p
    global partial_sell_rate,emergency_sell_rate_p
    global candle_interval,partial_sell_delay
    global market,expected_rate,emergency_sell_rate,time_delta,latest_krw

    with open(config_file, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    symbol = config['symbol']
    k = config['k']
    max_buy_limit_p = config['max_buy_limit_p']
    # ignore_k_buy_p = config['ignore_k_buy_p']
    expected_rate_p = config['expected_rate_p']
    partial_sell_rate = config['partial_sell_rate_p'] / 100
    emergency_sell_rate_p = config['emergency_sell_rate_p']
    candle_interval = config['candle_interval']
    partial_sell_delay = datetime.timedelta(seconds=config['partial_sell_delay_sec'])
    if candle_interval=="minute240":
        time_delta=datetime.timedelta(minutes=240)
    elif candle_interval=="minute60":
        time_delta=datetime.timedelta(minutes=60)
    elif candle_interval=="minute1":
        time_delta=datetime.timedelta(minutes=1)
    elif candle_interval=="day":
        time_delta=datetime.timedelta(days=1)
    market="KRW-{}".format(symbol)
    expected_rate=expected_rate_p / 100 + 1 # 익절 조건 : 매수시점대비 몇% 상승시 매도할 것인가 (일부 매도)
    emergency_sell_rate=1-emergency_sell_rate_p / 100
    latest_krw = None

# 각종 설정
load_config()

test_days=70
if candle_interval=="day":
    test_term=test_days
if candle_interval=="minute240":
    test_term=test_days*6
if candle_interval=="minute60":
    test_term=test_days*24
if candle_interval=="minute30":
    test_term=test_days*24*2
if candle_interval=="minute10":
    test_term=test_days*24*6
if candle_interval=="minute5":
    test_term=test_days*24*12
if candle_interval=="minute1":
    test_term=test_days*24*60

def diff_percent(n):
    return round((n - 1) * 100, 2)

def get_middle(value1, value2, rate=0.5):
    return value1 + (value2 - value1) * rate

# OHLCV(open, high, low, close, volume)로 당일 시가, 고가, 저가, 종가, 거래량에 대한 데이터
df = pyupbit.get_ohlcv(market, interval=candle_interval, count=test_term)
df['volume_diff_p'] = round(df['volume']/ df['volume'].shift(1) * 100 - 100,2)

df['low_rate'] = round((df['open'] - df['low']) / df['open'] * 100, 2)
df['high_rate'] = round((df['high'] - df['open']) / df['open'] * 100, 2)

# 변동폭 계산, (고가 - 저가) * k값
df['range'] = (df['high'] - df['low'])
df['range_k'] = (df['high'] - df['low'])*k
# df['range_k'] = np.where(df['open'] > df['close'], (df['high'] - df['low'])*k, (df['close'] - df['open'])*k)

# target(매수가), range 컬럼을 한칸씩 밑으로 내림(.shift(1))
df['target_original'] = df['close'].shift(1) + df['range_k'].shift(1)

# get_target_price
df['target'] = df['close'].shift(1) + df['range_k'].shift(1)

# get_target_price3
# df['target'] = np.where(df['close'].shift(1) + df['range_k'].shift(1) < df['close'].shift(1)*(100+max_buy_limit_p)/100,
#                         df['close'].shift(1) + df['range_k'].shift(1),
#                         df['close'].shift(1) * (100+max_buy_limit_p)/100
#                         )

# get_target_price4 : ignore_k_buy
# df['target'] = df['close'].shift(1) * (1 + ignore_k_buy_p / 100)

df['target_original_p'] = diff_percent(df['target_original']/df['open'])
df['target_p'] = diff_percent(df['target']/df['open'])

df['target_to_high'] = df['high'] - df['target']
df['target_to_high_p'] = diff_percent(df['target_to_high'] / df['target'] + 1)

df['target_to_low'] = df['low'] - df['target']
df['target_to_low_p'] = diff_percent(df['target_to_low'] / df['target'] + 1)

# ror(수익률), np.where(조건문, 참일때 값, 거짓일때 값)
df['ror'] = np.where(df['high'] > df['target'],
                     df['close'] / df['target'] - 0.005,
                     1)
df['ror_origin'] = df['ror']

# 손절 로직 반영
df['ror'] = np.where(df['ror'] > emergency_sell_rate, df['ror'], emergency_sell_rate)

# 익절 로직 반영
df['ror'] = np.where(df['target_to_high_p'] > expected_rate_p, get_middle(df['ror'], expected_rate, partial_sell_rate), df['ror'])

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
print("-----전체-----")
print(df)
print("----거래 일어난경우만------")
print(df.loc[(df['ror_p'] != 0)])
print("----- 익절조건 -----")
print(df.loc[(df.target_to_high_p > expected_rate_p), :])

print("시작가 :",df.iloc[0].name, df.iloc[0]['open'])
print("종료가 :",df.iloc[-1].name, df.iloc[-1]['open'])

increased_rate = diff_percent(df.iloc[-1]['open'] / df.iloc[0]['open'])
print("자연상승률 :",increased_rate)
print("-----")
print(df.tail(1))