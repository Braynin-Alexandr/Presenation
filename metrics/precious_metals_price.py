import pandas as pd
from datetime import datetime, timedelta


MONTH_NAMES_RU = {
    1: 'Январь',
    2: 'Февраль',
    3: 'Март',
    4: 'Апрель',
    5: 'Май',
    6: 'Июнь',
    7: 'Июль',
    8: 'Август',
    9: 'Сентябрь',
    10: 'Октябрь',
    11: 'Ноябрь',
    12: 'Декабрь'
}

METALLS = {
    1: 'Золото',
    2: 'Серебро',
    3: 'Платина',
    4: 'Палладий'
}

end_date = datetime.today()
start_date = (end_date - timedelta(days=120)).replace(day=1)

date_req1 = start_date.strftime('%d/%m/%Y')
date_req2 = end_date.strftime('%d/%m/%Y')


def get_monthly_avg(df: pd.DataFrame, metall_name: str) -> pd.Series:
    metall_df = df[df['Драгоценный металл'] == metall_name]
    return metall_df['Цена'].resample('ME').mean()


def get_precious_metals_price() -> pd.DataFrame:
    try:
        url = f'https://www.cbr.ru/scripts/xml_metall.asp?date_req1={date_req1}&date_req2={date_req2}'
        df = pd.read_xml(url, xpath='.//Record', parser='etree')

        df['Code'] = df['Code'].map(METALLS)
        df['Date'] = pd.to_datetime(df['Date'], format='%d.%m.%Y')
        df['Buy'] = df['Buy'].str.replace(',', '.').astype(float)
        df = df[['Date', 'Code', 'Buy']].set_index('Date')
        df.index.name = None
        df = df.rename(columns={'Code': 'Драгоценный металл', 'Buy': 'Цена'})

        latest_rates_df = df.iloc[-4:, :]

        latest_rates_df.index = latest_rates_df.index.strftime('%d.%m.%Y')
        latest_rates_df = latest_rates_df.pivot(columns='Драгоценный металл', values='Цена')
        latest_rates_df.index.name = None

        monthly_data = {}

        for metall in METALLS.values():
            monthly_data[metall] = get_monthly_avg(df=df.iloc[:-4, :], metall_name=metall)

        rates_df = pd.DataFrame(monthly_data)
        rates_df.index = rates_df.index.month.map(MONTH_NAMES_RU)

        summary_df = pd.concat([rates_df.iloc[:-1, :], latest_rates_df])

        last_row = summary_df.iloc[-1, :]
        prev_row = summary_df.iloc[-2, :]

        dynamics_series = (last_row-prev_row) / prev_row * 100
        dynamics_series.name = 'Динамика, %'

        summary_df = pd.concat([summary_df, pd.DataFrame(dynamics_series).T]).round(2)
        return summary_df
    except Exception as e:
        print(f'Ошибка в {get_precious_metals_price.__name__}: {e}')
        return pd.DataFrame()
