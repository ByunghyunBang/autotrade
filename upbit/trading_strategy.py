import numpy as np
from enum import Enum

class Action(Enum):
    STAY = 0
    DO = 1

class Reason(Enum):
    UNKNOWN = 0
    NOT_HIT_CONDITION = 1
    SMALL_DIFF = 2
    NOT_ENOUGH_BALANCE = 3

class Direction(Enum):
    UP = 0
    DOWN = 1

class Result:
    def __init__(self, action, reason=""):
        self.action = action
        self.reason = reason
    def __str__(self):
        return "action={},reason={}".format(str(self.action), self.reason)

class BuyAndSellTrading:
    def __init__(self, min_diff=0, tx_amount=100):
        self.min_diff = min_diff
        self.tx_amount = tx_amount
        self.last_tx_price = None

    # candles 는 최근 4개 이상이 필요
    def update_candle(self, candles):
        candles['direction'] = np.where(candles['open'] > candles['close'], Direction.DOWN, Direction.UP)
        # 2-series candle
        candles['time_to_buy'] = (candles['direction'].shift(3) == Direction.DOWN) & (candles['direction'].shift(2) == Direction.DOWN) & (candles['direction'].shift(1) == Direction.UP) & (candles['open'].shift(3) > candles['open'])
        candles['time_to_sell'] = (candles['direction'].shift(3) == Direction.UP) & (candles['direction'].shift(2) == Direction.UP) & (candles['direction'].shift(1) == Direction.DOWN) & (candles['open'].shift(3) < candles['open'])
        current_candle = candles.iloc[-1]
        self.current_candle = current_candle
        self.timestamp = current_candle.name
        self.current_price = current_candle['open']


    def update_balances(self, krw_balance, crypto_balance):
        self.krw_balance = krw_balance
        if self.last_tx_price is None:
            self.last_tx_price = self.current_price
        self.crypto_balance = crypto_balance

    def evaluate_buy_timing(self):
        time_to_buy = self.current_candle['time_to_buy']
        current_price = self.current_candle['open']

        # 시세흐름이 조건에 맞는지 확인
        if not time_to_buy:
            return Result(Action.STAY,Reason.NOT_HIT_CONDITION)
        # 최근 거래로부터 min_diff 이상의 가격 변화가 있어야 함.
        if self.last_tx_price <= current_price + self.min_diff:
            return Result(Action.STAY,Reason.SMALL_DIFF)
        # 원화잔액 확인
        if self.krw_balance <= self.tx_amount * 1.5:
            return Result(Action.STAY,Reason.NOT_ENOUGH_BALANCE)
        return Result(Action.DO)

    # def evaluate_sell_timing(self, current_candle):
