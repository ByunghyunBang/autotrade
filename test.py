import pykorbit

key = "xxxxx"          # 본인 값으로 변경
secret = "xxxxx"          # 본인 값으로 변경
korbit = pykorbit.Korbit(key=key, secret=secret)

balances = korbit.get_balances()

print(balances["btc"])         # KRW-BTC 조회
print(balances["krw"])         # 보유 현금 조회