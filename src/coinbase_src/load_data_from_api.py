import pandas as pd
from datetime import datetime as dt
# from coinapi_rest_v1.restapi import CoinAPIv1
import datetime, sys, os
import json 
import shutil
import tempfile
import urllib.request
import ast
import yaml
from coinbase.wallet.client import Client
import decimal

# from websocket import create_connection
import json

sys.path.append(os.getcwd())
import utils.connectivity as conns
import utils.configs_for_code as cfg
import utils.logs as logs
import pytz

configs_file = open(cfg.PATH_CONFIG_FILE, 'r')
configs = yaml.load(configs_file, Loader=yaml.FullLoader)
logger = logs.create_logger(__name__)

CB_API_KEY = configs['coinbase']['cb_api_key']
CB_API_SECRET = configs['coinbase']['cb_api_secret']
# Get Timestamp for Meta Info

tz = pytz.timezone('Europe/Berlin')
dt_now = dt.now(tz)
S_NOW = dt.strftime(dt_now, '%d-%m-%Y %H:%M:%S')

def get_balance_data(accounts):
    message = []
    data = []
    for wallet in accounts.data:

        account_id = wallet['id']

        native_balance = decimal.Decimal(wallet['native_balance']['amount'])
        str_native_balance = str(native_balance)

        balance_amount = decimal.Decimal(wallet['balance']['amount'])
        str_balance_amount = str(balance_amount)

        wallet_name = wallet['name']
        coin_name = wallet_name.split(' ')[0]

        updated_at = wallet['updated_at']


        if ( (1==1)
            & (balance_amount > 0.0)
        ):
            msg = str(wallet_name) + ' ' + str_native_balance + ' with id ' + account_id 
            message.append( msg )

            datarow = [coin_name, native_balance, balance_amount, account_id, updated_at]
            data.append(datarow)

    df_balance_altcoins_ret = pd.DataFrame(data, columns = ['coin_name', 'native_balance_EUR', 'balance_amount', 'account_id', 'ts_last_change'])
    return df_balance_altcoins_ret

def clean_coin_transactions(df_in, tsidx_colname_ine):
    df_tmp = df_in.copy()
    
    # set index
    df_in_tsidx = df_in.set_index(tsidx_colname_ine)
    df_tmp_tsidx = df_tmp.set_index(tsidx_colname_ine)
    
    # clean transactions from old zero sums. Assumption here: when sold, then everything is sold at once
    for index, row in df_in_tsidx.iterrows():
        if row.amount < 0:
            ts = row.name
            df_tmp_tsidx = df_tmp_tsidx[df_tmp_tsidx.index > ts]

    # delete index for output
    df_tmp = df_tmp_tsidx.reset_index()
    
    df_out = df_tmp
    return df_out

def get_rates_in_btc(client):
    data = []
    rates = client.get_exchange_rates(currency='BTC')
    # btc_price = decimal.Decimal(client.get_spot_price(currency_pair = 'BTC-EUR')['amount'])

    for rate in rates['rates'].items():
        mikro_faktor = 1000000
        
        # Coin Name
        str_coin = rate[0]

        # Rate in BTC instead of EUR
        curr_rate = rate[1]
        coin_price_btc = 1/decimal.Decimal(curr_rate)
        coin_price_mbtc = coin_price_btc*mikro_faktor
        
        datarow = [str_coin, coin_price_btc, S_NOW]
        data.append(datarow)

    df_rates_ret = pd.DataFrame(data, columns = ['coin_name', 'coin_price_BTC', 'timestamp'])

    return df_rates_ret


def get_transactions(wallet_id, wallet_name, client):
    txs = client.get_transactions(wallet_id)
    data = []
    for transaction in txs.data:

        trade_type = transaction['type']
        created_at = transaction['created_at']

#         print(trade_type)
        if (trade_type == 'trade') & (created_at > '2022-02-06T15:00:29Z'):
#             print(transaction)
            str_amount = str(transaction['amount']).split(' ')[1]
            amount = decimal.Decimal(str_amount)
            details = transaction['details']
            payment_method = details['payment_method_name']
            trade_id = transaction.trade['id']
            if 'Wallet' in payment_method:
                coin_name = payment_method.split(' ')[0]
            else:
                coin_name = 'dkb'

            datarow = [wallet_name, coin_name, amount, trade_id, created_at]
            data.append(datarow)
            
#             print(f"Transaction is created at {created_at} with amount {amount}. Details: {coin_name} with trade id {trade_id}.")

    df_transactions_ret = pd.DataFrame(data, columns = ['wallet_name', 'source_name', 'amount', 'trade_id', 'created_at'])
    return df_transactions_ret

def get_transactions_in_btc(df_balance_altcoins_in, client):
    df_altcoin_transactions = None
    df_btc_transactions = None
    for index, row in df_balance_altcoins_in.iterrows():
        account_id = row['account_id']
        coin_name = row['coin_name']

        if coin_name == 'BTC':
            df_btc_transactions = get_transactions(account_id, coin_name, client)[['trade_id','amount']].copy()
            df_btc_transactions['amount_BTC'] = -1 * df_btc_transactions['amount']
            df_btc_transactions = df_btc_transactions.drop('amount', axis=1)
        else:
            df_transactions_tmp = get_transactions(account_id, coin_name, client)
            df_transactions_tmp = clean_coin_transactions(df_transactions_tmp, 'created_at')
            if df_altcoin_transactions is None:
                df_altcoin_transactions = df_transactions_tmp
            else:
                df_altcoin_transactions = pd.concat([df_altcoin_transactions, df_transactions_tmp])
                
    # correction for first order missing in the wallet
    df_btc_transactions.loc[-1] = ['57bb1ac3-e523-5b15-a55e-67d5373c6916', 0.000596]

    df_altcoin_transactions_btc_ret = pd.merge(df_altcoin_transactions, df_btc_transactions, on=['trade_id'], how='left')
    df_altcoin_transactions_btc_ret = df_altcoin_transactions_btc_ret.astype({'amount': 'float64', 'amount_BTC': 'float64'})

    return df_altcoin_transactions_btc_ret