from datetime import date, datetime, timedelta
from typing import Dict, Tuple

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


class TradingModel:
    def __init__(self, base_url: str, headers: Dict[str, str], instrument_code: str, target_period_hours: int):
        self._base_url = base_url
        self._headers = headers
        self._instrument_code = instrument_code

        self._puts, self._calls = load_options(self._base_url, self._headers, self._instrument_code)

        self._target_expiry = min({k[1] for k in self._puts.keys()},
                            key=lambda d: abs(d - (datetime.now() + timedelta(hours=target_period_hours))))
        self._strikes = {strike for strike, _ in self._puts.keys()}
    
        self._current_price = load_current_price(base_url, headers, instrument_code)

        self._remaining_hours = int(round((self._target_expiry - datetime.now()).total_seconds() / 3600, 0))
        self._cutoff_year_month = None

    def cutoff_year_month(self, year_month: Tuple[int, int]):
        self._cutoff_year_month = year_month
        
    def evaluate(self, prices_df: pandas.DataFrame, strikes_universe_size: int):
        open_prices = prices_df['open']
        period_close_series = prices_df['close'].shift(-self.remaining_hours)
        df = pandas.DataFrame({
            'prices': open_prices,
            'period_close_series': period_close_series,
        }).dropna()

        if self._cutoff_year_month is not None:
            df = df.loc[map(lambda ind: (ind.year, ind.month) >= self._cutoff_year_month, df.index)]

        strike_prices = generate_strikes(self.underlying_price, self.strikes, strikes_universe_size)

        for count, strike_price in enumerate(strike_prices, start=1):
            strike_factor = strike_price / self.underlying_price
            df[f'strike_{count}'] = df['prices'].multiply(strike_factor)
            df[f'strike_pct_{count}'] = strike_factor

            df[f'call_value_{count}'] = df['period_close_series'].subtract(df[f'strike_{count}'])
            df.loc[df[f'call_value_{count}'] < 0., f'call_value_{count}'] = 0.
            df[f'call_value_pct_{count}'] = df[f'call_value_{count}'].divide(df['prices'])

            df[f'put_value_{count}'] = df[f'strike_{count}'].subtract(df['period_close_series'])
            df.loc[df[f'put_value_{count}'] < 0., f'put_value_{count}'] = 0.
            df[f'put_value_pct_{count}'] = df[f'put_value_{count}'].divide(df['prices'])

        option_chain = []
        for count, strike_price in enumerate(strike_prices, start=1):
            put_bid, put_ask = load_bid_ask(self._base_url, self._headers, self.puts, strike_price, self.target_expiry)
            call_bid, call_ask = load_bid_ask(self._base_url, self._headers, self.calls, strike_price, self.target_expiry)
            strike_data = {
                'strike': strike_price,
                'value_call': df[f'call_value_pct_{count}'].mean() * self.underlying_price,
                'value_put': df[f'put_value_pct_{count}'].mean() * self.underlying_price,
                'value_call_median': df[f'call_value_pct_{count}'].quantile(0.5) * self.underlying_price,
                'value_put_median': df[f'put_value_pct_{count}'].quantile(0.5) * self.underlying_price,
                'value_call_pct': df[f'call_value_pct_{count}'].mean(),
                'call_ask': call_ask,
                'value_put_pct': df[f'put_value_pct_{count}'].mean(),
                'put_ask': put_ask
            }
            if strike_price < self.underlying_price:
                strike_data['value_call_pct'] = None
            if strike_price > self.underlying_price:
                strike_data['value_put_pct'] = None

            option_chain.append(strike_data)

        return pandas.DataFrame(option_chain).set_index('strike').sort_index()

    @property
    def puts(self):
        return self._puts

    @property
    def calls(self):
        return self._calls
    
    @property
    def strikes(self):
        return self._strikes
    
    @property
    def underlying_price(self):
        return self._current_price
    
    @property
    def remaining_hours(self):
        return self._remaining_hours

    @property
    def target_expiry(self):
        return self._target_expiry
