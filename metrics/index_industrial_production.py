from io import BytesIO
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


PAGE_URL = "https://www.rosstat.gov.ru/enterprise_industrial"
FILE_PREFIX = "ind_sub_2023" #УКАЗАТЬ ВУРЧНУЮ


def find_excel_url(page_url: str) -> str:
    response = requests.get(page_url, timeout=60, verify=False)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for link in soup.select("a[href]"):
        file_url = urljoin(response.url, link["href"])
        file_name = urlparse(file_url).path.rsplit("/", 1)[-1].lower()

        if file_name.startswith(FILE_PREFIX) and file_name.endswith(".xlsx"):
            return file_url

    raise RuntimeError(
        f"На странице Росстата не найден XLSX-файл с префиксом {FILE_PREFIX!r}"
    )


def download_excel_file(url: str) -> BytesIO:
    response = requests.get(url, timeout=60, verify=False)
    response.raise_for_status()
    return BytesIO(response.content)


def get_index_industrial_production(
    excel_source: str | BytesIO,
) -> pd.DataFrame | None:
    metrics = {
        1: "в % к соответствующему месяцу предыдущего года",
        2: "в % к соответствующему периоду предыдущего года",
        3: "в % к предыдущему месяцу",
    }

    try:
        sheets = pd.read_excel(excel_source, sheet_name=list(metrics), header=4)
        results = []

        for sheet_num, metric_name in metrics.items():
            sheet = sheets.get(sheet_num)
            if sheet is None or sheet.empty:
                continue

            value = sheet.iat[0, -1]
            column_name = str(sheet.columns[-1]).strip()
            period = "".join(
                character for character in column_name if not character.isdigit()
            ).strip()

            results.append((f"{metric_name} ({period})", value))

        if not results:
            return None

        return pd.DataFrame(
            results,
            columns=["Период", "Показатель"],
        ).set_index("Период")
    except Exception as error:
        print(f"Ошибка в {get_index_industrial_production.__name__}: {error}")
        return None


def load_rosstat_data() -> pd.DataFrame | None:
    file_url = find_excel_url(PAGE_URL)
    excel_data = download_excel_file(file_url)
    return get_index_industrial_production(excel_data)
