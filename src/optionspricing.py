import os
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Tuple, List

import pandas
import requests


def generate_strikes(price: float, option_strikes, count_options):
    sorted_strikes = sorted(option_strikes)
    closest_strike = min(sorted_strikes, key=lambda s: abs(s - price))
    closest_strike_pos = sorted_strikes.index(closest_strike)
    return sorted_strikes[closest_strike_pos - count_options: closest_strike_pos + count_options + 1]


def load_bid_ask(base_url: str, headers: Dict[str, str], options, strike: float, expiry: date) -> Tuple[float, float]:
    instrument_id = options[(strike, expiry)]
    get_bid_ask = f"{base_url}/get_order_book_by_instrument_id?instrument_id={instrument_id}&depth=1"
    response_bid_ask = requests.get(get_bid_ask, headers=headers)

    if response_bid_ask.status_code != 200:
        raise IOError(f'request failed with error {response_bid_ask.status_code}')

    bid_ask = response_bid_ask.json()['result']
    bid = ask = None
    if 'bids' in bid_ask and bid_ask['bids'] and bid_ask['bids'][0] and bid_ask['bids'][0][0]:
        bid = bid_ask['bids'][0][0]
    if 'asks' in bid_ask and bid_ask['asks'] and bid_ask['asks'][0] and bid_ask['asks'][0][0]:
        ask = bid_ask['asks'][0][0]
    return bid, ask


def load_current_price(base_url: str, headers: Dict[str, str], instrument_code: str):
    get_current_price = f"{base_url}/get_index_price?index_name={instrument_code.lower()}_usd"
    response_current_price = requests.get(get_current_price, headers=headers)

    if response_current_price.status_code != 200:
        raise IOError(f'request failed with error {response_current_price.status_code}')

    return response_current_price.json()['result']['index_price']


def load_options(base_url: str, headers: Dict[str, str], instrument_code: str):
    get_options = f"{base_url}/get_instruments?currency={instrument_code}&kind=option&expired=false"
    response_options = requests.get(get_options, headers=headers)
    if response_options.status_code != 200:
        raise IOError(f'request failed with error {response_options.status_code}')

    result = response_options.json()['result']
    puts = {}
    calls = {}
    for option in result:
        if option['option_type'] == 'put':
            puts[(option['strike'], datetime.fromtimestamp(option['expiration_timestamp'] / 1000))] = option[
                'instrument_id']
        elif option['option_type'] == 'call':
            calls[(option['strike'], datetime.fromtimestamp(option['expiration_timestamp'] / 1000))] = option[
                'instrument_id']
    return puts, calls


class TradingScenario:
    def __init__(self, underlying_price, target_expiry, remaining_hours, options_chain):
        self._underlying_price = underlying_price
        self._target_expiry = target_expiry
        self._remaining_hours = remaining_hours
        self._options_chain = options_chain
        self._cases = []
        self._backtests = []

    @property
    def options_chain(self):
        return self._options_chain

    def evaluate_call(self, strike_price: int):
        target_option_strike = float(strike_price)
        target_option_type = "call"
        return self.options_chain.loc[target_option_strike][f"value_{target_option_type}"]

    def get_call_bid(self, strike_price: int):
        target_option_strike = float(strike_price)
        target_option_type = "call"
        return self.options_chain.loc[target_option_strike][f"{target_option_type}_bid"] * self._underlying_price
    
    def evaluate_put(self, strike_price: int):
        target_option_strike = float(strike_price)
        target_option_type = "put"
        return self.options_chain.loc[target_option_strike][f"value_{target_option_type}"]

    def get_put_bid(self, strike_price: int):
        target_option_strike = float(strike_price)
        target_option_type = "put"
        return self.options_chain.loc[target_option_strike][f"{target_option_type}_bid"] * self._underlying_price
    
    def __repr__(self):
        rows = [
            f'target expiry: {self._target_expiry.astimezone(timezone.utc).strftime("%a %d %b, %H:%M")} ({self._remaining_hours} hours left)',
            f'current price: {self._underlying_price}'
        ]
        for case in self._cases:
            rows.extend(
                (
                    "-------------------------------",
                    f"trading put {case['put_name']:.0f} and call {case['call_name']:.0f} (hit ratio: {case['hit_ratio']:.0%})",
                    f"cost: {case['cost']:.3f} / value: {case['value']:.3f}, benefit/cost = {case['gain_ratio']:.1f}x",
                    f"($) cost: {case['cost_amount']:.2f} / value: {case['value_amount']:.2f}, average gain = {case['gain_amount']:.2f}"
                )
            )
        return os.linesep.join(rows)

    def allocate(self, trading_cases: List[int], budget: float):
        if not (set(trading_cases) <= set(range(len(self.cases)))):
            raise ValueError(f'case {trading_cases} are not part of available trading cases')

        trades = []
        portion = budget / len(trading_cases)
        for case in trading_cases:
            trade = {
                "put": self.cases[case]["put_name"],
                "call": self.cases[case]["call_name"],
                "quantity": int(round(portion / self.cases[case]["cost_amount"], 0))
            }
            trades.append(trade)

        return trades

    def add_case(self, count, hit_ratio, put_name, call_name, cost, value, gain_ratio, cost_amount, value_amount, gain_amount):
        case_dict = {
            'count': count,
            'hit_ratio': hit_ratio,
            'put_name': put_name,
            'call_name': call_name,
            'cost': cost,
            'value': value,
            'gain_ratio': gain_ratio,
            'cost_amount': cost_amount,
            'value_amount': value_amount,
            'gain_amount': gain_amount
        }
        self._cases.append(case_dict)

    @property
    def cases(self):
        return self._cases

    def add_backtest(self, backtest):
        self._backtests.append(backtest)

    @property
    def backtests_returns(self):
        return self._backtests

    def backtests_prices(self, count: int):
        return (1 + self.backtests_returns[count]).cumprod()

    def backtests_drawdowns(self, count: int):
        return self.backtests_prices(count) - self.backtests_prices(count).cummax()

    def backtests_period_drawdowns(self, count: int):
        drawdown = self.backtests_prices(count) - self.backtests_prices(count).cummax()
        # Finds the start and end indices of each drawdown
        drawdown_start = (drawdown < 0) & (drawdown.shift(1) >= 0)

        # Calculates the duration of each drawdown
        return drawdown_start.groupby((drawdown_start != drawdown_start.shift()).cumsum()).cumcount() + 1


class TradingModel:
    def __init__(self, base_url: str, headers: Dict[str, str], instrument_code: str, target_period_hours: int):
        self._base_url = base_url
        self._headers = headers
        self._instrument_code = instrument_code

        self._puts, self._calls = load_options(self._base_url, self._headers, self._instrument_code)

        self._target_expiry = min({k[1] for k in self._puts.keys()},
                                  key=lambda d: abs(d - (datetime.now() + timedelta(hours=target_period_hours))))

        self._put_strikes = {strike for strike, expiry in self._puts.keys() if expiry == self._target_expiry}
        self._call_strikes = {strike for strike, expiry in self._calls.keys() if expiry == self._target_expiry}

        self._current_price = load_current_price(base_url, headers, instrument_code)

        self._remaining_hours = int(round((self._target_expiry - datetime.now()).total_seconds() / 3600, 0))
        self._cutoff_year_month = None
        self._valuation = None
        self._strike_prices = None

    def cutoff_year_month(self, year_month: Tuple[int, int]):
        self._cutoff_year_month = year_month

    def evaluate(self, prices_df: pandas.DataFrame, strikes_universe_size: int) -> TradingScenario:
        open_prices = prices_df['open']
        period_close_series = prices_df['close'].shift(-self.remaining_hours)
        df = pandas.DataFrame({
            'prices': open_prices,
            'period_close_series': period_close_series,
        }).dropna()

        if self._cutoff_year_month is not None:
            df = df.loc[map(lambda ind: (ind.year, ind.month) >= self._cutoff_year_month, df.index)]

        strike_prices = generate_strikes(self.underlying_price, self.put_strikes, strikes_universe_size)
        self._strike_prices = strike_prices
        for count, strike_price in enumerate(strike_prices, start=1):
            strike_factor = strike_price / self.underlying_price
            df[f'strike_{count}'] = df['prices'].multiply(strike_factor)
            df[f'strike_pct_{count}'] = strike_factor * 100.

            call_values = df['period_close_series'].subtract(df[f'strike_{count}'])
            df[f'call_value_pct_{count}'] = call_values.divide(df['prices'])
            df.loc[df[f'call_value_pct_{count}'] < 0., f'call_value_pct_{count}'] = 0.

            put_values = df[f'strike_{count}'].subtract(df['period_close_series'])
            df[f'put_value_pct_{count}'] = put_values.divide(df['prices'])
            df.loc[df[f'put_value_pct_{count}'] < 0., f'put_value_pct_{count}'] = 0.

        self._valuation = df

        option_chain = []
        for count, strike_price in enumerate(strike_prices, start=1):
            put_bid, put_ask = load_bid_ask(self._base_url, self._headers, self.puts, strike_price, self.target_expiry)
            call_bid, call_ask = load_bid_ask(self._base_url, self._headers, self.calls, strike_price,
                                              self.target_expiry)
            strike_data = {
                'strike': strike_price,
                'value_call': df[f'call_value_pct_{count}'].mean() * self.underlying_price,
                'value_call_pct': df[f'call_value_pct_{count}'].mean(),
                'call_bid': call_bid,
                'call_ask': call_ask,
                'value_put': df[f'put_value_pct_{count}'].mean() * self.underlying_price,
                'value_put_pct': df[f'put_value_pct_{count}'].mean(),
                'put_bid': put_bid,
                'put_ask': put_ask
            }
            if strike_price < self.underlying_price:
                strike_data['value_call_pct'] = None
            if strike_price > self.underlying_price:
                strike_data['value_put_pct'] = None

            option_chain.append(strike_data)

        option_chain_df = pandas.DataFrame(option_chain).set_index('strike').sort_index()
        return self.simulation(option_chain_df, strikes_universe_size)

    @property
    def puts(self):
        return self._puts

    @property
    def calls(self):
        return self._calls

    @property
    def strike_prices(self):
        return self._strike_prices

    @property
    def put_strikes(self):
        return self._put_strikes

    @property
    def call_strikes(self):
        return self._call_strikes

    @property
    def underlying_price(self):
        return self._current_price

    @property
    def remaining_hours(self):
        return self._remaining_hours

    @property
    def target_expiry(self):
        return self._target_expiry

    @property
    def valuation(self):
        return self._valuation

    def simulation(self, option_chain_df: pandas.DataFrame, strikes_universe_size: int):
        scenario = TradingScenario(self.underlying_price, self.target_expiry, self.remaining_hours, option_chain_df)
        for count in range(1, strikes_universe_size + 1):
            index_put = strikes_universe_size - count + 1
            index_call = strikes_universe_size + count + 1
            cost, value = (
                option_chain_df.iloc[index_put - 1]['put_ask'] + option_chain_df.iloc[index_call - 1]['call_ask'],
                option_chain_df.iloc[index_put - 1]['value_put_pct'] + option_chain_df.iloc[index_call - 1][
                    'value_call_pct']
            )
            strategy_value_pct = (self.valuation[f"put_value_pct_{index_put}"]
                                  + self.valuation[f"call_value_pct_{index_call}"])
            hit_ratio = strategy_value_pct.loc[(strategy_value_pct - cost) > 0.].count() / strategy_value_pct.count()
            scenario.add_case(count, hit_ratio,
                              option_chain_df.iloc[index_put - 1].name,
                              option_chain_df.iloc[index_call - 1].name,
                              cost,
                              value,
                              value / cost,
                              cost * self.underlying_price,
                              value * self.underlying_price,
                              (value - cost) * self.underlying_price
                              )
            ###
            backtest_current = strategy_value_pct - cost
            backtest_sampled_daily = backtest_current.loc[backtest_current.index.hour == 9]
            scenario.add_backtest(backtest_sampled_daily)
        return scenario
