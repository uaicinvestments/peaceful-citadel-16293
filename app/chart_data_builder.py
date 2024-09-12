from distutils.command.build import build
import aiohttp
import asyncio
import time
import pickle
import bisect
from datetime import datetime

START_EPOCH = 1571094000 #day of our first trade

def url_builder(ticker):
    return f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?period1={START_EPOCH}&period2=9999999999&interval=1d'

# def insert_or_add(_dict, key, value):
#     if key not in _dict:
#         _dict[key] = value
#     else:
#         _dict[key] += value

async def get_async(session, url, id):
    async with session.get(url) as resp:
        if resp.status == 404:
            raise ValueError(f'Ticker {id} is not valid!')
        return await resp.json()

async def query_yahoo(holdings):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for ticker in holdings:
            url = url_builder(ticker)
            tasks.append(asyncio.ensure_future(get_async(session, url, ticker)))

        all_resps = await asyncio.gather(*tasks)
        return all_resps

def get_data(holdings):
    # check to see if we can use the last query
    try:
        with open('last_query.pickle', 'rb') as f:
            last_query = pickle.load(f)
    except:
        last_query = {'timestamp': 0} # force it to fail
    if last_query['timestamp'] > (time.time() - 24*60*60) and last_query['holdings'] == holdings:
        return last_query['data']
    # otherwise, query yahoo
    else:
        response = asyncio.run(query_yahoo(holdings))
        storage_obj = {
            'timestamp': time.time(),
            'holdings': holdings,
            'data': response
        }
        with open('last_query.pickle', 'wb') as f:
            pickle.dump(storage_obj, f)
        return response

def build_data(holdings):
    # get and clean the data
    tickers = [x['ticker'] for x in holdings] + ['NZDAUD=X']
    all_data = get_data(tickers)
    clean_data = {}
    for holding_data in all_data:
        if holding_data['chart']['error'] != None:
            raise ValueError('Ticker')
        ticker = holding_data['chart']['result'][0]['meta']['symbol']
        clean_data[ticker] = {
            'timestamp': holding_data['chart']['result'][0]['timestamp'],
            'adjclose': holding_data['chart']['result'][0]['indicators']['adjclose'][0]['adjclose']
        }

    # generate new index by selecting all the timestamps and combining them
    new_index = list(range(START_EPOCH, int(time.time()), 24*60*60))
    # reindex on timestamp
    reindexed_data = {'timestamps': list(map(lambda x: datetime.fromtimestamp(x).date(), new_index))}
    # we're gonna use the multiple lists system again
    for ticker in clean_data:
        reindexed_data[ticker] = []

    for timestamp in new_index:
        for ticker, data in clean_data.items():
            index = bisect.bisect_left(data['timestamp'], timestamp) # find the nearest timestamp that matches with the index
            if index == len(data['timestamp']):
                index -= 1 # prevent an index error
            reindexed_data[ticker] += [data['adjclose'][index]]

    # determine value at each timestamp
    cur_holdings = []
    cur_holdings_val = 0
    output_data = {
        'timestamps': [],
        'total': [],
        'invested': []
    }
    for i in range(len(reindexed_data['timestamps'])):
        date_str = reindexed_data['timestamps'][i].strftime('%Y-%m-%d')
        output_data['timestamps'] += [date_str]
        # check the holdings to see if there were any updates on this day
        for action in holdings:
            if action['date'] == date_str:
                cur_holdings += [{
                    'ticker': action['ticker'],
                    'price': action['price'],
                    'quantity': action['quantity']
                }]
                new_investment = action['quantity'] * action['price']
                if action['ticker'][-3:] == '.AX':
                    new_investment /= reindexed_data['NZDAUD=X'][i]
                cur_holdings_val += new_investment
        # determine the values of the portfolio / invested amounts based on cur_holdings
        portfolio_value = 0
        for holding in cur_holdings:
            holding_value = holding['quantity'] * reindexed_data[holding['ticker']][i]
            # adjust for currency
            if holding['ticker'][-3:] == '.AX':
                holding_value /= reindexed_data['NZDAUD=X'][i]
            # add to total
            portfolio_value += holding_value
        output_data['total'] += [portfolio_value]
        output_data['invested'] += [cur_holdings_val]

    # return the values as json
    return output_data

def main(holdings):
    # check to see if we can use the last run
    try:
        with open('last_dataset.pickle', 'rb') as f:
            last_ds = pickle.load(f)
    except:
        last_ds = {'timestamp': 0} # force it to fail 
    if last_ds['timestamp'] > (time.time() - 24*60*60) and last_ds['holdings'] == holdings:
        return last_ds['data']
    # otherwise, run the build
    else:
        data = build_data(holdings)
        storage_obj = {
            'timestamp': time.time(),
            'holdings': holdings,
            'data': data
        }
        with open('last_dataset.pickle', 'wb') as f:
            pickle.dump(storage_obj, f)
        return data

# For testing only
if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    HOLDINGS = [
        {
            'ticker': 'CSL.AX',
            'quantity': 4,
            'price': 296.835,
            'date': '2021-08-17'
        },
        {
            'ticker': 'SSG.AX',
            'quantity': 1338,
            'price': 1.00,
            'date': '2021-09-24'
        },
        {
            'ticker': 'SPK.NZ',
            'quantity': 430,
            'price': 4.49,
            'date': '2019-10-15'
        },
        {
            'ticker': 'QAN.AX',
            'quantity': 400,
            'price': 3.64,
            'date': '2020-05-05'
        },
        {
            'ticker': 'SGM.AX',
            'quantity': 200,
            'price': 6.77,
            'date': '2020-05-05'
        },
        {
            'ticker': 'CWY.AX',
            'quantity': 622,
            'price': 2.107,
            'date': '2020-06-19'
        },
        {
            'ticker': 'RHC.AX',
            'quantity': 20,
            'price': 66.68,
            'date': '2020-06-19'
        },
    ]
    print(main(HOLDINGS))
