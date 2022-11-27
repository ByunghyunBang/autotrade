import pyupbit
import numpy as np
import pandas as pd

###################################
# 순환 매수매도 알고리즘 구현
###################################

pd.set_option('display.max_rows', 1000)

market = "KRW-ETH"
k = 0.5
candle_interval="minute240"

# test_period = "20221020" # 횡보장
# test_period = "20221030" # 상승장
# test_period = "20220921" # 하락장
# test_period = "20221115" # 하락장
test_period = None

test_days=90
fee_rate=0.002
if candle_interval=="day":
    test_term=test_days
if candle_interval=="minute240":
    test_term=test_days*6
if candle_interval=="minute60":
    test_term=test_days*24
if candle_interval=="minute30":
    test_term=test_days*24*2
if candle_interval=="minute10":
    test_term=test_days*24*6
if candle_interval=="minute5":
    test_term=test_days*24*12
if candle_interval=="minute1":
    test_term=test_days*24*60
# OHLCV(open, high, low, close, volume)로 당일 시가, 고가, 저가, 종가, 거래량에 대한 데이터
df = pyupbit.get_ohlcv(market, interval=candle_interval, count=test_term, to=test_period)

df['low_rate'] = round((df['open'] - df['low']) / df['open'] * 100, 2)
df['high_rate'] = round((df['high'] - df['open']) / df['open'] * 100, 2)
df['direction'] = np.where(df['open'] > df['close'], "down", "up")
df['height'] = df['high']-df['low']

print(df)
print("--------------------------")

time_to_buy = False
time_to_sell = False

def human_readable(num):
    return format(int(num), ',')

def get_compate_rate(num1, num2):
    return round((num2 - num1) / num1 * 100, 2)

def get_status_string(current_price, krw_balance, crypto_balance):
    current_total_balance = krw_balance + crypto_balance * current_price

    return "current_price={};krw={},crypto={},total={},krw-balance-rate={}".format(
                    human_readable(current_price),
                    human_readable(krw_balance),
                    crypto_balance,
                    human_readable(current_total_balance),
                    get_compate_rate(current_total_balance,krw_balance+current_total_balance),
            )

def buy_condition(latest2_row):
    target_price = get_target_price_to_buy(latest2_row)
    current = latest2_row.iloc[1]
    return current['high'] >= target_price

def get_target_price_to_buy(latest2_row):
    prev = latest2_row.iloc[0]
    target_price = prev['close'] + prev['height'] * k
    return target_price

def sell_condition(latest2_row):
    target_price = get_target_price_to_sell(latest2_row)
    current = latest2_row.iloc[1]
    return current['low'] <= target_price

def get_target_price_to_sell(latest2_row):
    prev = latest2_row.iloc[0]
    target_price = prev['close'] - prev['height'] * k
    return target_price

def simulation(df, krw_balance, crypto_balance_in_krw, amount, min_diff):
    open_row = df.iloc[0]
    open_price = open_row['open']
    crypto_balance = crypto_balance_in_krw / open_price
    last_tx_price = open_price
    last_tx_type = None
    open_total_balance = krw_balance + crypto_balance * open_price
    print("{} start:{}"
        .format(
            open_row.name, get_status_string(open_row['open'], krw_balance, crypto_balance)
        )
    )
    for i in range(len(df)):
        if i<1:
            continue
        current_row = df.iloc[i]
        latest2_row = df.iloc[i-1:i+1]
        timestamp = current_row.name
        current_price = current_row['open']
        crypto_balance_in_krw = crypto_balance * current_price
        time_to_buy = krw_balance > crypto_balance_in_krw
        time_to_sell = krw_balance < crypto_balance_in_krw
        # print("{}: log: current_price={},krw_balance={};crypto_balance_in_krw={};time_to_buy={},time_to_sell={}".format(
        #     timestamp,
        #     human_readable(current_price), 
        #     human_readable(krw_balance),
        #     human_readable(crypto_balance_in_krw),
        #     time_to_buy,
        #     time_to_sell
        #     )
        # )
        if (not time_to_buy and not time_to_sell):
            continue

        if time_to_buy and buy_condition(latest2_row):

            target_price = get_target_price_to_buy(latest2_row)
            amount = krw_balance
            krw_balance -= amount
            crypto_balance += (amount / target_price) * (1 - fee_rate)
            total_krw = krw_balance + crypto_balance * current_price
            print("{} buy: {}".format(
                timestamp, get_status_string(target_price, krw_balance, crypto_balance)
                )
            )
            latest_krw_balance = total_krw

        if time_to_sell and sell_condition(latest2_row):

            target_price = get_target_price_to_sell(latest2_row)
            amount = crypto_balance
            krw_balance += amount * current_price * (1 - fee_rate)
            crypto_balance -= amount
            total_krw = krw_balance + crypto_balance * current_price

            result_comment = "earned={}({}%)".format(
                    human_readable(total_krw-latest_krw_balance),
                    get_compate_rate(latest_krw_balance, total_krw)
                )

            print("{} sell: {};{}".format(
                timestamp,
                get_status_string(target_price, krw_balance, crypto_balance),
                result_comment
                )
            )
            latest_krw_balance = total_krw

    close_row = df.iloc[-1]
    timestamp = close_row.name

    print("{} finish: {}".format(
        close_row.name, get_status_string(close_row['close'], krw_balance, crypto_balance)
        )
    )

    print("---------------------------------------------------")
    close_price = close_row['open']
    close_total_balance = krw_balance + crypto_balance * close_price
    print("price_rate={}%;balance_diff={}({}%)"
        .format(
            get_compate_rate(open_price, close_price),
            human_readable(close_total_balance - open_total_balance),
            get_compate_rate(open_total_balance, close_total_balance),
        )
    )

simulation(df, krw_balance = 5000 * 10000, crypto_balance_in_krw = 0 * 10000, amount= 4000 * 10000, min_diff = 5000)
