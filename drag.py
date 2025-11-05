import matplotlib.pyplot as plt
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


def get_monthly_avg(df: pd.DataFrame, metall_name: str) -> pd.Series:
    metall_df = df[df['Драгоценный металл'] == metall_name]
    return metall_df['Цена'].resample('ME').mean()


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
print(summary_df)


# --- НАСТРОЙКИ ГРАФИКА ---
fig, axes = plt.subplots(1, len(summary_df.columns), figsize=(15, 4))
fig.patch.set_facecolor("white")

last_date_str = summary_df.index[-2]

for ax, metal in zip(axes, summary_df.columns):
    # Данные для мини-графика
    data = summary_df.loc[['Июль', 'Август', 'Сентябрь', last_date_str], metal]
    change = summary_df.loc['Динамика, %', metal]

    # Цвета
    bg_color = "#007bff"
    text_color = "white"
    trend_symbol = "▲" if change > 0 else "▼"
    trend_color = "#00ff88" if change > 0 else "#ff6666"

    # Фон блока
    ax.set_facecolor(bg_color)
    ax.set_xlim(-0.5, len(data) - 0.5)
    ax.set_ylim(min(data) * 0.98, max(data) * 1.05)

    # Мини-график (линия тренда)
    ax.plot(range(len(data)), data.values, color="white", marker="o", linewidth=2)
    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)

    # --- ТЕКСТ ---
    current_price = data.iloc[-1]

    # Название металла
    ax.text(0.05, 0.85, metal, color=text_color, fontsize=12, weight="bold", transform=ax.transAxes)
    # Текущий курс
    ax.text(0.05, 0.70, f"{current_price:,.2f}".replace(",", " "), color=text_color, fontsize=12, transform=ax.transAxes)
    # Динамика
    ax.text(0.05, 0.55, f"{trend_symbol} {abs(change):.2f}%", color=trend_color, fontsize=11, transform=ax.transAxes)

    # Добавляем числа к точкам
    for i, value in enumerate(data.values):
        ax.annotate(
            f"{value:.2f}",
            (i, value),
            textcoords="offset points",
            xytext=(12, 0),
            ha='left',
            va='center',
            color="white",
            fontsize=9,
            weight="bold"
        )

    for spine in ax.spines.values():
        spine.set_visible(False)

plt.tight_layout()
plt.show()
