import gspread
import yaml
import os
import sys
import pandas as pd

sys.path.append(os.getcwd())
sys.path.append('.')
sys.path.append('../.')
import utils.connectivity as conns
import utils.configs_for_code as cfg
import utils.logs as logs


configs_file = open(cfg.PATH_CONFIG_FILE, 'r')
configs = yaml.load(configs_file, Loader=yaml.FullLoader)
logger = logs.create_logger(__name__)

LIST_SPREADSHEET_NAMES = configs['google']['list_spreadsheet_names']
LIST_WORKSHEET_NAMES = configs['google']['list_worksheet_names']

def empty_worksheet(worksheet):
    """
        Takes one worksheet from a google spreadsheet and deletes all data inside of it.

        :param worksheet: A google worksheet object which represents the actual worksheet that shall be emptied.
    """
    logger.info("Start empty_worksheet()")

    # create empty dummy row: a worksheet can never be truly empty
    row = []
    index = 1
    worksheet.insert_row(row, index)

    # delete the other rows
    nb_rows = worksheet.row_count
    # index starts at 1 and not at 0
    worksheet.delete_rows(start_index=2, end_index=nb_rows + 1)


def fill_worksheet_from_df(worksheet, df_input):
    """
        Writes the information inside a dataframe into a google worksheet.

        :param worksheet: A google worksheet object which represents the actual worksheet that shall be filled with data.
        :param df_input: The given dataframe whose data shall be written into a google spreadsheet.
    """
    logger.info("Start fill_worksheet_from_df()")
    
    # google does not like int32 or int64 (btw.: int gets auto cast to int64)
    for col in df_input.columns.values:
        if df_input[col].dtype == 'int64':
            df_input = df_input.astype({col: 'float'})

    # fill worksheet with header line
    all_cols = df_input.columns.values
    header = all_cols.tolist()
    worksheet.insert_row(header, 1)

    # fill worksheet with data lines
    data_rows = []
    
    for idx in range(0, len(df_input)):  # counting starts at 1 not at 0
        pd_row = df_input.iloc[idx]
        row = pd_row.tolist()
        data_rows.append(row)
    worksheet.insert_rows(data_rows, 2)


def main(credentials=None):
    """
        Main function, performs the data transfer from the Azure SQL DB to a google spreadsheet document..
    """
    logger.info("Start main()")

    # open connections
    conn_azure, cursor_azure, engine = conns.connect_to_azure_sql_db()
    if credentials:
        conn_google = conns.connect_to_google_spreadsheets(auth_type='env', credentials=credentials)
    else:
        conn_google = conns.connect_to_google_spreadsheets()

    # define SQL statements
    sql_stmts = []
    sql_stmt = """select * from data_exit.v_coinbase_total_balance_mbtc"""
    sql_stmts.append(sql_stmt)
    sql_stmt = """select * from data_exit.v_coinbase_balance_auswertung"""
    sql_stmts.append(sql_stmt)

    for idx, spreadsheet in enumerate(LIST_SPREADSHEET_NAMES):
        # defaults
        worksheet = LIST_WORKSHEET_NAMES[idx]
        sql_st = sql_stmts[idx]
        
        # load sheets
        sheet_data = conn_google.open(spreadsheet)

        # load worksheets
        data_worksheet = sheet_data.worksheet(worksheet)

        # load tables from Azure SQL DB
        df_table_data = pd.read_sql(sql_st, conn_azure)


        empty_worksheet(data_worksheet)

        fill_worksheet_from_df(data_worksheet, df_table_data)


if __name__ == "__main__":
    main()
