import pyupbit
import os

access = os.getenv('UPBIT_ACCESS')
secret = os.getenv('UPBIT_SECRET')

upbit = pyupbit.Upbit(access, secret)

print(upbit.get_balance("KRW-BTC"))     # KRW-BTC 조회
print(upbit.get_balance("KRW"))         # 보유 현금 조회