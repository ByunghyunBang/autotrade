import pyupbit
import numpy as np

market = "KRW-ETH"

# OHLCV(open, high, low, close, volume)로 당일 시가, 고가, 저가, 종가, 거래량에 대한 데이터
df = pyupbit.get_ohlcv(market, interval="minute60", count=200, to="20221020")

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

def simulation(df, krw_balance, crypto_balance, amount, min_diff):
    open_price = df.iloc[0]['open']
    last_tx_price = open_price
    print("{} start:open={},krw={},crypto={},total={}"
        .format(
            df.iloc[0].name,
            human_readable(open_price),
            human_readable(krw_balance),
            human_readable(crypto_balance),
            human_readable(krw_balance + crypto_balance * open_price)
            )
        )
    for i in range(len(df)):
        row = df.iloc[i]
        timestamp = row.name
        current_price = row['open']
        time_to_buy = row['time_to_buy']
        time_to_sell = row['time_to_sell']
        if (not time_to_buy and not time_to_sell):
            continue
        if time_to_buy and last_tx_price > current_price + min_diff:
            if krw_balance > 10000:
                last_tx_price = current_price
                krw_balance -= amount
                crypto_balance += amount / current_price
                total_balance = krw_balance + crypto_balance * current_price
                print("{} buy: open={};krw={},crypto={},total={}".format(
                    timestamp,
                    human_readable(current_price),
                    human_readable(krw_balance),
                    crypto_balance,
                    human_readable(total_balance)
                    )
                )
            else:
                print("{} cannot buy".format(timestamp))
        if time_to_sell and current_price > last_tx_price + min_diff:
            if crypto_balance > 0.001:
                last_tx_price = current_price
                krw_balance += amount
                crypto_balance -= amount / current_price
                total_balance = krw_balance + crypto_balance * current_price
                print("{} sell: open={};krw={},crypto={},total={}".format(
                    timestamp,
                    human_readable(current_price),
                    human_readable(krw_balance),
                    crypto_balance,
                    human_readable(total_balance)
                    )
                )
            else:
                print("{} cannot sell".format(timestamp))

    row = df.iloc[-1]
    timestamp = row.name
    current_price = row['open']
    print("{} finish: open={},krw={},crypto={},total={}"
        .format(
            row.name,
            human_readable(current_price),
            human_readable(krw_balance),
            crypto_balance,
            human_readable(krw_balance + crypto_balance * current_price)
            )
        )

simulation(df, krw_balance=30000000, crypto_balance=16, amount=1000 * 10000, min_diff = 0)
