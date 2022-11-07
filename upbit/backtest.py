import pyupbit
import numpy as np

k = 0.5
cut_rate = 1 - 0.005
expecte_rate_p = 2.0
partial_sell_rate=0.8 # 익절시 매도비율
market = "KRW-ETH"

def diff_percent(n):
    return round((n - 1) * 100, 2)

def get_middle(value1, value2, rate=0.5):
    return value1 + (value2 - value1) * rate

# OHLCV(open, high, low, close, volume)로 당일 시가, 고가, 저가, 종가, 거래량에 대한 데이터
# df = pyupbit.get_ohlcv(market, interval="minute10", count=24*6*7)
# df = pyupbit.get_ohlcv(market, interval="minute60", count=24*7)
df = pyupbit.get_ohlcv(market, interval="minute240", count=6*7)
# df = pyupbit.get_ohlcv(market, interval="day", count=7)

df['low_rate'] = round((df['open'] - df['low']) / df['open'] * 100, 2)
df['high_rate'] = round((df['high'] - df['open']) / df['open'] * 100, 2)

# 변동폭 * k 계산, (고가 - 저가) * k값
df['range'] = (df['high'] - df['low']) * k

# target(매수가), range 컬럼을 한칸씩 밑으로 내림(.shift(1))
df['target'] = df['open'] + df['range'].shift(1)

df['target_to_high'] = df['high'] - df['target']
df['target_to_high_percent'] = diff_percent(df['target_to_high'] / df['target'] + 1)

# ror(수익률), np.where(조건문, 참일때 값, 거짓일때 값)
df['ror'] = np.where(df['high'] > df['target'],
                     df['close'] / df['target'] - 0.001,
                     1)
df['ror_origin'] = df['ror']

# 손절 로직 반영
df['ror'] = np.where(df['ror'] > cut_rate, df['ror'], cut_rate)

# 익절 로직 반영
df['ror'] = np.where(df['target_to_high_percent'] > expecte_rate_p, get_middle(df['ror'], (expecte_rate_p / 100 + 1), partial_sell_rate), df['ror'])

df['ror_origin_p'] = diff_percent(df['ror_origin'])
df['ror_p'] = diff_percent(df['ror'])

# 누적 곱 계산(cumprod) => 누적 수익률
df['hpr'] = df['ror'].cumprod()

df['hpr_percent'] = diff_percent(df['hpr'])


print(df.loc[(df.ror != 1), :])
print("----- 익절조건 -----")
print(df.loc[(df.target_to_high_percent > expecte_rate_p), :])

print("시작가 :",df.iloc[0].name, df.iloc[0]['open'])
print("종료가 :",df.iloc[-1].name, df.iloc[-1]['open'])

increased_rate = diff_percent(df.iloc[-1]['open'] / df.iloc[0]['open'])
print("자연상승률 :",increased_rate)
