import subprocess
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
RSCRIPT_PATH = Path(r"C:\Program Files\R\R-4.6.0\bin\x64\Rscript.exe")

R_SCRIPT = PROJECT_DIR / "load_producer_price_index.R"
RAW_CSV = PROJECT_DIR / "data" / "fedstat_57609_raw.csv"


MONTH_ORDER = {
    "январь": 1,
    "февраль": 2,
    "март": 3,
    "апрель": 4,
    "май": 5,
    "июнь": 6,
    "июль": 7,
    "август": 8,
    "сентябрь": 9,
    "октябрь": 10,
    "ноябрь": 11,
    "декабрь": 12,
}


SECTORS = [
    "ДОБЫЧА ПОЛЕЗНЫХ ИСКОПАЕМЫХ",
    "ОБРАБАТЫВАЮЩИЕ ПРОИЗВОДСТВА",
    "ОБЕСПЕЧЕНИЕ ЭЛЕКТРИЧЕСКОЙ ЭНЕРГИЕЙ, ГАЗОМ И ПАРОМ; КОНДИЦИОНИРОВАНИЕ ВОЗДУХА",
    "ВОДОСНАБЖЕНИЕ; ВОДООТВЕДЕНИЕ, ОРГАНИЗАЦИЯ СБОРА И УТИЛИЗАЦИИ ОТХОДОВ, "
    "ДЕЯТЕЛЬНОСТЬ ПО ЛИКВИДАЦИИ ЗАГРЯЗНЕНИЙ",
]


POK_LAST_MONTH = "К предыдущему месяцу"
POK_LAST_YEAR_MONTH = (
    "Отчетный месяц к соответствующему месяцу предыдущего года"
)


def run_r_loader() -> None:
    """Download the current producer price index data from Fedstat."""
    if not RSCRIPT_PATH.is_file():
        raise FileNotFoundError(f"Не найден Rscript: {RSCRIPT_PATH}")
    if not R_SCRIPT.is_file():
        raise FileNotFoundError(f"Не найден R-скрипт: {R_SCRIPT}")

    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [str(RSCRIPT_PATH), str(R_SCRIPT)],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )

    if result.returncode != 0:
        error_details = result.stderr.strip() or result.stdout.strip()
        if "Forbidden (HTTP 403)" in error_details:
            error_details = "Fedstat отклонил автоматический запрос (HTTP 403)."
        elif "Empty reply from server" in error_details:
            error_details = "Fedstat закрыл соединение, не вернув данные."
        raise RuntimeError(
            "Выгрузка Fedstat не выполнена."
            + (f"\n{error_details}" if error_details else "")
        )

    if not RAW_CSV.is_file():
        raise FileNotFoundError(
            f"R-скрипт завершился без ошибки, но файл не создан: {RAW_CSV}"
        )

    print("Выгрузка Fedstat завершена")


def prepare_producer_price_index_data(path: str | Path) -> pd.DataFrame:
    """Read and normalize the raw Fedstat response."""
    df = pd.read_csv(path, encoding="utf-8-sig")

    df = df.rename(
        columns={
            "s_POK": "ВидПоказателя",
            "s_OKVED2": "Сектор",
            "ObsValue": "Значение",
            "PERIOD": "Месяц",
            "Time": "Год",
        }
    )

    required_cols = ["ВидПоказателя", "Сектор", "Значение", "Месяц", "Год"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Не найдены нужные колонки: {missing_cols}. "
            f"Фактические колонки: {list(df.columns)}"
        )

    df["ВидПоказателя"] = df["ВидПоказателя"].astype(str).str.strip()
    df["Сектор"] = df["Сектор"].astype(str).str.strip()
    df["Месяц"] = df["Месяц"].astype(str).str.strip().str.lower()

    df["Год"] = pd.to_numeric(df["Год"], errors="coerce")
    df["Значение"] = pd.to_numeric(
        df["Значение"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )

    df = df[
        df["Месяц"].isin(MONTH_ORDER)
        & df["Сектор"].isin(SECTORS)
        & df["Год"].notna()
    ].copy()

    if df.empty:
        raise ValueError("После фильтрации в выгрузке Fedstat не осталось данных")

    df["НомерМесяца"] = df["Месяц"].map(MONTH_ORDER)
    df["Год"] = df["Год"].astype(int)
    df["Дата"] = pd.to_datetime(
        dict(
            year=df["Год"],
            month=df["НомерМесяца"],
            day=1,
        )
    )
    df["ДатаТекст"] = df["Месяц"].str.title() + " " + df["Год"].astype(str)

    return df


def make_result_table(df: pd.DataFrame, indicator_name: str) -> pd.DataFrame:
    """Build a sector-by-month table for the latest three available months."""
    df_part = df[df["ВидПоказателя"] == indicator_name].copy()
    if df_part.empty:
        raise ValueError(f"В выгрузке нет показателя: {indicator_name}")

    last_3_dates = (
        df_part[["Дата"]]
        .drop_duplicates()
        .sort_values("Дата")
        .tail(3)["Дата"]
        .tolist()
    )
    df_part = df_part[df_part["Дата"].isin(last_3_dates)].copy()

    result = df_part.pivot_table(
        index="Сектор",
        columns="ДатаТекст",
        values="Значение",
        aggfunc="first",
    )

    date_order = (
        df_part[["Дата", "ДатаТекст"]]
        .drop_duplicates()
        .sort_values("Дата")["ДатаТекст"]
        .tolist()
    )

    return result.reindex(index=SECTORS, columns=date_order)


def get_producer_price_index_from_fedstat(path: str | Path) -> dict:
    """Transform an existing Fedstat CSV into the two result tables."""
    try:
        df = prepare_producer_price_index_data(path)

        return {
            "(мес)": make_result_table(df, POK_LAST_MONTH),
            "(год)": make_result_table(df, POK_LAST_YEAR_MONTH),
        }
    except Exception as error:
        print(f"Ошибка в get_producer_price_index_from_fedstat: {error}")
        return {}


def get_producer_price_index(
    path: str | Path = RAW_CSV,
    *,
    refresh: bool = True,
) -> dict:
    """
    Refresh producer price data via R and return tables for the workbook.

    ``refresh=False`` is useful for offline checks against an existing CSV.
    """
    if refresh:
        try:
            run_r_loader()
        except Exception as error:
            cached_path = Path(path)
            if not cached_path.is_file():
                print(f"Ошибка в get_producer_price_index: {error}")
                return {}

            print(
                "Предупреждение: не удалось обновить данные Fedstat.\n"
                f"{error}\n"
                f"Используется последняя успешная выгрузка: {cached_path}"
            )

    return get_producer_price_index_from_fedstat(path)


if __name__ == "__main__":
    result = get_producer_price_index()

    for name, table in result.items():
        print(f"\n{name}")
        print(table)
