import pyupbit
import numpy as np

###################################
# 순환 매수매도 알고리즘 구현
###################################

market = "KRW-ETH"

# test_period = "20221020" # 횡보장
# test_period = "20221030" # 상승장
# test_period = "20220921" # 하락장

# OHLCV(open, high, low, close, volume)로 당일 시가, 고가, 저가, 종가, 거래량에 대한 데이터
# df = pyupbit.get_ohlcv(market, interval="minute240", count=6 * 90, to=test_period)
# df = pyupbit.get_ohlcv(market, interval="minute60", count=24 * 120, to=test_period)
# df = pyupbit.get_ohlcv(market, interval="day", count=90, to=test_period)
df = pyupbit.get_ohlcv(market, interval="day", count=24 * 120)

df['low_rate'] = round((df['open'] - df['low']) / df['open'] * 100, 2)
df['high_rate'] = round((df['high'] - df['open']) / df['open'] * 100, 2)
df['direction'] = np.where(df['open'] > df['close'], "down", "up")

# 3-series candle
# df['time_to_buy'] = (df['direction'].shift(4) == "down") & (df['direction'].shift(3) == "down") & (df['direction'].shift(2) == "down") & (df['direction'].shift(1) == "up") & (df['open'].shift(4) > df['open'])
# df['time_to_sell'] = (df['direction'].shift(4) == "up") & (df['direction'].shift(3) == "up") & (df['direction'].shift(2) == "up") & (df['direction'].shift(1) == "down") & (df['open'].shift(4) < df['open'])

# 2-series candle
df['time_to_buy'] = (df['direction'].shift(3) == "down") & (df['direction'].shift(2) == "down") & (df['direction'].shift(1) == "up") & (df['open'].shift(3) > df['open'])
df['time_to_sell'] = (df['direction'].shift(3) == "up") & (df['direction'].shift(2) == "up") & (df['direction'].shift(1) == "down") & (df['open'].shift(3) < df['open'])

print(df)
print("--------------------------")

def human_readable(num):
    return format(int(num), ',')

def get_compate_rate(num1, num2):
    return round((num2 - num1) / num1 * 100, 2)

def get_status_string(row, krw_balance, crypto_balance):
    timestamp = row.name
    current_price = row['open']
    current_total_balance = krw_balance + crypto_balance * current_price

    return "open={};krw={},crypto={},total={},krw-balance-rate={}".format(
                    human_readable(current_price),
                    human_readable(krw_balance),
                    crypto_balance,
                    human_readable(current_total_balance),
                    get_compate_rate(current_total_balance,krw_balance+current_total_balance),
            )

def simulation(df, krw_balance, crypto_balance_in_krw, amount, min_diff):
    open_row = df.iloc[0]
    open_price = open_row['open']
    crypto_balance = crypto_balance_in_krw / open_price
    last_tx_price = open_price
    last_tx_type = None
    open_total_balance = krw_balance + crypto_balance * open_price

    print("{} start:{}"
        .format(
            open_row.name, get_status_string(open_row, krw_balance, crypto_balance)
        )
    )
    for i in range(len(df)):
        current_row = df.iloc[i]
        timestamp = current_row.name
        current_price = current_row['open']
        time_to_buy = current_row['time_to_buy']
        time_to_sell = current_row['time_to_sell']
        if (not time_to_buy and not time_to_sell):
            continue

        if time_to_buy and last_tx_price > current_price + min_diff:
            # if last_tx_type != "buy":
            #     total_balance = krw_balance + crypto_balance * current_price
            #     print("{} skip buy: open={};krw={},crypto={},total={}".format(
            #         timestamp,
            #         human_readable(current_price),
            #         human_readable(krw_balance),
            #         crypto_balance,
            #         human_readable(total_balance)
            #         )
            #     )
            #     continue

            if krw_balance > amount * 1.5:
                last_tx_price = current_price
                last_tx_type = "buy"
                krw_balance -= amount
                crypto_balance += amount / current_price
                print("{} buy: {}".format(
                    timestamp, get_status_string(current_row, krw_balance, crypto_balance)
                    )
                )
            else:
                print("{} cannot buy: {}".format(
                    timestamp, get_status_string(current_row, krw_balance, crypto_balance)
                    )
                )

        if time_to_sell and current_price > last_tx_price + min_diff:
            # if last_tx_type != "sell":
            #     total_balance = krw_balance + crypto_balance * current_price
            #     print("{} skip sell: open={};krw={},crypto={},total={}".format(
            #         timestamp,
            #         human_readable(current_price),
            #         human_readable(krw_balance),
            #         crypto_balance,
            #         human_readable(total_balance)
            #         )
            #     )
            #     continue

            if crypto_balance > (amount / current_price) * 2 :
                last_tx_price = current_price
                last_tx_type = "sell"
                krw_balance += amount
                crypto_balance -= amount / current_price

                print("{} sell: {}".format(
                    timestamp, get_status_string(current_row, krw_balance, crypto_balance)
                    )
                )

            else:
                print("{} cannot sell: {}".format(
                    timestamp, get_status_string(current_row, krw_balance, crypto_balance)
                    )
                )

    close_row = df.iloc[-1]
    timestamp = close_row.name

    print("{} finish: {}".format(
        close_row.name, get_status_string(close_row, krw_balance, crypto_balance)
        )
    )

    close_price = close_row['open']
    close_total_balance = krw_balance + crypto_balance * close_price
    print("price_rate={};balance_rate={}"
        .format(
            get_compate_rate(open_price, close_price),
            get_compate_rate(open_total_balance, close_total_balance),
        )
    )

simulation(df, krw_balance = 3000 * 10000, crypto_balance_in_krw = 3000 * 10000, amount= 750 * 10000, min_diff = 10000)
