import pykorbit

key = "4hWIjWfC7GSf9MHllleMrLn4LzYYDpZdS7fTLJpRqH6Jc79M0ELWqVrODpn0u"          # 본인 값으로 변경
secret = "aD0xZGOnePgVIeGItBiT0n10OfauxR1CKDwHhgPuGJkYPIJMDQBumuEwpzMd0"          # 본인 값으로 변경
korbit = pykorbit.Korbit(key=key, secret=secret)

balances = korbit.get_balances()
print(balances)
print(balances["btc"])         # KRW-BTC 조회
print(balances["krw"])         # 보유 현금 조회