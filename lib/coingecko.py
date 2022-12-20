from pycoingecko import CoinGeckoAPI
from datetime import datetime, timedelta
import yaml, time

cg = CoinGeckoAPI()

# Config Properties
with open('config.yml', 'rb') as f:
    config = yaml.safe_load(f)

trending = {}
perps = {}
movers = {}

my_file = open("market_blacklist", "r")
blacklisted_markets = my_file.read().split("\n")

def gen_json_key(json_ticker):
    return json_ticker['index_id'] + json_ticker['market'] + json_ticker['symbol']


def init():
    sync_trending()
    now = datetime.now()
    seen = []
    unseen = []
    json_data = cg.get_derivatives()

    for json_ticker in json_data:
        key = gen_json_key(json_ticker)
        if key not in seen:
            json_ticker['last_price_percentage_change'] = json_ticker['price_percentage_change_24h']
            json_ticker['last_price_percentage_change_updated_at'] = datetime.now()

            if json_ticker['index_id'] not in perps.keys():
                perps[json_ticker['index_id']] = [json_ticker]
            else:
                perps[json_ticker['index_id']] += [json_ticker]

            seen.append(key)
        else:
            print(f"Skipping seen element: {json_ticker}")
            unseen.append(json_ticker)
    print(f"init ran in {datetime.now() - now}")


def sync_perps():
    now = datetime.now()
    seen = []
    unseen = []
    json_data = cg.get_derivatives()
    for json_ticker in json_data:
        json_ticker_key = gen_json_key(json_ticker)
        if json_ticker_key in seen:
            unseen.append(json_ticker)
        else:
            seen.append(json_ticker_key)
            symbol = json_ticker['index_id']
            if symbol not in perps.keys():
                json_ticker['last_price_percentage_change'] = json_ticker['price_percentage_change_24h']
                json_ticker['last_price_percentage_change_updated_at'] = datetime.now()
                perps[symbol] = [json_ticker]
                # TODO: new symbol found message
            else:
                updated = False
                for index in range(len(perps[symbol])):
                    item = perps[symbol][index]
                    if item['market'] == json_ticker['market'] and item['symbol'] == json_ticker['symbol'] and item[
                        'price'] != json_ticker['price']:
                        # found match with updated price, update....
                        item['price'] = json_ticker['price']
                        item['funding_rate'] = json_ticker['funding_rate']
                        item['spread'] = json_ticker['spread']
                        item['price_percentage_change_24h'] = json_ticker['price_percentage_change_24h']
                        item['volume_24h'] = json_ticker['volume_24h']
                        if item['last_price_percentage_change_updated_at'] < datetime.now() - timedelta(
                                minutes=config['price_percentage_change_lookback_minutes']):
                            item['last_price_percentage_change'] = json_ticker['price_percentage_change_24h']
                            item['last_price_percentage_change_updated_at'] = datetime.now()

                        # check for mover
                        item_abs = abs(item['last_price_percentage_change'])
                        ticker_abs = abs(json_ticker['price_percentage_change_24h'])
                        if item_abs > ticker_abs:
                            dist = item_abs - ticker_abs
                        else:
                            dist = ticker_abs - item_abs
                        if dist > config['price_percentage_change_distance']:
                            item['mover_updated_at'] = datetime.now()
                            item['dist'] = dist
                            mover_updated = False
                            if symbol in movers.keys():
                                # symbol might not exist
                                for i in range(len(movers[symbol])):
                                    e = movers[symbol][i]
                                    if e['index_id'] == item['index_id'] and e['market'] == item['market'] and e[
                                        'symbol'] == item['symbol']:
                                        print("replacing MOVER\n")
                                        movers[symbol][i] = item
                                        mover_updated = True
                            else:
                                movers[symbol] = [item]
                                mover_updated = True
                            if not mover_updated:
                                # my_list.append('another')
                                movers[symbol] += [item]

                        # update item in perps list
                        perps[symbol][index] = item
                        updated = True
                    elif item['market'] == json_ticker['market'] and item['symbol'] == json_ticker['symbol'] \
                            and item['price'] == json_ticker['price']:
                        updated = True
                if not updated:
                    # found new market for this coin
                    print(f"found new market : {json_ticker['index_id']}, {json_ticker['market']}, {json_ticker['symbol']}")
                    json_ticker['last_price_percentage_change'] = json_ticker['price_percentage_change_24h']
                    json_ticker['last_price_percentage_change_updated_at'] = datetime.now()
                    perps[symbol] += [json_ticker]

    ret = ""

    mover_count = {}

    for key in movers.keys():
        moving_markets = len(movers[key])
        total_markets = len(perps[key])
        percentage = (100*moving_markets)/total_markets
        if percentage > 15:
            for i in range(len(movers[key])):
                item = movers[key][i]
                print(
                    f" - market: {item['market']}, {item['symbol']}, {item['price_percentage_change_24h']}, {item['last_price_percentage_change']}, {item['last_price_percentage_change_updated_at']}")
                if item['mover_updated_at'] > (datetime.now() - timedelta(minutes=config['mover_threshold_minutes'])):
                    # Mover has been updated in the last 15 min
                    if 'reported_at' not in item and item['market'] not in blacklisted_markets:# or ('reported_at' in item and item['reported_at'] < (datetime.now() - timedelta(minutes=config['mover_threshold_minutes']+1))):
                        # Mover has not been reported in the last 15 min
                        print("adding to mover count")
                        if key in mover_count.keys():
                            mover_count[key] += [item]
                        else:
                            mover_count[key] = [item]
                        movers[key][i]['reported_at'] = datetime.now()
                        print("setting reported at")
                        print(movers[key][i]['reported_at'])
    for key in mover_count.keys():
        ret += f"{key} is moving on exchanges:\n"
        for item in mover_count[key]:
            ret += f"   - {item['market']}: (+/-){round(item['dist'], config['fiat_round_to'])}% in the last {config['mover_threshold_minutes']} minutes, {round(item['price_percentage_change_24h'], config['fiat_round_to'])}% in the last 24h\n"
        ret += "\n"

    for key in movers.copy():
        for i in range(len(movers[key]) - 1, -1, -1):
            if 'reported_at' in movers[key][i]:
                del movers[key][i]
        if len(movers[key]) == 0:
            del movers[key]

    print(f"sync_PERPS ran in {datetime.now() - now}")

    return ret


def sync_trending():
    json_data = cg.get_search_trending()
    ret = ""
    for json_coin in json_data['coins']:
        json_coin = json_coin['item']
        if json_coin['symbol'] not in trending.keys():
            json_coin['last_updated'] = datetime.now()
            trending[json_coin['symbol']] = json_coin
            ret += f"{json_coin['symbol']} #{json_coin['market_cap_rank']} is search trending\n"
    for key in list(trending.keys()):
        remove = True
        for json_coin in json_data['coins']:
            if key == json_coin['item']['symbol']:
                remove = False
                trending[key]['last_updated'] = datetime.now()
        if remove and trending[key]['last_updated'] < datetime.now() - timedelta(minutes=config['trending_threshold_minutes']):
            print(datetime.now())
            print(trending[key]['last_updated'])
            # ret += f"{trending[key]['symbol']} is no longer search trending\n"
            trending.pop(key)
    return ret
