from pathlib import Path
import pandas as pd


PROJECT_DIR = Path(__file__).parent
RAW_CSV = PROJECT_DIR / "data" / "fedstat_57824_raw.csv"

regions = {
    'Центральный федеральный округ': 'ЦФО',
    'Северо-Западный федеральный округ': 'СЗФО',
    'Южный федеральный округ': 'ЮФО',
    'Северо-Кавказский федеральный округ': 'СКФО',
    'Приволжский федеральный округ': 'ПФО',
    'Уральский федеральный округ': 'УФО',
    'Сибирский федеральный округ': 'СФО',
    'Дальневосточный федеральный округ': 'ДВФО'
}

MONTH_ORDER = {
    'январь': 1,
    'февраль': 2,
    'март': 3,
    'апрель': 4,
    'май': 5,
    'июнь': 6,
    'июль': 7,
    'август': 8,
    'сентябрь': 9,
    'октябрь': 10,
    'ноябрь': 11,
    'декабрь': 12
}


def find_column(df: pd.DataFrame, possible_names: list[str]) -> str:
    for name in possible_names:
        if name in df.columns:
            return name

    raise ValueError(
        f"Не найдена колонка. Ищу одно из: {possible_names}. "
        f"Фактические колонки: {list(df.columns)}"
    )


def prepare_fedstat_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    df = df.rename(columns={
        "s_OKATO": "Округ",
        "ObsValue": "ЗП",
        "PERIOD": "Период",
        "Time": "Год"
    })

    required_cols = ["Округ", "Год", "Период", "ЗП"]

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Не найдены нужные колонки: {missing_cols}. "
            f"Фактические колонки: {list(df.columns)}"
        )

    df["Округ"] = df["Округ"].astype(str).str.strip()
    df["Период"] = df["Период"].astype(str).str.strip()
    df["Год"] = pd.to_numeric(df["Год"], errors="coerce")
    df["ЗП"] = pd.to_numeric(df["ЗП"], errors="coerce")

    df = df[df["Период"].isin(MONTH_ORDER.keys())].copy()

    df_wide = (
        df.pivot_table(
            index=["Округ", "Год"],
            columns="Период",
            values="ЗП",
            aggfunc="first"
        )
        .reset_index()
    )

    df_wide.columns.name = None

    return df_wide


def get_salary_statistics_from_fedstat(path: Path) -> dict:
    try:
        df = prepare_fedstat_data(path)

        month_cols = [c for c in MONTH_ORDER if c in df.columns]

        df_regions = df[df["Округ"].isin(regions.keys())].copy()
        df_regions = df_regions[df_regions[month_cols].notna().any(axis=1)]

        latest_year = int(df_regions["Год"].max())
        df_regions = df_regions[df_regions["Год"] == latest_year].copy()

        df_regions["ЗП"] = df_regions[month_cols].mean(axis=1).round(0)

        df_regions_result = df_regions[["Округ", "ЗП"]].copy()
        df_regions_result["Округ"] = df_regions_result["Округ"].map(regions)

        # ---------------------------------------------------
        # 2. По годам: РФ, среднее по каждому году
        # ---------------------------------------------------
        region_russia = "Российская Федерация без учета новых субъектов (с 01.01.2023)"
        df_russia = df[df["Округ"] == region_russia].copy()

        df_russia_result = (
            df_russia[["Год"] + month_cols]
            .set_index("Год")
            .mean(axis=1)
            .round(0)
            .rename("ЗП")
            .reset_index()
        )

        # ---------------------------------------------------
        # 3. Последние 6 месяцев: корректно через дату
        # ---------------------------------------------------
        df_ru_months = df_russia[["Год"] + month_cols].copy()

        df_ru_months_long = df_ru_months.melt(
            id_vars="Год",
            value_vars=month_cols,
            var_name="Месяц",
            value_name="ЗП"
        )

        df_ru_months_long = df_ru_months_long.dropna(subset=["ЗП"]).copy()
        df_ru_months_long["НомерМесяца"] = df_ru_months_long["Месяц"].map(MONTH_ORDER)

        df_ru_months_long["Дата"] = pd.to_datetime(
            dict(
                year=df_ru_months_long["Год"].astype(int),
                month=df_ru_months_long["НомерМесяца"],
                day=1
            )
        )

        last_6_months = (
            df_ru_months_long[["Дата", "Год", "Месяц", "ЗП"]]
            .sort_values("Дата")
            .tail(6)
            .reset_index(drop=True)
        )

        return {
            "по округам": df_regions_result,
            "по годам": df_russia_result,
            "последние 6 мес": last_6_months
        }

    except Exception as e:
        print(f"Ошибка в get_salary_statistics_from_fedstat: {e}")
        return {}


if __name__ == "__main__":
    result = get_salary_statistics_from_fedstat(RAW_CSV)

    for name, table in result.items():
        print(f"\n{name}")
        print(table)
