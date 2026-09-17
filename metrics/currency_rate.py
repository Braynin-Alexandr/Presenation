import pandas as pd
from datetime import datetime, timedelta
from utils.set_locale import set_rus_locale, set_eng_locale


CURRENCY_CODES = {'USD': 'R01235', 'EUR': 'R01239', 'CNY': 'R01375', 'AED': 'R01230'}

end_date = datetime.today()
start_date = (end_date - timedelta(days=120)).replace(day=1)
date_req1 = start_date.strftime('%d/%m/%Y')
date_req2 = end_date.strftime('%d/%m/%Y')


def get_currency_rate() -> pd.DataFrame:
    try:
        set_rus_locale()
        currency_dfs = []
        for name, code in CURRENCY_CODES.items():
            url = f'https://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={date_req1}&date_req2={date_req2}&VAL_NM_RQ={code}'
            df = pd.read_xml(url, xpath='.//Record', parser='etree')
            df['date'] = pd.to_datetime(df['Date'], format='%d.%m.%Y')
            df[name] = df['Value'].str.replace(',', '.').astype(float)
            df = df[['date', name]].set_index('date')
            currency_dfs.append(df)

        rates_df = pd.concat(currency_dfs, axis=1)

        monthly_avg = rates_df.resample('ME').mean()

        monthly_avg.index = monthly_avg.index.month_name(locale='Russian') + ' ' + monthly_avg.index.year.astype('str')

        last_row = monthly_avg.iloc[-1, :]
        prev_row = monthly_avg.iloc[-2, :]
        currency_change = (last_row - prev_row) / prev_row * 100
        df_currency_change = currency_change.to_frame(name='Динамика, %').T

        summary_df = pd.concat([monthly_avg, df_currency_change]).round(2)
        return summary_df

    except Exception as e:
        print(f'Ошибка в {get_currency_rate.__name__}: {e}')
        return pd.DataFrame()
    finally:
        set_eng_locale()
