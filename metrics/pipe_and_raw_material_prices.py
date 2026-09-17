import requests
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import date
from dateutil.relativedelta import relativedelta
from utils.convert_carrency import convert_into_rub, get_currency
from utils.set_locale import set_rus_locale, set_eng_locale

load_dotenv()


NAMES_MAP = {
    'Сварные трубы ГОСТ 10704-91/10705-80; D219х6мм ; ст.20, CPT Центральный регион, руб./т, с НДС': 'Сварные ОН, D219x6мм; ст.20',
    'Сварные трубы ГОСТ 10704-91/10705-80; D159х8мм; сталь 20, CPT Уральский регион, руб./т, с НДС': 'НГП Св, D159x8мм; сталь 20',
    'Трубы большого диаметра ГОСТ 20295 - 85; D530-1220; марка стали 17Г1С-У, CPT Центральный ФО, руб./т с НДС': 'ТБД, D530-1020; сталь 17Г1С-У',
    'Бесшовные трубы ГОСТ 8732-78; D219х8мм; сталь 09Г2С, CPT Уральский регион, руб./т, с НДС': 'НГП Бш D219x8мм; сталь 09Г2С',

    '3А, FOB РФ Черное море, $/т': 'Лом 3А, руб./т. без НДС',
    'Россия, FCA руб./т, без НДС': 'Чугун, руб./т. без НДС',
    '150-250 мм, ст. рядовая, FOB Черное море, $/т': 'Сляб, руб./т. без НДС',
    'FOB РФ Черное море, $/т': 'Квадрат, руб./т. без НДС',
}


BASE_URL = "https://client.metalsmining.ru/api/v1"
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

today = date.today()
today_str = today.strftime("%Y-%m-%d")

previous_months = today - relativedelta(months=5)
previous_months_str = previous_months.strftime("%Y-%m-%d")

payload_pipes = {
    "base_id": 1,
    "catalog_id": [697761, 697758, 695805, 697759],
    "date_from": previous_months_str,
    "date_to": today_str,
    "display": "average",
    "hide_null": False,
    "output": "screen",
    "periodicity": "month",
    "show_output": "horizontal",
    "truncate": 1
}

payload_raw_materials = {
    "base_id": 1,
    "catalog_id": [587742, 587586, 587614, 587618],
    "date_from": previous_months_str,
    "date_to": today_str,
    "display": "average",
    "hide_null": False,
    "output": "screen",
    "periodicity": "month",
    "show_output": "horizontal",
    "truncate": 1
}


def get_token(email: str, password: str) -> str:
    url = f"{BASE_URL}/auth/login"
    payload = {
        "email": email,
        "password": password
    }
    r = requests.post(url, json=payload)
    r.raise_for_status()
    new_token = r.json().get('token')
    if not new_token:
        raise ValueError("Не удалось получить токен. Ответ: " + str(r.json()))
    return new_token


def new_session(token: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    })
    return session


def export_stats(session: requests.Session, payload: dict) -> dict:
    url = f"{BASE_URL}/export.p"
    r = session.post(url, json=payload)
    r.raise_for_status()
    return r.json()


def extract_data(data: dict) -> pd.DataFrame:
    data_months = [d.get('text').title() for d in data.get('columns')[-5:]]
    data_prices = [[p.get('text') for p in d[-5:]] for d in data.get('data')]
    data_names = [d[3].get('text') for d in data.get('data')]

    data_price_float = []
    for name, prices_list in zip(data_names, data_prices):
        prices_list_formatted = []
        for i, price in enumerate(prices_list):
            year_tax = data_months[i].split('.')[1]
            try:
                if 'с ндс' in name.lower():
                    tax = 1.2 if year_tax == '2025' else 1.22
                    prices_list_formatted.append(float(price) / tax)
                else:
                    prices_list_formatted.append(float(price))
            except (ValueError, TypeError):
                prices_list_formatted.append(None)
        data_price_float.append(prices_list_formatted)

    try:

        filtered = [
            (name, prices)
            for name, prices in zip(data_names, data_price_float)
            if isinstance(name, str) and name.strip() and any(p is not None for p in prices)
        ]

        if filtered:
            data_names, data_price_float = zip(*filtered)
        else:
            data_names, data_price_float = [], []

        df = pd.DataFrame(data_price_float, columns=data_months, index=data_names).T
        df = df.dropna(how='all')
        df.index = pd.to_datetime(df.index, format='%b.%Y')
        df.index = df.index.month_name(locale='Russian') + ' ' + df.index.year.astype('str')
        df.rename(columns=NAMES_MAP, inplace=True)
    except Exception as e:
        print("Ошибка при создании DataFrame:", e)
        df = pd.DataFrame()
        df.rename(columns=NAMES_MAP, inplace=True)
    return df


def get_metals_mining() -> dict:
    try:
        set_rus_locale()

        token = get_token(EMAIL, PASSWORD)
        session = new_session(token)

        data_pipes = export_stats(session, payload_pipes)
        data_raw_materials = export_stats(session, payload_raw_materials)

        df_pipes = extract_data(data_pipes)
        df_raw_materials = extract_data(data_raw_materials)

        cols_convert = [
            'Квадрат, руб./т. без НДС',
            'Лом 3А, руб./т. без НДС',
            'Сляб, руб./т. без НДС'
        ]
        usd_curr = get_currency('USD')
        df_raw_materials = convert_into_rub(
            df_raw_materials,
            columns=cols_convert,
            currency=usd_curr
        )

        return {
            'трубы': df_pipes,
            'сырье': df_raw_materials
        }
    except Exception as e:
        print(f'Ошибка в {get_metals_mining.__name__}: {e}')
        return {}
    finally:
        set_eng_locale()


if __name__ == '__main__':
    results = get_metals_mining()
    with pd.ExcelWriter('mmi.xlsx') as writer:
        for sheet_name, df in results.items():
            df.to_excel(writer, sheet_name=sheet_name)
