import pyupbit
import numpy as np
import pandas as pd
import math

###################################
# 순환 매수매도 알고리즘 구현
###################################

pd.set_option('display.max_rows', 1000)

ticker = "ETH"
unit_price = 1000 # ETH
# unit_price = 1 # DOGE
market = "KRW-" + ticker
k = 0.7
candle_interval="minute60"
# test_period = "20221020" # 횡보장
# test_period = "20221030" # 상승장
# test_period = "20220921" # 하락장
# test_period = "20221115" # 하락장
test_period = None

test_days=7
fee_rate=0.0005

min_loss_p = 0.3

# min_diff_price_to_buy=1 # DOGE
# min_volumn_to_buy= 80 * 1000 * 1000 # DOGE
min_diff_price_to_buy=5000 # ETH
min_volumn_to_buy= 1500 # ETH
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
latest_buy_price = 0

def human_readable(num):
    return format(int(num), ',')

def get_middle(value1, value2, rate=0.5):
    return value1 + (value2 - value1) * rate

def get_compate_rate(num1, num2):
    return round((num2 - num1) / num1 * 100, 2)

def get_status_string(current_price, volume, krw_balance, crypto_balance):
    current_total_balance = krw_balance + crypto_balance * current_price

    return "current_price={};volume={};krw={};crypto={};total={};krw-balance-rate={}".format(
                    human_readable(current_price),
                    human_readable(volume),
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
    current = latest2_row.iloc[1]
    height_k = max(prev['height'] * k,min_diff_price_to_buy)
    target_price = current['low'] + height_k
    return target_price

def sell_condition(latest2_row):
    target_price = get_target_price_to_sell(latest2_row)
    current = latest2_row.iloc[1]
    return current['low'] <= target_price

def get_target_price_to_sell(latest2_row):
    prev = latest2_row.iloc[0]
    current = latest2_row.iloc[1]
    # height_k = max(prev['height'] * k,2)
    height_k = prev['height'] * k
    min_loss_price = latest_buy_price * (1-min_loss_p/100)
    target_price = max(prev['high'] - height_k, min_loss_price)
    # target_price = max(get_middle(prev['close'],current['high']) - height_k, min_loss_price)
    return target_price

def simulation(df, krw_balance, crypto_balance_in_krw, amount, min_diff):
    global latest_buy_price
    open_row = df.iloc[0]
    open_price = open_row['open']
    crypto_balance = crypto_balance_in_krw / open_price
    open_total_balance = krw_balance + crypto_balance * open_price
    latest_krw_balance = open_total_balance
    print("{} start:{}"
        .format(
            open_row.name, get_status_string(open_row['open'], open_row['volume'], krw_balance, crypto_balance)
        )
    )
    for i in range(len(df)):
        if i<1:
            continue
        current_row = df.iloc[i]
        latest2_row = df.iloc[i-1:i+1]
        timestamp = current_row.name
        current_price = current_row['open']
        volume = current_row['volume']
        crypto_balance_in_krw = crypto_balance * current_price
        time_to_buy = krw_balance > crypto_balance_in_krw and volume >= min_volumn_to_buy and current_row['close'] > current_row['open']
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

            target_price = math.ceil(get_target_price_to_buy(latest2_row)/unit_price)*unit_price
            amount = krw_balance
            krw_balance -= amount
            crypto_balance += (amount / target_price) * (1 - fee_rate)
            total_krw = krw_balance + crypto_balance * target_price
            print("{} buy: {}".format(
                timestamp, get_status_string(target_price, volume, krw_balance, crypto_balance)
                )
            )
            latest_buy_price = current_price

        if time_to_sell and sell_condition(latest2_row):

            target_price = math.trunc(get_target_price_to_sell(latest2_row)/unit_price)*unit_price
            amount = crypto_balance
            krw_balance += amount * target_price * (1 - fee_rate)
            crypto_balance -= amount
            total_krw = krw_balance + crypto_balance * target_price

            result_comment = "earned={}({}%)".format(
                    human_readable(total_krw-latest_krw_balance),
                    get_compate_rate(latest_krw_balance, total_krw)
                )

            print("{} sell: {};{}".format(
                timestamp,
                get_status_string(target_price, volume, krw_balance, crypto_balance),
                result_comment
                )
            )
            latest_krw_balance = total_krw

    close_row = df.iloc[-1]
    timestamp = close_row.name

    print("---------------------------------------------------")
    print("{} finish: {}".format(
        close_row.name, get_status_string(close_row['close'], close_row['volume'], krw_balance, crypto_balance)
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
