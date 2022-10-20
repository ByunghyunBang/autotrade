import pykorbit

key = "xxx"          # 본인 값으로 변경
secret = "xxx"          # 본인 값으로 변경
korbit = pykorbit.Korbit(key=key, secret=secret)

balances = korbit.get_balances()
print(balances)
print(balances["btc"])         # KRW-BTC 조회
print(balances["KRW"])         # 보유 현금 조회