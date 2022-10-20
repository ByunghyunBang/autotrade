import time
import pykorbit
import datetime

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pykorbit.get_ohlc(ticker, period=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pykorbit.get_ohlc(ticker, period=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = korbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pykorbit.get_orderbook(ticker)["orderbook_units"][0]["ask_price"]

# 로그인
key = os.getenv('API_KEY')
secret = os.getenv('API_SECRET')
korbit = pykorbit.Korbit(key=key, secret=secret)
print("autotrade start")

symbol = "BTC"
k = 0.5
# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time(symbol)
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=30):
            target_price = get_target_price(symbol, k)
            current_price = get_current_price(symbol)
            if target_price < current_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    #korbit.buy_market_order(symbol, krw*0.998)
                    print("매수")
        else:
            btc = get_balance("BTC")
            if btc > 0.00008:
                #korbit.sell_market_order(symbol, btc*0.998)
                print("매도")
        time.sleep(5)
    except Exception as e:
        print(e)
        time.sleep(5)
