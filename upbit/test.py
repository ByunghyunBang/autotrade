import pyupbit
import os
import yaml

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_middle(value1, value2, rate=0.5):
    return value1 + (value2 - value1) * rate

def get_target_price2(ohlcv_day2, k):
    """변동성 돌파 전략으로 매수 목표가 조회 (어제 종가 + 오늘 최저가 가중치 반영으로 매수 목표 설정)"""
    df = ohlcv_day2
    base = get_middle(df.iloc[0]['close'],df.iloc[1]['low'],0.6)
    target_price = base + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def save_status(status):
    with open(status_file, "w") as f:
        yaml.dump(status, f)

def load_status():
    with open(status_file, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)

status_file = "trading-status.yml"

access = os.getenv('UPBIT_ACCESS')
secret = os.getenv('UPBIT_SECRET')

upbit = pyupbit.Upbit(access, secret)

print(upbit.get_balance("KRW-ETH"))     # KRW-BTC 조회
print(upbit.get_balance("KRW"))         # 보유 현금 조회

market="KRW-BTC"
df = pyupbit.get_ohlcv(market, interval="day", count=2)
diff = df.iloc[0]['high'] - df.iloc[0]['low']
base = get_middle(df.iloc[0]['close'],df.iloc[1]['low'],0.6)
close = df.iloc[0]['close']
today_low = df.iloc[1]['low']
target = base + diff * 0.5
print(df)
print("diff={},close={},today_low={},base={}".format(diff, close, today_low, base))
print("target={}".format(target))
print(get_middle(df.iloc[0]['high'],df.iloc[0]['low']))

# krw = get_balance("KRW")
# if krw > 5000:
#     print("매수:{}".format(krw))
#     upbit.buy_market_order("KRW-BTC", krw*0.9995)

# btc = get_balance("BTC")
# if btc > 0.00008:
#     print("매도:{}".format(btc))
#     upbit.sell_market_order("KRW-BTC", btc)

status = load_status()
print(status)

status["krw_balance"] = 5555
save_status(status)

