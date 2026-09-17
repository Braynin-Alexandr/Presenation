import pandas as pd
from metrics.currency_rate import get_currency_rate


def get_currency(currency: str) -> pd.Series | None:
    """return currency as Series for the last 5 months"""
    df_currencies = get_currency_rate()
    if df_currencies.empty:
        return None
    try:
        return df_currencies[currency].iloc[:-1]
    except Exception as e:
        print(f'Ошибка в {get_currency.__name__}: {e}')
        return None


def convert_into_rub(df: pd.DataFrame, columns: list, currency: str) -> pd.DataFrame | None:

    idx_col_dct = {df.columns.get_loc(c): c for c in df.columns}
    try:
        df_rest = df.drop(columns=columns)
        df_converted = df[columns].mul(currency, axis=0)
        df_new = pd.concat([df_converted, df_rest], axis=1)
        res_df = df_new.reindex(columns=[c for c in idx_col_dct.values()])
        return res_df
    except Exception as e:
        print(f'Ошибка в {convert_into_rub.__name__}: {e}')
        return None
