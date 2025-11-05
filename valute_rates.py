import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import numpy as np


CURRENCY_CODES = {
    'USD': 'R01235',
    'EUR': 'R01239',
    'CNY': 'R01375',
    'AED': 'R01230'
}

CURRENCY_FLAGS = {
    'USD': 'flags/usa.png',
    'EUR': 'flags/eu.png',
    'CNY': 'flags/china.png',
    'AED': 'flags/uae.png'
}

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


end_date = datetime.today()
start_date = (end_date - timedelta(days=120)).replace(day=1)
date_req1 = start_date.strftime('%d/%m/%Y')
date_req2 = end_date.strftime('%d/%m/%Y')


currency_dfs = []

for name, code in CURRENCY_CODES.items():
    url = f'https://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={date_req1}&date_req2={date_req2}&VAL_NM_RQ={code}'
    df = pd.read_xml(url, xpath='.//Record', parser='etree')
    df['date'] = pd.to_datetime(df['Date'], format='%d.%m.%Y')
    df[name] = df['Value'].str.replace(',', '.').astype(float)
    df = df[['date', name]].set_index('date')
    currency_dfs.append(df)


rates_df = pd.concat(currency_dfs, axis=1)

latest_rates = rates_df.iloc[-1, :]
latest_rates.name = latest_rates.name.strftime('%d.%m.%Y')
latest_rates_df = pd.DataFrame(latest_rates).T

monthly_avg = rates_df.resample('ME').mean().iloc[:-1, :]

monthly_avg.index = monthly_avg.index.month.map(MONTH_NAMES_RU)

summary_df = pd.concat([monthly_avg, latest_rates_df])

last_row = summary_df.iloc[-1, :]
prev_row = summary_df.iloc[-2, :]

dynamics_series = (prev_row/last_row - 1) * 100
dynamics_series.name = 'Динамика, %'

summary_df = pd.concat([summary_df, pd.DataFrame(dynamics_series).T]).round(2)
print(summary_df)


# Визуализация
fig, axes = plt.subplots(1, len(summary_df.columns), figsize=(15, 4))
fig.patch.set_facecolor("white")

for ax, currency in zip(axes, summary_df.columns):
    # Данные для мини-графика (последние 3 месяца и последний день)
    data = summary_df.loc[['Июль', 'Август', 'Сентябрь', latest_rates.name], currency]
    chronological_data = data.values
    change = summary_df.loc['Динамика, %', currency]

    # Цвета
    bg_color = "#007bff"
    text_color = "white"
    trend_symbol = "▲" if change > 0 else "▼"
    trend_color = "#00ff88" if change > 0 else "#ff6666"

    # Фон блока
    ax.set_facecolor(bg_color)
    ax.set_xlim(-0.5, len(chronological_data) - 0.5)
    ax.set_ylim(min(chronological_data) * 0.98, max(chronological_data) * 1.05)

    # Мини-график (линия тренда)
    ax.plot(range(len(chronological_data)), chronological_data, color="white", marker="o", linewidth=2)
    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)

    # --- ДОБАВЛЯЕМ ФЛАГ ---
    # ... предыдущий код ...

    # ... код добавления флага ...
    flag_path = CURRENCY_FLAGS.get(currency)
    if flag_path:
        img = Image.open(flag_path).convert("RGBA")
        img = img.resize((64, 40))
        img_arr = np.array(img)
        imagebox = OffsetImage(img_arr, zoom=1)
        ab = AnnotationBbox(
            imagebox,
            (0, 1),
            frameon=False,
            xycoords='axes fraction',
            box_alignment=(0, 1)
        )
        ax.add_artist(ab)
        # Подпись под флагом
        ax.text(
            0, 0.80,  # X, Y: чуть ниже флага
            f"RUB/{currency}",
            color=text_color,
            fontsize=13,
            weight="bold",
            transform=ax.transAxes,
            ha="left",
            va="top"
        )

    # --- ТЕКСТ ---
    current_rate = chronological_data[-1]
    ax.text(0.05, 0.70, f"{current_rate:,.2f}".replace(",", " "), color=text_color, fontsize=12, transform=ax.transAxes)
    ax.text(0.05, 0.55, f"{trend_symbol} {abs(change):.2f}%", color=trend_color, fontsize=11, transform=ax.transAxes)

    # Добавляем числа к точкам
    for i, value in enumerate(chronological_data):
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

    # Убираем рамки
    for spine in ax.spines.values():
        spine.set_visible(False)


plt.tight_layout()
plt.show()
# plt.savefig('plot.png')
