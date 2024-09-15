import csv
import os
import pytz
import requests
from datetime import datetime
import argparse

# Klucz api key trzeba pobrać z https://docs.polygonscan.com/getting-started/viewing-api-usage-statistics
API_KEY = "apikey"
api_key = os.environ.get("API_KEY", API_KEY)

tz = pytz.timezone('Europe/Warsaw')


user_address_map = {
    # '0x486ebcfee0466def0302a944bd6408cd2cb3e806': 'nazwa',
    # '0x486ebcfee0466def0302a944bd6408cd2cb3e806': 'nazwa',
}

CONTRACT_ZICO = "0x486ebcfee0466def0302a944bd6408cd2cb3e806"
CONTRACT_MARKET = "0x8338df80adc51da4e570bf6da803781358f3a28c"


def parse_zico(zico_string):
    zico = int(zico_string)
    zico /= 1000000000000000000
    return zico


def download_transactions(contract_address, offset, startblock, action, page=1):
    print(f"Pobieranie transakcji, początkowy blok: {startblock}")
    url = f"https://api.polygonscan.com/api?module=account&action={action}&contractaddress=" \
          f"{contract_address}&page={page}&offset={offset}&startblock={startblock}&endblock=99999999&sort=asc&apikey={api_key}"

    resp = requests.get(url=url)
    data = resp.json()

    if data['message'] == 'NOTOK':
        print(f"Błąd: {data}")
        exit(1)
    return data


def list_transactions(contract_address, action, offset=5000, startblock=0):
    block = startblock
    last_block = -1

    data = download_transactions(contract_address, offset=offset, startblock=block, action=action)
    while block != last_block:
        block = last_block
        for txn in data['result']:
            last_block = txn['blockNumber']
            yield txn
        data = download_transactions(contract_address, offset=offset, startblock=last_block, action=action)


def filter_transactions(transactions, date_from, date_to):
    for txn in transactions:
        if txn['to'] == CONTRACT_MARKET or \
                txn['from'] == CONTRACT_MARKET:
            timestamp = datetime.fromtimestamp(int(txn['timeStamp']), tz)
            if date_from < timestamp < date_to:
                yield txn


def get_trades(transactions):
    trades = {}

    for txn in transactions:
        txn_hash = txn['hash']
        if txn_hash not in trades:
            trades[txn_hash] = {}
            ts = datetime.fromtimestamp(int(txn['timeStamp']), tz).strftime('%Y-%m-%d %H:%M:%S')
            trades[txn_hash]['timestamp'] = ts

        if txn['to'] == CONTRACT_MARKET:
            trades[txn_hash]['from'] = txn['from']
            trades[txn_hash]['price'] = parse_zico(txn['value'])
            trades[txn_hash]['from_name'] = user_address_map[txn['from']] if txn['from'] in user_address_map else ''

        if txn['from'] == CONTRACT_MARKET:
            if txn['to'] == CONTRACT_ZICO:
                trades[txn_hash]['commission'] = parse_zico(txn['value'])
            else:
                trades[txn_hash]['to'] = txn['to']
                trades[txn_hash]['to_name'] = user_address_map[txn['to']] if txn['to'] in user_address_map else ''

    return trades


def save_trades_to_file(trades, filename):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["hash", "timestamp", "from", "from_name", "to", "to_name", "price", "commission"])
        for key, value in trades.items():
            writer.writerow([key, value['timestamp'], value['from'], value['from_name'], value['to'], value['to_name'], value['price'], value['commission']])


def print_users(groups):
    counter = 1
    max_name = max(len(x) for x in user_address_map.keys()) if user_address_map else 0

    for address, group in groups.items():
        name = ""
        if user_address_map:
            name = f"{group['name'].ljust(max_name)}, "
        print(f"{str(counter).rjust(3)}, {name}{address}, {'{:.2f}'.format(group['sum']).rjust(9)}")
        counter += 1


def print_top_users(trades):
    sellers = {}
    buyers = {}

    for t in trades.values():
        if t['to'] not in sellers:
            sellers[t['to']] = {'sum': 0, 'name': t['to_name']}
        if t['from'] not in buyers:
            buyers[t['from']] = {'sum': 0, 'name': t['from_name']}

        sellers[t['to']]['sum'] += t['price']
        buyers[t['from']]['sum'] += t['price']

    sellers = dict(sorted(sellers.items(), key=lambda item: item[1]['sum'], reverse=True)[:10])
    buyers = dict(sorted(buyers.items(), key=lambda item: item[1]['sum'], reverse=True)[:10])

    print("Pierwsze 10 miejsc kupujących:")
    print_users(buyers)
    print("Pierwsze 10 miejsc sprzedających:")
    print_users(sellers)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'date_from',
        type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
        const='2023-12-01', nargs='?', default='2023-12-01'
    )
    parser.add_argument(
        'date_to',
        type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
        const='2023-12-01', nargs='?', default=datetime.today().strftime('%Y-%m-%d')
    )
    args = parser.parse_args()

    date_from = tz.localize(args.date_from)
    date_to = tz.localize(args.date_to)

    date_from_string = date_from.strftime('%Y-%m-%d')
    date_to_string = date_to.strftime('%Y-%m-%d')

    print(f'Obliczanie sumy transakcji pomiędzy {date_from_string} i {date_to_string}')

    transaction_list = list(list_transactions(CONTRACT_ZICO, action="tokentx"))

    trade_list = get_trades(filter_transactions(transaction_list, date_from, date_to))

    print_top_users(trade_list)

    save_trades_to_file(trade_list, 'trades.csv')
