import pandas as pd
from datetime import datetime


#источник данных:
# https://monetka.com.ru/quotes-metal/?m=Nickel&v=kg
# https://monetka.com.ru/quotes-metal/?m=Copper&v=kg
# https://monetka.com.ru/quotes-metal/?m=Aluminium&v=kg
# https://monetka.com.ru/quotes-metal/?m=Tin&v=kg

# Получить данные с каждой страницы (выше) и сохранить их в Excel
# Назвать листы Excel: 'Медь', 'Алюминий', 'Олово', 'Никель'
# На каждом листе должны быть две колонки: Дата и Цена


path = r"C:\Users\brayn\Desktop\Металлы.xlsx" #указать путь до файла
xls = pd.ExcelFile(path)
dfs = {}


for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
    dfs[sheet_name] = df


for name, df in dfs.items():
    df.columns = ['Дата', 'Цена']
    df['Дата'] = pd.to_datetime(df['Дата'], format='%d %B %Y').dt.date
    df['Цена'] = df['Цена'].str.split().str[0].astype(float)


latest_rates = {metall_name: df.iloc[0, :] for metall_name, df in dfs.items()}
latest_rates_df = pd.DataFrame(latest_rates).T.round(2)
latest_rates_df.reset_index(inplace=True)
latest_rates_df = latest_rates_df.pivot_table(index='Дата', columns='index', values='Цена')
latest_rates_df.index.name = 'Дата'
latest_rates_df = latest_rates_df.astype(float)


def get_monthly_avg(df: pd.DataFrame) -> pd.Series:
    monthly_avg = df['Цена'].resample('ME').mean().round(2)
    monthly_avg.index = monthly_avg.index.date
    return monthly_avg


current_month = datetime.now().month
monthly_data = {}

for name, df in dfs.items():
    df['Дата'] = pd.to_datetime(df['Дата'], format='%Y-%m-%d')
    df = df.set_index('Дата')
    df = df[df.index.month != current_month]
    monthly_avg = get_monthly_avg(df)
    monthly_data[name] = monthly_avg #.map(lambda x: round(x, 2))

monthly_df = pd.DataFrame(monthly_data)

summary_df = pd.concat([monthly_df, latest_rates_df])

last_row = summary_df.iloc[-1, :]
prev_row = summary_df.iloc[-2, :]

dynamics_series = ((last_row-prev_row) / prev_row * 100).round(2)
dynamics_series.name = 'Динамика, %'
summary_df = pd.concat([summary_df, pd.DataFrame(dynamics_series).T])
print(summary_df)
