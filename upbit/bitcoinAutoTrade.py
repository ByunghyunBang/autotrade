import time
import pyupbit
import datetime
import os

access = os.getenv('UPBIT_ACCESS')
secret = os.getenv('UPBIT_SECRET')

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

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

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def log(msg):
    now = datetime.datetime.now()
    print(now, msg)

# 로그인
upbit = pyupbit.Upbit(access, secret)
log("autotrade start")
k=0.5
exit_rate=0.05 # 매수시점대비 몇% 상승시 매도할 것인가 (절반만 매도)

# 자동매매 시작
is_exit=False
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price("KRW-BTC", k)
            current_price = get_current_price("KRW-BTC")
            exit_price = target_price * (1 + exit_rate)

            # 변동성 돌파 시점에 매수
            if target_price < current_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    log("buy: current_price={}, target_price={}, krw={}".format(current_price, target_price, krw))
                    upbit.buy_market_order("KRW-BTC", krw*0.9995)

            # 이익실현 시점에 50% 매도
            if (not is_exit) and exit_price < current_price:
                exit_btc = get_balance("BTC") * 0.5
                if btc > 0.00008:
                    log("exit: current_price={}, exit_price={}, exit_btc={}".format(current_price, target_price, exit_btc))
                    upbit.sell_market_order("KRW-BTC", exit_btc)
                    is_exit=True
        else:
            btc = get_balance("BTC")
            if btc > 0.00008:
                log("sell: btc={}".format(btc))
                upbit.sell_market_order("KRW-BTC", btc*0.9995)
            is_exit=False
        time.sleep(5)
    except Exception as e:
        log(e)
        time.sleep(5)
