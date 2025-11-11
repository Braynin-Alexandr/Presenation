import pandas as pd

#Делаем выгрузку с сайта https://fedstat.ru/indicator/57824
#Предварительно отфильтровав данные на сайте, выбираем: "Российская Федерация без учета новых субъектов (с 01.01.2023)"

path = r"C:\Users\brayn\Downloads\data (9).xls"
df = pd.read_excel(path, header=3)
df = df.iloc[:, 1:].rename(columns={"Unnamed: 1": "Месяц"})
incorrect_months = df["Месяц"].str.contains("-", na=False)
df = df[~incorrect_months].set_index('Месяц')
df = df.iloc[:, -3:]

mean_series = df.mean(axis=0, skipna=True).round(2)
mean_series.index.name = 'Год'
mean_series.name = 'ЗП'

result = pd.DataFrame(mean_series).reset_index()
print(result)
