import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Set, Tuple, List

import pandas
import requests

from dataclasses import dataclass, field


@dataclass
class ScenarioRunResult:
    count: int
    hit_ratio: float
    cost: float
    value: float
    underlying_price: float
    option_chain_df: pandas.DataFrame
    put_weights: List[float]
    call_weights: List[float]
    scale_factor: float
    
    gain_pct: float = field(init=False)
    cost_amount: float = field(init=False)
    value_amount: float = field(init=False)
    gain_amount: float = field(init=False)

    def __post_init__(self):
        self.cost_amount = self.cost * self.scale_factor
        self.value_amount = self.value * self.scale_factor
        self.gain_amount = (self.value - self.cost) * self.scale_factor
        self.gain_pct = self.gain_amount / self.scale_factor


def generate_strikes(price: float, option_strikes, count_options) -> List[float]:
    sorted_strikes = sorted(option_strikes)
    closest_strike = min(sorted_strikes, key=lambda s: abs(s - price))
    closest_strike_pos = sorted_strikes.index(closest_strike)
    return sorted_strikes[closest_strike_pos - count_options: closest_strike_pos + count_options + 1]


def load_bid_ask(base_url: str, headers: Dict[str, str], options: Dict[Tuple[float, datetime], str], strike: float, expiry: datetime) -> Tuple[float, float]:
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


def load_options(base_url: str, headers: Dict[str, str], instrument_code: str) -> Tuple[Dict[Tuple[float, datetime], str], Dict[Tuple[float, datetime], str]]:
    if instrument_code in ('SOL', ):
        currency_code = 'USDC'
        
    else:
        currency_code = instrument_code
        
    get_options = f"{base_url}/get_instruments?currency={currency_code}&kind=option&expired=false"
    logging.warning(f"calling option chain: {get_options}")
    response_options = requests.get(get_options, headers=headers)
    if response_options.status_code != 200:
        raise IOError(f'request failed with error {response_options.status_code}')

    result = response_options.json()['result']
    puts = {}
    calls = {}
    for option in result:
        if currency_code == 'USDC' and not option['instrument_name'].startswith('SOL_'):
            continue
        if option['option_type'] == 'put':
            puts[(option['strike'], datetime.fromtimestamp(option['expiration_timestamp'] / 1000))] = option['instrument_id']
        elif option['option_type'] == 'call':
            calls[(option['strike'], datetime.fromtimestamp(option['expiration_timestamp'] / 1000))] = option['instrument_id']
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

    def add_case(self, result: ScenarioRunResult):
        self._cases.append(result)

    @property
    def cases(self) -> List[ScenarioRunResult]:
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

    def __repr__(self):
        rows = [
            f'target expiry: {self._target_expiry.astimezone(timezone.utc).strftime("%a %d %b, %H:%M")} ({self._remaining_hours} hours left)',
            f'current price: {self._underlying_price}'
        ]
        for case in self.cases:
            trades = []
            for count, weights in enumerate(zip(case.put_weights, case.call_weights)):
                weight_put, weight_call = weights
                if weight_put != 0.:
                    trade = ("sell", "buy")[weight_put > 0] + f" put {case.option_chain_df.iloc[count].name}"
                    trades.append(trade)
                
                if weight_call != 0.:
                    trade = ("sell", "buy")[weight_call > 0] + f" call {case.option_chain_df.iloc[count].name}"
                    trades.append(trade)
            
            rows.extend(
                [
                    "-------------------------------",
                    f"hit ratio: {case.hit_ratio:.0%}",
                    f"cost: {case.cost:.3f} / value: {case.value:.3f}, gain% = {case.gain_pct:.2%}",
                    f"($) cost: {case.cost_amount:.2f} / value: {case.value_amount:.2f}, average gain = {case.gain_amount:.2f}"
                ] + trades
            )
        return os.linesep.join(rows)


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

    def evaluate_options(self, prices_df: pandas.DataFrame) -> pandas.DataFrame:
        open_prices = prices_df['open']
        period_close_series = prices_df['close'].shift(-self.remaining_hours)
        df = pandas.DataFrame({
            'prices': open_prices,
            'period_close_series': period_close_series,
        }).dropna()

        if self._cutoff_year_month is not None:
            df = df.loc[map(lambda ind: (ind.year, ind.month) >= self._cutoff_year_month, df.index)]
            
        for count, strike_price in enumerate(self.strike_prices, start=1):
            strike_factor = strike_price / self.underlying_price
            df[f'strike_{count}'] = df['prices'].multiply(strike_factor)
            df[f'strike_pct_{count}'] = strike_factor * 100.

            call_values = df['period_close_series'].subtract(df[f'strike_{count}'])
            df[f'call_value_pct_{count}'] = call_values.divide(df['prices'])
            df.loc[df[f'call_value_pct_{count}'] < 0., f'call_value_pct_{count}'] = 0.

            put_values = df[f'strike_{count}'].subtract(df['period_close_series'])
            df[f'put_value_pct_{count}'] = put_values.divide(df['prices'])
            df.loc[df[f'put_value_pct_{count}'] < 0., f'put_value_pct_{count}'] = 0.

        return df

    def build_option_chain_data(self) -> pandas.DataFrame:
        option_chain = []
        for count, strike_price in enumerate(self.strike_prices, start=1):
            put_bid, put_ask = load_bid_ask(self._base_url, self._headers, self.puts, strike_price, self.target_expiry)
            call_bid, call_ask = load_bid_ask(self._base_url, self._headers, self.calls, strike_price, self.target_expiry)
            strike_data = {
                'strike': strike_price,
                'value_call': self._valuation[f'call_value_pct_{count}'].mean() * self.underlying_price,
                'value_call_pct': self._valuation[f'call_value_pct_{count}'].mean(),
                'call_bid': call_bid,
                'call_ask': call_ask,
                'value_put': self._valuation[f'put_value_pct_{count}'].mean() * self.underlying_price,
                'value_put_pct': self._valuation[f'put_value_pct_{count}'].mean(),
                'put_bid': put_bid,
                'put_ask': put_ask
            }
            if strike_price < self.underlying_price:
                strike_data['value_call_pct'] = None
            if strike_price > self.underlying_price:
                strike_data['value_put_pct'] = None

            option_chain.append(strike_data)

        return pandas.DataFrame(option_chain).set_index('strike').sort_index()

    def evaluate(self, prices_df: pandas.DataFrame, strikes_universe_size: int) -> TradingScenario:
        self._strike_prices = generate_strikes(self.underlying_price, self.put_strikes, strikes_universe_size)
        self._valuation = self.evaluate_options(prices_df)
        option_chain_df = self.build_option_chain_data()
        return option_chain_df
    
    @property
    def puts(self) -> Dict[Tuple[float, datetime], str]:
        return self._puts

    @property
    def calls(self) -> Dict[Tuple[float, datetime], str]:
        return self._calls

    @property
    def strike_prices(self):
        return self._strike_prices

    @property
    def put_strikes(self) -> Set[float]:
        return self._put_strikes

    @property
    def call_strikes(self) -> Set[float]:
        return self._call_strikes

    @property
    def underlying_price(self):
        return self._current_price

    @property
    def remaining_hours(self):
        return self._remaining_hours

    @property
    def target_expiry(self) -> datetime:
        return self._target_expiry

    @property
    def valuation(self):
        return self._valuation

    def backtest(self, option_chain_df, put_weights, call_weights):
        cost = 0.
        for index, put_call_weight in enumerate(zip(put_weights, call_weights)):
            put_weight, call_weight = put_call_weight
            put_prefix = ("bid", "ask")[put_weight > 0]
            call_prefix = ("bid", "ask")[call_weight > 0]
            if put_weight != 0.:
                cost += put_weight * option_chain_df.iloc[index][f"put_{put_prefix}"]
            if call_weight != 0.:
                cost += call_weight * option_chain_df.iloc[index][f"call_{call_prefix}"]
        
        def calculate_value(row):
            value_puts = sum(row[f"put_value_pct_{count + 1}"] * weight for count, weight in enumerate(put_weights))
            value_calls = sum(row[f"call_value_pct_{count + 1}"] * weight for count, weight in enumerate(call_weights))
            return value_puts + value_calls

        return self.valuation.apply(calculate_value, axis=1), cost

    def simulate_strategy_long_straddle(self, option_chain_df: pandas.DataFrame,
                                        strikes_universe_size: int,
                                        quote_in_usd: bool=False) -> TradingScenario:
        scenario = TradingScenario(self.underlying_price, self.target_expiry, self.remaining_hours, option_chain_df)
        for count in range(strikes_universe_size):
            put_weights = [0.] * (2 * strikes_universe_size + 1)
            call_weights = [0.] * (2 * strikes_universe_size + 1)
            index_put = strikes_universe_size - count - 1
            index_call = strikes_universe_size + count + 1
            put_weights[index_put] = 1.
            call_weights[index_call] = 1.
            
            strategy_value_pct, cost = self.backtest(option_chain_df, put_weights, call_weights)
            value = strategy_value_pct.mean()
            if quote_in_usd:
                value *= self.underlying_price
                hit_ratio = strategy_value_pct.loc[(strategy_value_pct - cost / self.underlying_price) > 0.].count() / strategy_value_pct.count()
                scale_factor = 1.
            else:   
                hit_ratio = strategy_value_pct.loc[(strategy_value_pct - cost) > 0.].count() / strategy_value_pct.count()
                scale_factor =  self.underlying_price
            
            result = ScenarioRunResult(count, hit_ratio, cost, value,
                                       underlying_price=self.underlying_price,
                                       option_chain_df=option_chain_df,
                                       put_weights=put_weights,
                                       call_weights=call_weights,
                                       scale_factor=scale_factor
                                       )
            scenario.add_case(result)
            
            backtest_current = strategy_value_pct - cost
            backtest_sampled_daily = backtest_current.loc[backtest_current.index.hour == 9]
            scenario.add_backtest(backtest_sampled_daily)
        return scenario

    def simulate_strategy(self, option_chain_df: pandas.DataFrame,
                          put_weights: List[float],
                          call_weights: List[float],
                          quote_in_usd: bool=False
                          ) -> TradingScenario:
        scenario = TradingScenario(self.underlying_price, self.target_expiry, self.remaining_hours, option_chain_df)        
        strategy_value_pct, cost = self.backtest(option_chain_df, put_weights, call_weights)
        value = strategy_value_pct.mean()
        
        hit_ratio = strategy_value_pct.loc[(strategy_value_pct - cost) > 0.].count() / strategy_value_pct.count()
        
        if quote_in_usd:
            scale_factor = 1.
        else:
            scale_factor =  self.underlying_price
        
        result = ScenarioRunResult(0, hit_ratio, cost, value,
                                    underlying_price=self.underlying_price,
                                    option_chain_df=option_chain_df,
                                    put_weights=put_weights,
                                    call_weights=call_weights,
                                    scale_factor=scale_factor
                                    )
        scenario.add_case(result)
        
        backtest_current = strategy_value_pct - cost
        backtest_sampled_daily = backtest_current.loc[backtest_current.index.hour == 9]
        scenario.add_backtest(backtest_sampled_daily)
        return scenario
