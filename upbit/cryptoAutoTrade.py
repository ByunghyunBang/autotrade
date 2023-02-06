import time
import pyupbit
import datetime
import os
import traceback
import lineNotify
import debug_settings
import yaml
import argparse
from enum import Enum


access = os.getenv('UPBIT_ACCESS')
secret = os.getenv('UPBIT_SECRET')


def get_middle(value1, value2, rate=0.5):
    return value1 + (value2 - value1) * rate


def get_target_price_to_buy(ohlcv_candle2_param):
    prev = ohlcv_candle2_param.iloc[0]
    # current = ohlcv_candle2.iloc[1]
    height = prev['high'] - prev['low']
    height_k = max(height * k, min_diff_price_to_buy)
    result = prev['close'] + height_k
    # target_price = current['low'] + height_k
    return result


def get_target_price_to_sell(ohlcv_candle2_param, sell_price_policy_param):
    prev = ohlcv_candle2_param.iloc[0]
    # current = ohlcv_candle2.iloc[1]
    height = prev['high'] - prev['low']
    height_k = height * k
    if sell_price_policy_param == "PREV_CLOSE_BASED":
        result = prev['close'] - height_k
    else:
        result = prev['high'] - height_k
    min_loss_price = latest_buy_price * (1 - min_loss_p / 100)
    return max(result, min_loss_price)


def get_candle_open(ohlcv_candle2_param):
    df = ohlcv_candle2_param
    return df.iloc[1]['open']


def get_start_time(market_param):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(market_param, interval=candle_interval, count=1)
    result = df.index[0]
    return result


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


def get_current_price(market_param):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=market_param)["orderbook_units"][0]["ask_price"]


def get_total_balance_krw_and_crypto_with_locked(market_param, current_price_param):
    total_krw_ = upbit.get_balance_t()
    total_crypto = upbit.get_balance_t(market_param)
    return total_krw_ + total_crypto * current_price_param


def log(msg):
    now_ = datetime.datetime.now()
    print(now_, msg)


def log_and_notify(msg):
    log(msg)
    if debug_settings.trading_enabled:
        now_ = datetime.datetime.now().replace(microsecond=0)
        notify_msg = str(now_) + "\n" + msg.replace(";", "\n").replace(": ", ":\n")
        lineNotify.line_notify(notify_msg)


def diff_percent(n):
    return round((n - 1) * 100, 2)


def clear_flags():
    global trading_status, time_to_partial_sell, emergency_sell, latest_buy_price
    global frozen_time, partial_sell_done
    trading_status = TradingStatus.INITIAL
    latest_buy_price = 0
    time_to_partial_sell = None
    emergency_sell = False
    frozen_time = time.time()
    partial_sell_done = False


def human_readable(num):
    if num is None:
        return ""
    return "{:,.2f}".format(num)


def start_log():
    log_str = "config: market={};k={};volume_k={};candle_interval={}".format(
        market,
        k,
        volume_k,
        candle_interval
    )

    if debug_settings.trading_enabled:
        log(log_str)
    else:
        log(log_str)


def save_status(status_param):
    with open(status_file, "w") as f:
        yaml.dump(status_param, f)


def load_status():
    try:
        with open(status_file, "r") as f:
            status_ = yaml.load(f, Loader=yaml.FullLoader)
    except:
        status_ = {'latest_krw': None}
    return status_


status_file = "trading_status.yml"
config_file = "trading_config.yml"


def get_config_or_default(config_, key, default=None):
    try:
        value = config_[key]
        return value
    except Exception:
        return default


def load_config():
    global symbol, k
    global candle_interval, partial_sell_delay
    global market, time_delta, latest_krw
    global min_diff_price_to_buy
    global volume_k
    global min_volume_to_buy
    global time_deadline_to_buy_p
    global min_loss_p
    global sell_on_end
    global sell_price_policy
    global expected_rate_p

    parser = argparse.ArgumentParser()

    parser.add_argument('--symbol', required=False, help='symbol')
    parser.add_argument('--k', required=False, help='k')
    parser.add_argument('--volume_k', required=False, help='volume_k')
    parser.add_argument('--min_volume_to_buy', required=False, help='min_volume_to_buy')
    args = parser.parse_args()

    with open(config_file, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    if args.symbol is not None:
        symbol = args.symbol
    else:
        symbol = get_config_or_default(config, "symbol")
    if symbol is None:
        print("symbol is unspecified. Terminated.")
        exit(1)

    k = get_config_or_default(config, "k", default=99999)
    volume_k = get_config_or_default(config, "volume_k", 0)
    if args.min_volume_to_buy is not None:
        min_volume_to_buy = int(args.min_volume_to_buy)
    else:
        min_volume_to_buy = int(get_config_or_default(config, "min_volume_to_buy", default=0))

    expected_rate_p = float(get_config_or_default(config, "expected_rate_p", default=1000))
    candle_interval = config['candle_interval']
    min_diff_price_to_buy = config['min_diff_price_to_buy']
    time_deadline_to_buy_p = config['time_deadline_to_buy_p']
    min_loss_p = config['min_loss_p']
    sell_on_end = config['sell_on_end']
    sell_price_policy = config['sell_price_policy']
    if candle_interval == "minute240":
        time_delta = datetime.timedelta(minutes=240)
    elif candle_interval == "minute60":
        time_delta = datetime.timedelta(minutes=60)
    elif candle_interval == "minute30":
        time_delta = datetime.timedelta(minutes=30)
    elif candle_interval == "minute5":
        time_delta = datetime.timedelta(minutes=5)
    elif candle_interval == "minute1":
        time_delta = datetime.timedelta(minutes=1)
    elif candle_interval == "day":
        time_delta = datetime.timedelta(days=1)
    market = "KRW-{}".format(symbol)
    latest_krw = None


# 변수 선언
market = None
sell_price_policy = None
buy_price_tollerance = 0.01 # 매수조건 만족시점에 현재가가 목표가보다 너무 높으면 매수하지 않음

# 각종 설정
load_config()

# 로그인
upbit = pyupbit.Upbit(access, secret)


class TradingStatus(Enum):
    INITIAL = 1
    READY_TO_BUY = 2
    BOUGHT = 3
    MEET_EXPECTED_PRICE = 4
    DONE = 5
    TIME_END = 6


# 자동매매 시작
clear_flags()
status = load_status()
latest_buy_price = 0
max_betting_amount = 1000000

def candle_begin_event():
    load_config()
    global current_price, emergency_sell_price, candle_open, status
    global time_to_buy, time_to_sell, target_price_to_buy, target_price_to_sell
    global trading_status
    global min_volume_to_buy
    global expected_price
    ohlcv_candle2 = pyupbit.get_ohlcv(market, interval=candle_interval, count=2)
    current_price = get_current_price(market)
    candle_open = get_candle_open(ohlcv_candle2)
    krw_balance = get_balance("KRW")
    crypto_balance = get_balance(symbol)
    crypto_balance_in_krw = crypto_balance * current_price
    time_to_buy = krw_balance > crypto_balance_in_krw
    if time_to_buy:
        trading_status = TradingStatus.READY_TO_BUY
    else:
        trading_status = TradingStatus.BOUGHT
        expected_price = None
    time_to_sell = krw_balance < crypto_balance_in_krw
    target_price_to_buy = get_target_price_to_buy(ohlcv_candle2)
    target_price_to_sell = get_target_price_to_sell(ohlcv_candle2, sell_price_policy)
    min_volume_to_buy = get_volume_to_buy(ohlcv_candle2, min_volume_to_buy, volume_k)

    start_log()
    log(
        "candle begin: market={};current_price={};candle_open={};latest_krw={};{}"
        .format(
            market,
            human_readable(current_price),
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


def sell_procedure(mark="sell", symbol_param="", current_price_param=0, sell_rate=1, earned_message="N/A"):
    crypto = get_balance(symbol_param) * sell_rate
    total_krw = get_total_balance_krw_and_crypto_with_locked(market, current_price_param)
    log_and_notify(
        "{}: 🐼🐼🐼🐼🐼🐼🐼🐼;market={};current_price={};crypto={};crypto_balance={};total_krw={};earned={}"
        .format(
            mark,
            market,
            human_readable(current_price_param),
            crypto,
            human_readable(current_price_param * crypto),
            human_readable(total_krw),
            earned_message
        )
    )
    if crypto > 0.00008:
        if debug_settings.trading_enabled:
            upbit.sell_market_order(market, crypto)


def get_volume_to_buy(ohlcv_candle2, min_volume_to_buy, volume_k):
    if volume_k > 0:
        return max(min_volume_to_buy, ohlcv_candle2.iloc[0]['volume'] * volume_k)
    return min_volume_to_buy


def earned_log_message(current_price, latest_buy_price):
    if latest_buy_price is None or latest_buy_price == 0:
        return
    earned = current_price - latest_buy_price
    earned_rate = (current_price / latest_buy_price) * 100 - 100
    if earned > 0:
        diff_mark = "️;❤️❤️❤️❤️❤️❤️❤️❤️"
    elif earned < 0:
        diff_mark = "️;💀💀💀💀💀💀💀💀💀"
    else:
        diff_mark = ""
    return "diff={};earned_rate={}%{}".format(
            human_readable(earned),
            human_readable(earned_rate),
            diff_mark
        )


def main():
    global latest_buy_price, time_to_buy, time_to_sell
    global trading_status, expected_price
    global max_betting_amount
    while True:
        try:
            now = datetime.datetime.now()
            start_time = get_start_time(market)
            end_time = start_time + time_delta - datetime.timedelta(seconds=60)
            time_deadline_to_buy = start_time + time_delta * time_deadline_to_buy_p

            # 거래 가능 시간: 봉시작 ~ 봉종료 20초전
            if start_time < now < end_time:

                ohlcv_candle2 = pyupbit.get_ohlcv(market, interval=candle_interval, count=2)
                current_price = get_current_price(market)
                volume = ohlcv_candle2.iloc[1]['volume']

                if trading_status == TradingStatus.INITIAL or trading_status == TradingStatus.TIME_END:
                    clear_flags()
                    candle_begin_event()

                log(
                    "(no-event) diff from current: market={};current_price={};volume={};min_volume_to_buy={};latest_buy_price={};{}"
                    .format(
                        market,
                        human_readable(current_price),
                        human_readable(ohlcv_candle2.iloc[1]['volume']),
                        human_readable(min_volume_to_buy),
                        human_readable(latest_buy_price),
                        get_target_price_str()
                    )
                )

                # 매수여부 판단
                if trading_status == TradingStatus.READY_TO_BUY and volume >= min_volume_to_buy and (not sell_on_end or now < time_deadline_to_buy):
                    target_price = get_target_price_to_buy(ohlcv_candle2)
                    if current_price >= target_price * (1 + buy_price_tollerance):
                        trading_status = TradingStatus.DONE
                        buy_mark = "cannot buy (target_price is too high):"
                        log_and_notify(
                            "{};market={};current_price={};target_price={};expected_price={};krw={}"
                            .format(
                                buy_mark,
                                market,
                                human_readable(current_price),
                                human_readable(target_price),
                                human_readable(expected_price),
                                human_readable(krw)
                            )
                        )
                        time_to_buy = False

                    elif current_price >= target_price:
                        krw = get_balance("KRW")
                        latest_buy_price = current_price
                        expected_price = latest_buy_price * (1 + expected_rate_p / 100)
                        trading_status = TradingStatus.BOUGHT
                        if krw > 5000:
                            buy_mark = "buy: 🦁🦁🦁🦁🦁🦁🦁🦁"
                            if debug_settings.trading_enabled:
                                buy_amount = min(krw, max_betting_amount)
                                upbit.buy_market_order(market, buy_amount * 0.9995)
                        else:
                            buy_mark = "cannot buy (no money):"

                        log_and_notify(
                            "{};market={};current_price={};target_price={};expected_price={};krw={}"
                            .format(
                                buy_mark,
                                market,
                                human_readable(current_price),
                                human_readable(target_price),
                                human_readable(expected_price),
                                human_readable(krw)
                            )
                        )
                        time_to_buy = False

                if trading_status == TradingStatus.BOUGHT:
                    if expected_price is not None and current_price >= expected_price:
                        trading_status = TradingStatus.MEET_EXPECTED_PRICE
                        top_price = current_price
                        log(
                            "meet_expected_price: market={};current_price={},expected_price={}"
                            .format(
                                market,
                                human_readable(current_price),
                                human_readable(expected_price)
                            )
                        )

                if trading_status == TradingStatus.MEET_EXPECTED_PRICE:
                    if current_price > top_price: # 기대값에 도달했어도 가격이 오르는 중에는 팔지 않음
                        log(
                            "top_price updated: market={};top_price_old={};new_top_price={}"
                            .format(
                                market,
                                human_readable(top_price),
                                human_readable(current_price)
                            )
                        )
                        top_price = current_price
                    elif current_price < top_price * (1 - 0.005): # 최고점 대비 0.5% 하락시점에 매도
                        trading_status = TradingStatus.DONE
                        earned_message = earned_log_message(current_price, latest_buy_price)
                        sell_procedure(mark="sell_on_expected", symbol_param=symbol, current_price_param=current_price, earned_message=earned_message)
                        time_to_sell = False


                # 매도여부 판단
                if time_to_sell:
                    target_price = get_target_price_to_sell(ohlcv_candle2, sell_price_policy)
                    if current_price <= target_price:
                        trading_status = TradingStatus.DONE
                        sell_procedure(mark="sell_on_fall", symbol_param=symbol, current_price_param=current_price)
                        time_to_sell = False

            # 종료 시점
            else:
                if trading_status != TradingStatus.TIME_END:
                    # 종료시 매도조건이면
                    if sell_on_end and (trading_status == TradingStatus.BOUGHT or trading_status == TradingStatus.MEET_EXPECTED_PRICE):
                        trading_status = TradingStatus.DONE
                        earned_message = earned_log_message(current_price, latest_buy_price)
                        sell_procedure(mark="sell_on_end", symbol_param=symbol, current_price_param=current_price, earned_message=earned_message)
                        time_to_sell = False
                        time.sleep(5)

                    # 현재 잔액 로그
                    total_krw = get_total_balance_krw_and_crypto_with_locked(market, current_price)
                    latest_krw = status['latest_krw']
                    if latest_krw is None:
                        latest_krw = total_krw
                    total_krw_diff = total_krw - latest_krw
                    if total_krw > latest_krw:
                        diff_mark = "❤️❤️❤️❤️❤️❤️❤️❤️"
                    elif total_krw == latest_krw:
                        diff_mark = ""
                    else:
                        diff_mark = "💀💀💀💀💀💀💀💀💀"

                    log(
                        "candle end: market={};balance={};earned={}({}%);{};******************************"
                        .format(
                            market,
                            human_readable(total_krw),
                            human_readable(total_krw_diff),
                            round(total_krw_diff / latest_krw * 100, 2),
                            diff_mark
                        )
                    )
                    latest_krw = total_krw
                    trading_status = TradingStatus.TIME_END
                    status['latest_krw'] = latest_krw
                    save_status(status)

            time.sleep(1)
        except Exception as e:
            log(e)
            traceback.print_exc()
            time.sleep(5)

main()