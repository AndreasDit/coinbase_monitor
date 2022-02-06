from datetime import datetime
import sys
import pandas as pd
import tweepy as tw
import yaml
import argparse
sys.path.append('.')
from utils import connectivity as connect
import coinbase_src.load_data_from_api as cb
import utils.logs as logs
import utils.configs_for_code as cfg
from coinbase.wallet.client import Client

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
accounts = client.get_accounts(limit=200)

df_balance_altcoins = cb.get_balance_data(accounts)

df_altcoin_transactions_btc = cb.get_transactions_in_btc(df_balance_altcoins, client)

print(df_altcoin_transactions_btc)