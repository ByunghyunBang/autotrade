import pykorbit
import os

def get_balance(ticker):
    """잔고 조회"""
    balances = korbit.get_balances()
    balance = balances[ticker]
    if balance is not None:
        return float(balance['available'])
    else:
        return 0

key = os.getenv('API_KEY')
secret = os.getenv('API_SECRET')
korbit = pykorbit.Korbit(key=key, secret=secret)

balances = korbit.get_balances()
# print(balances)
print("btc : ", balances["btc"])         # KRW-BTC 조회
print("krw : ", balances["krw"])         # 보유 현금 조회

symbol="btc"
krw=1000
print("매수결과 : symbol={}, krw={}".format(symbol,krw))

# btc = get_balance(symbol)
# if btc > 0.001:
#     print("매도")
#     korbit.sell_market_order(symbol, btc)
# else:
#     print("매도실패:잔액없음")

# krw = int(get_balance("krw"))
# if krw > 5000:
#     print("매수", krw)
#     order=korbit.buy_market_order(symbol,krw)
#     print(order)
# else:
#     print("매수실패:잔액없음")
