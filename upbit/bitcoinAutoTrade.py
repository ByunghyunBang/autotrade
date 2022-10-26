import time
import pyupbit
import datetime
import os

trading_enabled=True
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

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    return upbit.get_balance(ticker)

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def log(msg):
    now = datetime.datetime.now()
    print(now, msg)

def clear_flags():
    meet_expected_rate=False
    emergency_sell=False
    is_freezed=False
    freezed_time=time.time()

def set_freeze(now):
    is_freezed=True
    freezed_time=now

# 로그인
upbit = pyupbit.Upbit(access, secret)
log("autotrade start")
ticker="KRW-BTC"
k=0.5
expected_rate=0.03 # 매수시점대비 몇% 상승시 매도할 것인가 (절반만 매도)
panic_sell_rate=0.008 # 하락시 손절시점 설정

# 자동매매 시작
meet_expected_rate=False
emergency_sell=False
is_freezed=False
freezed_time=time.time()

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            ohlcv_day2 = pyupbit.get_ohlcv(ticker, interval="day", count=2)
            target_price = get_target_price(ohlcv_day2, k)
            target_price2 = get_target_price2(ohlcv_day2, k)
            current_price = get_current_price("KRW-BTC")
            expected_rate_price = target_price * (1 + expected_rate)
            emergency_sell_price = target_price2 * (1 - panic_sell_rate)
            log(
                "(no-event) current_price={},target_price={},target_price2={},expected_rate_price={},is_freezed={}"
                .format(current_price,target_price,target_price2,expected_rate_price,is_freezed)
                )

            # Freeze 상태이면 거래하지 않음
            if is_freezed:
                continue

            # 변동성 돌파 시점에 매수
            if current_price > target_price2:
                krw = get_balance("KRW")
                if krw > 5000:
                    log("buy: current_price={}, target_price2={}, krw={}".format(current_price, target_price2, krw))
                    if trading_enabled:
                        upbit.buy_market_order("KRW-BTC", krw*0.9995)

            # 기대이익실현 시점에 50% 매도
            if (not meet_expected_rate) and current_price > expected_rate_price:
                half_btc = get_balance("BTC") * 0.5
                if half_btc > 0.00008:
                    log("exit: current_price={}, expected_rate_price={}, half_btc={}".format(current_price, expected_rate_price, half_btc))
                    if trading_enabled:
                        upbit.sell_market_order("KRW-BTC", half_btc)
                    meet_expected_rate=True

            # 손절 : 지정된 손절시점에서 전량매도
            if (current_price < emergency_sell_price):
                btc = get_balance("BTC")
                if btc > 0.00008:
                    log("emergency sell: trading was freezed: current_price={}, btc={}".format(current_price, btc))
                    if trading_enabled:
                        upbit.sell_market_order("KRW-BTC", btc)
                    set_freeze(now)

        else:
            # 일일 종료 시점에 전량매도
            btc = get_balance("BTC")
            if btc > 0.00008:
                log("sell: current_price={}, btc={}".format(current_price, btc))
                if trading_enabled:
                    upbit.sell_market_order("KRW-BTC", btc)
            
            # 현재 잔액 로그
            krw = get_balance("KRW")
            log("Closing balance={}".format(krw))
            clear_flags()
        time.sleep(5)
    except Exception as e:
        log(e)
        time.sleep(5)
