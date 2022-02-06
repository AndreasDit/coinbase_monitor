import pandas as pd
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


configs_file = open(cfg.PATH_CONFIG_FILE, 'r')
configs = yaml.load(configs_file, Loader=yaml.FullLoader)
logger = logs.create_logger(__name__)

CB_API_KEY = configs['coinbase']['cb_api_key']
CB_API_SECRET = configs['coinbase']['cb_api_secret']

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


def get_transactions(wallet_id, wallet_name, client):
    txs = client.get_transactions(wallet_id)
    data = []
    for transaction in txs.data:
#         print(transaction)

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
            df_btc_transactions['amount_BTC'] = df_btc_transactions['amount']
            df_btc_transactions = df_btc_transactions.drop('amount', axis=1)
        else:
            df_transactions_tmp = get_transactions(account_id, coin_name, client)
            if df_altcoin_transactions is None:
                df_altcoin_transactions = df_transactions_tmp
            else:
                df_altcoin_transactions = pd.concat([df_altcoin_transactions, df_transactions_tmp])

    df_altcoin_transactions_btc_ret = pd.merge(df_altcoin_transactions, df_btc_transactions, on=['trade_id'], how='left')
    
    return df_altcoin_transactions_btc_ret