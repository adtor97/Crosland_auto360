import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def iter_pd(df):
    for val in df.columns:
        yield val
    for row in df.to_numpy():
        for val in row:
            if pd.isna(val):
                yield ""
            else:
                yield val

def pandas_to_sheets(pandas_df, sheet, clear = True):
    # Updates all values in a workbook to match a pandas dataframe
    if clear:
        sheet.clear()
    (row, col) = pandas_df.shape
    cells = sheet.range("A1:{}".format(gspread.utils.rowcol_to_a1(row + 1, col)))
    for cell, val in zip(cells, iter_pd(pandas_df)):
        cell.value = val
    sheet.update_cells(cells)

def open_ws(sheet, ws_name):
    scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
                                        'google-credentials.json', scope) # Your json file here

    gc = gspread.authorize(credentials)

    ws = gc.open(sheet).worksheet(ws_name)

    return ws

def read_ws_data(ws):

    data = ws.get_all_values()
    headers = data.pop(0)

    df = pd.DataFrame(data, columns=headers)

    return df
