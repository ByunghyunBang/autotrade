import pyupbit
import os

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

access = os.getenv('UPBIT_ACCESS')
secret = os.getenv('UPBIT_SECRET')

upbit = pyupbit.Upbit(access, secret)

print(upbit.get_balance("KRW-BTC"))     # KRW-BTC 조회
print(upbit.get_balance("KRW"))         # 보유 현금 조회

print(get_middle(100,200))
# krw = get_balance("KRW")
# if krw > 5000:
#     print("매수:{}".format(krw))
#     upbit.buy_market_order("KRW-BTC", krw*0.9995)

# btc = get_balance("BTC")
# if btc > 0.00008:
#     print("매도:{}".format(btc))
#     upbit.sell_market_order("KRW-BTC", btc)
