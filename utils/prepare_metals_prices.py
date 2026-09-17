import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = BASE_DIR / 'source_data'

excel_path = SOURCE_DIR / 'Металлы.xlsx'

links = {'Никель': 'https://monetka.com.ru/quotes-metal/?m=Nickel&v=kg',
         'Медь': 'https://monetka.com.ru/quotes-metal/?m=Copper&v=kg',
         'Алюминий': 'https://monetka.com.ru/quotes-metal/?m=Aluminium&v=kg',
         'Олово': 'https://monetka.com.ru/quotes-metal/?m=Tin&v=kg'
         }

#Попробовать с VPN и без
try:
    with pd.ExcelWriter(excel_path) as writer:
        for metal, base_url in links.items():
            dfs = []
            for suffix in ['', '&nbl=1']:
                url = base_url + suffix
                df = pd.read_html(url, header=0)[1]
                df = df.iloc[1:, :2]
                dfs.append(df)
            result = pd.concat(dfs, ignore_index=True)
            result.to_excel(writer, sheet_name=metal, index=False, header=False)
    print('Файл успешно создан: Металлы.xlsx')
except Exception as e:
    print('Не удалось получить данные по металлам. Ошибка:', e)
