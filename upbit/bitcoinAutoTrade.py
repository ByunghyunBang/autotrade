import time
import pyupbit
import datetime
import os
import traceback

access = os.getenv('UPBIT_ACCESS')
secret = os.getenv('UPBIT_SECRET')

def get_middle(value1, value2, rate=0.5):
    return value1 + (value2 - value1) * rate

def get_target_price(ohlcv_day2, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = ohlcv_day2
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_target_price2(ohlcv_day2, k):
    """변동성 돌파 전략으로 매수 목표가 조회 (어제 종가 + 오늘 최저가 가중치 반영으로 매수 목표 설정)"""
    df = ohlcv_day2
    base = get_middle(df.iloc[0]['close'],df.iloc[1]['low'],0.6)
    target_price = base + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_today_open(ohlcv_day2):
    df = ohlcv_day2
    return df.iloc[1]['open']

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
    global already_buyed, meet_expected_price, emergency_sell, is_frozen, frozen_time
    already_buyed=False
    meet_expected_price=False
    emergency_sell=False
    is_frozen=False
    frozen_time=time.time()

def set_freeze(now):
    global is_frozen, frozen_time
    is_frozen=True
    frozen_time=now

# 각종 설정
trading_enabled=True
symbol="BTC"
market="KRW-{}".format(symbol)
k=0.3
expected_rate=0.03 # 매수시점대비 몇% 상승시 매도할 것인가 (절반만 매도)
emergency_sell_rate=0.01 # 하락시 손절시점 설정

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

        if start_time < now < end_time - datetime.timedelta(seconds=20):
            ohlcv_day2 = pyupbit.get_ohlcv(market, interval="day", count=2)
            today_open = get_today_open(ohlcv_day2)
            # target_price = get_target_price(ohlcv_day2, k)
            target_price = get_target_price2(ohlcv_day2, k)
            current_price = get_current_price(market)
            expected_price = target_price * (1 + expected_rate)
            emergency_sell_price = target_price * (1 - emergency_sell_rate)
            log(
                "(no-event) market={},current_price={},target_price={},expected_price={},emergency_sell_price={},today_open={},is_frozen={}"
                .format(market,current_price, target_price, expected_price, emergency_sell_price, today_open, is_frozen)
                )

            # Freeze 상태이면 거래하지 않음
            if is_frozen:
                continue

            # 변동성 돌파 시점에 매수
            if (not already_buyed) and (current_price > target_price):
                krw = get_balance("KRW")
                if krw > 5000:
                    log("buy: current_price={}, target_price={}, krw={}".format(current_price, target_price, krw))
                    if trading_enabled:
                        upbit.buy_market_order(market, krw*0.9995)
                    already_buyed = True

            # 기대이익실현 시점에 50% 매도
            if (not meet_expected_price) and (current_price > expected_price):
                half_crypto = get_balance(symbol) * 0.5
                if half_crypto > 0.00008:
                    log("exit: current_price={}, expected_price={}, half_crypto={}".format(current_price, expected_price, half_crypto))
                    if trading_enabled:
                        upbit.sell_market_order(market, half_crypto)
                    meet_expected_price=True

            # 손절 : 지정된 손절시점에서 전량매도
            if (current_price < emergency_sell_price and current_price < today_open):
                crypto = get_balance(symbol)
                if crypto > 0.00008:
                    log("emergency sell: current_price={}, crypto={}".format(current_price, crypto))
                    if trading_enabled:
                        upbit.sell_market_order(market, crypto)
                    # set_freeze(now)

        else:
            # 일일 종료 시점에 전량매도
            crypto = get_balance(symbol)
            if crypto > 0.00008:
                log("closing sell: current_price={}, crypto={}, current_balance={}".format(current_price, crypto, current_price*crypto))
                if trading_enabled:
                    upbit.sell_market_order(market, crypto)
                    time.sleep(5)

            # 현재 잔액 로그
            krw = get_balance("KRW")
            log("Closing balance={}".format(krw))
            clear_flags()

        time.sleep(10)
    except Exception as e:
        log(e)
        traceback.print_exec()
        time.sleep(10)
