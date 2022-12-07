import time
import pyupbit
import datetime
import os
import traceback
import lineNotify
import debug_settings
import yaml

access = os.getenv('UPBIT_ACCESS')
secret = os.getenv('UPBIT_SECRET')

def get_middle(value1, value2, rate=0.5):
    return value1 + (value2 - value1) * rate

def get_target_price_to_buy(ohlcv_candle2):
    prev = ohlcv_candle2.iloc[0]
    current = ohlcv_candle2.iloc[1]
    height = prev['high'] - prev['low']
    height_k = max(height * k, min_diff_price_to_buy)
    # target_price = prev['close'] + height_k
    target_price = current['low'] + height_k
    return target_price

def get_target_price_to_sell(ohlcv_candle2):
    prev = ohlcv_candle2.iloc[0]
    current = ohlcv_candle2.iloc[1]
    height = prev['high'] - prev['low']
    height_k = height * k
    # target_price = prev['close'] - height_k
    target_price = current['high'] - height_k
    if target_price < latest_buy_price:
        return latest_buy_price
    return target_price

def get_candle_open(ohlcv_candle2):
    df = ohlcv_candle2
    return df.iloc[1]['open']

def get_start_time(market):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(market, interval=candle_interval, count=1)
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

def get_total_balance_krw_and_crypto_with_locked(market, current_price):
    total_krw = upbit.get_balance_t()
    total_crypto = upbit.get_balance_t(market)
    return total_krw + total_crypto * current_price

def log(msg):
    now = datetime.datetime.now()
    print(now, msg)

def log_and_notify(msg):
    log(msg)
    if debug_settings.trading_enabled:
        now = datetime.datetime.now().replace(microsecond=0)
        notify_msg = str(now) + "\n" + msg.replace(";","\n").replace(": ",":\n")
        lineNotify.line_notify(notify_msg)

def diff_percent(n):
    return round((n - 1) * 100, 2)

def clear_flags():
    global already_buyed, meet_expected_price, time_to_partial_sell, emergency_sell, is_frozen, frozen_time, is_closed, partial_sell_done
    already_buyed=False
    meet_expected_price=False
    time_to_partial_sell=None
    emergency_sell=False
    is_frozen=False
    frozen_time=time.time()
    is_closed=False
    partial_sell_done=False

def set_freeze(now):
    global is_frozen, frozen_time
    is_frozen=True
    frozen_time=now

def human_readable(num):
    return "{:,.2f}".format(num)

def start_log():
    log_str="config: market={};k={};candle_interval={}".format(
                market,
                k,
                candle_interval
                )

    if debug_settings.trading_enabled:
        log_and_notify(log_str)
    else:
        log(log_str)

status_file = "trading_status.yml"
def save_status(status):
    with open(status_file, "w") as f:
        yaml.dump(status, f)

def load_status():
    try:
        with open(status_file, "r") as f:
            status = yaml.load(f, Loader=yaml.FullLoader)
    except:
        status = { 'latest_krw': None}
    return status

config_file = "trading_config.yml"
def load_config():
    global symbol,k
    global candle_interval,partial_sell_delay
    global market,time_delta,latest_krw
    global min_diff_price_to_buy
    global min_volumn_to_buy

    with open(config_file, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    symbol = config['symbol']
    k = config['k']
    candle_interval = config['candle_interval']
    min_diff_price_to_buy = config['min_diff_price_to_buy']
    min_volumn_to_buy = config['min_volumn_to_buy']
    if candle_interval=="minute240":
        time_delta=datetime.timedelta(minutes=240)
    elif candle_interval=="minute60":
        time_delta=datetime.timedelta(minutes=60)
    elif candle_interval=="minute5":
        time_delta=datetime.timedelta(minutes=5)
    elif candle_interval=="minute1":
        time_delta=datetime.timedelta(minutes=1)
    elif candle_interval=="day":
        time_delta=datetime.timedelta(days=1)
    market="KRW-{}".format(symbol)
    latest_krw = None

# 각종 설정
load_config()

# 로그인
upbit = pyupbit.Upbit(access, secret)

# 자동매매 시작
clear_flags()
status = load_status()
is_closed = True
latest_buy_price = 0

def candle_begin_event():
    load_config()
    global current_price,target_price,expected_price,emergency_sell_price,candle_open,status
    global time_to_buy,time_to_sell,target_price_to_buy,target_price_to_sell
    ohlcv_candle2 = pyupbit.get_ohlcv(market, interval=candle_interval, count=2)
    current_price = get_current_price(market)
    candle_open = get_candle_open(ohlcv_candle2)
    krw_balance = get_balance("KRW")
    crypto_balance = get_balance(symbol)
    crypto_balance_in_krw = crypto_balance * current_price
    time_to_buy = krw_balance > crypto_balance_in_krw
    time_to_sell = krw_balance < crypto_balance_in_krw
    target_price_to_buy = get_target_price_to_buy(ohlcv_candle2)
    target_price_to_sell = get_target_price_to_sell(ohlcv_candle2)

    start_log()
    log_and_notify(
        "candle begin: market={};current_price={};min_volumn_to_buy={};candle_open={};latest_krw={};{}"
        .format(
            market,
            human_readable(current_price),
            human_readable(min_volumn_to_buy),
            human_readable(candle_open),
            human_readable(status['latest_krw']),
            get_target_price_str()
            )
        )

def get_target_price_str():
    if time_to_buy:
        return "target_price_to_buy={}".format(human_readable(target_price_to_buy))
    elif time_to_sell:
        return "target_price_to_sell={}".format(human_readable(target_price_to_sell))
    else:
        return "target_price=N/A"

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time(market)
        end_time = start_time + time_delta - datetime.timedelta(seconds=10)

        # 거래 가능 시간: 봉시작 ~ 봉종료 20초전
        if start_time < now < end_time:

            ohlcv_candle2 = pyupbit.get_ohlcv(market, interval=candle_interval, count=2)
            current_price = get_current_price(market)
            volume = ohlcv_candle2.iloc[1]['volume']

            if is_closed:
                clear_flags()
                candle_begin_event()
                is_closed=False

            log(
                "(no-event) diff from current: current_price={};volumn={};latest_buy_price={};{}"
                .format(
                    human_readable(current_price),
                    human_readable(ohlcv_candle2.iloc[1]['volume']),
                    human_readable(latest_buy_price),
                    get_target_price_str()
                )
            )

            # Freeze 상태이면 거래하지 않음
            if is_frozen:
                continue

            # 매수여부 판단
            if time_to_buy and volume >= min_volumn_to_buy:
                target_price = get_target_price_to_buy(ohlcv_candle2)
                if current_price >= target_price :
                    krw = get_balance("KRW")
                    if krw > 5000:
                        log_and_notify(
                            "buy: 🦁🦁🦁🦁🦁🦁🦁🦁;current_price={};target_price={};krw={}"
                            .format(
                                human_readable(current_price),
                                human_readable(target_price),
                                human_readable(krw)
                            )
                        )
                        if debug_settings.trading_enabled:
                            upbit.buy_market_order(market, krw*0.9995)
                        latest_buy_price = current_price
                        time_to_buy = False

            # 매도여부 판단
            if time_to_sell:
                target_price = get_target_price_to_sell(ohlcv_candle2)
                if current_price <= target_price :
                    crypto = get_balance(symbol)
                    total_krw = get_total_balance_krw_and_crypto_with_locked(market, current_price)
                    if crypto > 0.00008:
                        log_and_notify(
                            "sell: 🐥🐥🐥🐥🐥🐥🐥🐥;current_price={};crypto={};crypto_balance={};total_krw={}"
                            .format(
                                human_readable(current_price),
                                crypto,
                                human_readable(current_price*crypto),
                                human_readable(total_krw)
                            )
                        )
                        if debug_settings.trading_enabled:
                            upbit.sell_market_order(market, crypto)

                        time_to_sell=False

        # 종료 시점
        else:
            if not is_closed:
                # 현재 잔액 로그
                total_krw = get_total_balance_krw_and_crypto_with_locked(market,current_price)
                latest_krw = status['latest_krw']
                if (latest_krw is None):
                    latest_krw = total_krw
                total_krw_diff = total_krw - latest_krw
                if (total_krw > latest_krw):
                    diff_mark = "❤️❤️❤️❤️❤️❤️❤️❤️"
                elif (total_krw == latest_krw):
                    diff_mark = ""
                else:
                    diff_mark = "💀💀💀💀💀💀💀💀💀"
                
                log_and_notify(
                    "candle end: balance={};earned={}({}%);{};******************************"
                    .format(
                        human_readable(total_krw),
                        human_readable(total_krw_diff),
                        round(total_krw_diff/latest_krw*100,2),
                        diff_mark
                    )
                )
                latest_krw = total_krw
                is_closed= True
                status['latest_krw']=latest_krw
                save_status(status)

        time.sleep(1)
    except Exception as e:
        log(e)
        traceback.print_exc()
        time.sleep(5)
