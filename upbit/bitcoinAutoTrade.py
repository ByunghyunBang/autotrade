import time
import pyupbit
import datetime
import os

access = os.getenv('UPBIT_ACCESS')
secret = os.getenv('UPBIT_SECRET')

def get_target_price(ohlcv_day2, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = ohlcv_day2
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_target_price2(ohlcv_day2, k):
    """변동성 돌파 전략으로 매수 목표가 조회 (어제 종가 아닌 오늘 최저가 기준으로 매수 목표 설정)"""
    df = ohlcv_day2
    today_low = df.iloc[1]['low']
    target_price = today_low + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(market):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(market, interval="day", count=1)
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

def get_current_price(market):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=market)["orderbook_units"][0]["ask_price"]

def log(msg):
    now = datetime.datetime.now()
    print(now, msg)

def clear_flags():
    global meet_expected_rate, emergency_sell, is_frozen, frozen_time
    meet_expected_rate=False
    emergency_sell=False
    is_frozen=False
    frozen_time=time.time()

def set_freeze(now):
    global is_frozen, frozen_time
    is_frozen=True
    frozen_time=now

# 각종 설정
trading_enabled=False
symbol="BTC"
market="KRW-BTC"
k=0.5
expected_rate=0.03 # 매수시점대비 몇% 상승시 매도할 것인가 (절반만 매도)
panic_sell_rate=0.008 # 하락시 손절시점 설정

# 로그인
upbit = pyupbit.Upbit(access, secret)
log("autotrade start")

# 자동매매 시작
clear_flags()

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time(market)
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            ohlcv_day2 = pyupbit.get_ohlcv(market, interval="day", count=2)
            target_price = get_target_price(ohlcv_day2, k)
            target_price2 = get_target_price2(ohlcv_day2, k)
            current_price = get_current_price(market)
            expected_rate_price = target_price * (1 + expected_rate)
            emergency_sell_price = target_price2 * (1 - panic_sell_rate)
            log(
                "(no-event) current_price={},target_price={},target_price2={},expected_rate_price={},is_frozen={}"
                .format(current_price,target_price,target_price2,expected_rate_price,is_frozen)
                )

            # Freeze 상태이면 거래하지 않음
            if is_frozen:
                continue

            # 변동성 돌파 시점에 매수
            if current_price > target_price2:
                krw = get_balance("KRW")
                if krw > 5000:
                    log("buy: current_price={}, target_price2={}, krw={}".format(current_price, target_price2, krw))
                    if trading_enabled:
                        upbit.buy_market_order(market, krw*0.9995)

            # 기대이익실현 시점에 50% 매도
            if (not meet_expected_rate) and current_price > expected_rate_price:
                half_crypto = get_balance(symbol) * 0.5
                if half_crypto > 0.00008:
                    log("exit: current_price={}, expected_rate_price={}, half_crypto={}".format(current_price, expected_rate_price, half_crypto))
                    if trading_enabled:
                        upbit.sell_market_order(market, half_crypto)
                    meet_expected_rate=True

            # 손절 : 지정된 손절시점에서 전량매도
            if (current_price < emergency_sell_price):
                btc = get_balance(symbol)
                if btc > 0.00008:
                    log("emergency sell: trading was frozen: current_price={}, btc={}".format(current_price, btc))
                    if trading_enabled:
                        upbit.sell_market_order(market, btc)
                    set_freeze(now)

        else:
            # 일일 종료 시점에 전량매도
            btc = get_balance(symbol)
            if btc > 0.00008:
                log("sell: current_price={}, btc={}".format(current_price, btc))
                if trading_enabled:
                    upbit.sell_market_order(market, btc)
            
            # 현재 잔액 로그
            krw = get_balance("KRW")
            log("Closing balance={}".format(krw))
            clear_flags()
        time.sleep(5)
    except Exception as e:
        log(e)
        time.sleep(5)
