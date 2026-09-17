import pandas as pd


MONTH_NAMES_RU = {
    1: 'январь',
    2: 'февраль',
    3: 'март',
    4: 'апрель',
    5: 'май',
    6: 'июнь',
    7: 'июль',
    8: 'август',
    9: 'сентябрь',
    10: 'октябрь',
    11: 'ноябрь',
    12: 'декабрь'
}


def get_date_of_change(month, keyrates):
    current_keyrate = keyrates.iloc[0]
    date_of_change = month.iloc[0]

    for k in keyrates.iloc[1:]:
        if k != current_keyrate:
            date_of_change = month.iloc[keyrates[keyrates == k].index[0]]
            return date_of_change
    return date_of_change


def get_inflation_and_keyrate() -> pd.DataFrame:
    try:
        url = 'https://www.cbr.ru/hd_base/infl/'
        df = pd.read_html(url)[0]

        keyrate_series = df.iloc[0, [0, 1]]
        keyrate_value = keyrate_series.iloc[1] / 100
        date_of_change_keyrate = get_date_of_change(month=df.iloc[:, 0], keyrates=df.iloc[:, 1])
        keyrate_month = pd.to_datetime(str(date_of_change_keyrate), format='%m.%Y').month
        keyrate_date = MONTH_NAMES_RU.get(keyrate_month, '')

        inflation = df.iloc[0, [0, 2]]
        infl = inflation.iloc[1] / 100

        month = pd.to_datetime(str(inflation.loc['Дата']), format='%m.%Y').month
        inflation_data = MONTH_NAMES_RU.get(month, '').lower()

        result_dct = pd.DataFrame(
            {
                'inflation': [f'Инфляция на {inflation_data}: {infl}% г/г'],
                'keyrate': [f'Ключевая ставка {keyrate_value}% годовых, последнее изменение: {keyrate_date}']
            }
        )
        return result_dct

    except Exception as e:
        print(f'Ошибка в {get_inflation_and_keyrate.__name__}: {e}')
