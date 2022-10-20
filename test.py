import pykorbit
import os

key = os.getenv('API_KEY')
secret = os.getenv('API_SECRET')
korbit = pykorbit.Korbit(key=key, secret=secret)

balances = korbit.get_balances()

print(balances["btc"])         # KRW-BTC 조회
print(balances["krw"])         # 보유 현금 조회
