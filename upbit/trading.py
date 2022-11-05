class TradingStragy:

    def reset(self):
        self.buyed = False

    def upset_ohlcv_day2(self, ohlcv_day2):
        self.ohlcv_day2 = ohlcv_day2

    def set_buyed(self, buyed):
        self.buyed = buyed

    def can_buy(self):
        if (self.buyed):
            return True
        else:
            return False

    def ohlcv_yesterday(self):
        self.ohlcv_day2.iloc[0]

    def ohlcv_today(self):
        self.ohlcv_day2.iloc[1]

    def get_yester_volatility(self):
        yesterday = self.ohlcv_yesterday()
        return yesterday['high'] - yesterday['low']

    def get_target_price(self, k):
        """변동성 돌파 전략으로 매수 목표가 조회"""
        yesterday = self.ohlcv_yesterday()
        target_price = yesterday['close'] + self.get_yester_volatility() * k
        return target_price

    def get_target_price2(self, k):
        """변동성 돌파 전략으로 매수 목표가 조회 (어제 종가 + 오늘 최저가 가중치 반영으로 매수 목표 설정)"""
        yesterday = self.ohlcv_yesterday()
        today = self.ohlcv_today()
        base = get_middle(yesterday['close'], today['low'], 0.6)
        target_price = base + self.get_yester_volatility() * k
        return target_price

class TradingAction:

    def __init__(self, pyupbit):
        self.pyupbit = pyupbit

    def get_ohlcv_day2(self):
        self.ohlcv_day2 = pyupbit.get_ohlcv(market, interval="day", count=2)

    def get_balance():
        return 0

def get_middle(value1, value2, rate=0.5):
    return value1 + (value2 - value1) * rate

def get_today_open(ohlcv_day2):
    df = ohlcv_day2
    return df.iloc[1]['open']

def get_start_time(market):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(market, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(market):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=market)["orderbook_units"][0]["ask_price"]

def log(msg):
    now = datetime.datetime.now()
    print(now, msg)

def clear_flags():
    global meet_expected_price, emergency_sell, is_frozen, frozen_time
    meet_expected_price=False
    emergency_sell=False
    is_frozen=False
    frozen_time=time.time()

def set_freeze(now):
    global is_frozen, frozen_time
    is_frozen=True
    frozen_time=now
