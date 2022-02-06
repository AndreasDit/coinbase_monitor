from datetime import datetime
import sys
import pandas as pd
import tweepy as tw
import yaml
import argparse
sys.path.append('.')
from utils import connectivity as connect
import coinbase_src.load_data_from_api as cb
from coinbase_src.load_data_from_api import S_NOW
import utils.logs as logs
import utils.configs_for_code as cfg
from coinbase.wallet.client import Client
from datetime import datetime as dt

configs_file = open(cfg.PATH_CONFIG_FILE, 'r')
configs = yaml.load(configs_file, Loader=yaml.FullLoader)
logger = logs.create_logger(__name__)

parser = argparse.ArgumentParser(allow_abbrev=False)
# parser.add_argument("--nb-hashtag", type=str, required=True, help="number of used hashtag")
# args = parser.parse_args()
# nb_hashtag = int(args.nb_hashtag)

CB_API_KEY = configs['coinbase']['cb_api_key']
CB_API_SECRET = configs['coinbase']['cb_api_secret']

client = Client(CB_API_KEY, CB_API_SECRET)
accounts = client.get_accounts(limit=300)

# Get balance right now
df_balance_altcoins = cb.get_balance_data(accounts)

# Get rates for all coins in BTC right now
df_rates = cb.get_rates_in_btc(client)
df_rates['timestamp'] = S_NOW

# Get what the altcoins are worth in BTC right now
df_balance_altcoins_btc = pd.merge(df_balance_altcoins, df_rates, on=['coin_name'], how='left')
df_balance_altcoins_btc['native_balance_BTC'] = df_balance_altcoins_btc['balance_amount'] * df_balance_altcoins_btc['coin_price_BTC']

# Get transactions for alt coins
df_altcoin_transactions_btc = cb.get_transactions_in_btc(df_balance_altcoins, client)

# Get what was paid for in BTC
df_altcoin_btc_total = df_altcoin_transactions_btc[['wallet_name', 'amount_BTC']].groupby('wallet_name').sum()
df_altcoin_btc_total = df_altcoin_btc_total.reset_index()
df_altcoin_btc_total['timestamp'] = S_NOW

# print(df_balance_altcoins)
# print(df_balance_altcoins_btc.columns)
# print(df_balance_altcoins_btc[['coin_name', 'native_balance_EUR', 'balance_amount', 'native_balance_BTC']])
# print(df_altcoin_transactions_btc)
# print(df_altcoin_btc_total)

# Write dataframes to SQL DB
connect.write_df_to_sql_table(df_rates, 'coin_rates', 'coinbase', 'append')
connect.write_df_to_sql_table(df_balance_altcoins_btc, 'balance_altcoins_btc', 'coinbase', 'append')
connect.write_df_to_sql_table(df_altcoin_btc_total, 'altcoin_btc_total', 'coinbase')

