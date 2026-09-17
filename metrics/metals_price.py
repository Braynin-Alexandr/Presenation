import pandas as pd
from datetime import datetime


metal_map = {
    'Медь': 'Cu',
    'Никель': 'Ni',
    'Алюминий': 'Al',
    'Олово': 'Sn'
}


def get_monthly_avg(df: pd.DataFrame) -> pd.Series:
    monthly_avg = df['Цена'].resample('ME').mean().round(2)
    monthly_avg.index = monthly_avg.index.date
    return monthly_avg


def get_metals_price(path: str) -> pd.DataFrame:
    try:
        xls = pd.ExcelFile(path)
        dfs = {}

        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            df.columns = ['Дата', 'Цена']
            df['Дата'] = pd.to_datetime(df['Дата'], format='%d %B %Y', errors='coerce')
            df = df.dropna(subset=['Дата'])
            df = df.set_index('Дата')
            df['Цена'] = df['Цена'].str.split().str[0].astype(float)
            dfs[sheet_name] = df

        latest_data = []
        for metal_name, df in dfs.items():
            latest_row = df.iloc[0]
            latest_date = latest_row.name
            latest_price = latest_row['Цена']
            latest_data.append({'Дата': latest_date, 'Металл': metal_name, 'Цена': latest_price})

        latest_rates_df = pd.DataFrame(latest_data)
        latest_rates_df = latest_rates_df.pivot(
            index='Дата',
            columns='Металл',
            values='Цена'
        )
        latest_rates_df = latest_rates_df.astype(float)
        latest_rates_df.index = latest_rates_df.index.date
        current_month = datetime.now().month
        monthly_data = {}

        for name, df in dfs.items():
            df = df[df.index.month != current_month]
            monthly_avg = get_monthly_avg(df)
            monthly_data[name] = monthly_avg

        monthly_df = pd.DataFrame(monthly_data)

        summary_df = pd.concat([monthly_df, latest_rates_df])

        last_row = summary_df.iloc[-1, :]
        prev_row = summary_df.iloc[-2, :]

        dynamics_series = ((last_row-prev_row) / prev_row * 100).round(2)

        dynamics_series.name = 'Динамика, %'
        summary_df = pd.concat([summary_df, pd.DataFrame(dynamics_series).T])
        summary_df = summary_df.rename(columns=metal_map).reindex(columns=metal_map.values())

        return summary_df
    except Exception as e:
        print(f'Ошибка в {get_metals_price.__name__}: {e}')
        return pd.DataFrame()
