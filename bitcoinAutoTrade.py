import time
import pykorbit
import datetime
import os

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pykorbit.get_ohlc(ticker, period=2)
    target_price = df.iloc[1]['close'] + (df.iloc[1]['high'] - df.iloc[1]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pykorbit.get_ohlc(ticker, period=2)
    start_time = df.index[1]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = korbit.get_balances()
    balance = balances[ticker]
    if balance is not None:
        return float(balance['available'])
    else:
        return 0

def get_current_price(ticker):
    """현재가 조회"""
    current_price = pykorbit.get_orderbook(ticker)["asks"][0][0]
    if current_price is not None:
        return float(current_price)
    else:
        return 0

def log(msg):
    now = datetime.datetime.now()
    print(now, msg)
# 로그인
key = os.getenv('API_KEY')
secret = os.getenv('API_SECRET')
korbit = pykorbit.Korbit(key=key, secret=secret)

symbol = "btc"
k = 0.5

# 자동매매 시작
log("autotrade start")
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time(symbol)
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=30):
            target_price = get_target_price(symbol, k)
            current_price = get_current_price(symbol)
            if target_price < current_price:
                krw = get_balance("krw")
                if krw > 5000:
                    #korbit.buy_market_order(symbol, krw*0.998)
                    log("매수")
        else:
            btc = get_balance(symbol)
            if btc > 0.00008:
                #korbit.sell_market_order(symbol, btc*0.998)
                log("매도")
        time.sleep(5)
    except Exception as e:
        log(e)
        time.sleep(5)
