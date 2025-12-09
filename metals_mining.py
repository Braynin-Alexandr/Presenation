import requests
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import date
from dateutil.relativedelta import relativedelta
load_dotenv()


BASE_URL = "https://client.metalsmining.ru/api/v1"
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

today = date.today()
today_str = today.strftime("%Y-%m-%d")

previous_months = today - relativedelta(months=4)
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

    print("Токен успешно получен.")
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
    data_months = [d.get('text').title() for d in data.get('columns')[-3:]]
    data_prices = [[p.get('text') for p in d[-3:]] for d in data.get('data')]
    data_names = [d[3].get('text').replace('с НДС', 'без НДС') for d in data.get('data')]
    data_price_float = []

    for prices_list in data_prices:
        prices_list_formatted = []
        for price in prices_list:
            try:
                prices_list_formatted.append(float(price) / 1.2)
            except (ValueError, TypeError):
                prices_list_formatted.append(None)
        data_price_float.append(prices_list_formatted)

    try:
        df = pd.DataFrame(data_price_float, columns=data_months, index=data_names).T
    except Exception as e:
        print("Ошибка при создании DataFrame:", e)
        df = pd.DataFrame()
    return df


token = get_token(EMAIL, PASSWORD)
session = new_session(token)


data_pipes = export_stats(session, payload_pipes)
data_raw_materials = export_stats(session, payload_raw_materials)

df_pipes = extract_data(data_pipes)
df_raw_materials = extract_data(data_raw_materials)

with pd.ExcelWriter("metalsmining.xlsx") as writer:
    df_pipes.to_excel(writer, sheet_name='Трубы')
    df_raw_materials.to_excel(writer, sheet_name='Сырье')

print("Данные успешно сохранены в файл metalsmining.xlsx")
