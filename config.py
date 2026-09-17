from pathlib import Path
from metrics.currency_rate import get_currency_rate
from metrics.energy import get_energy
from metrics.index_industrial_production import get_index_industrial_production
from metrics.metals_price import get_metals_price
from metrics.pipe_and_raw_material_prices import get_metals_mining
from metrics.precious_metals_price import get_precious_metals_price
from metrics.inflation_and_keyrate import get_inflation_and_keyrate
from metrics.producer_price_index import get_producer_price_index
from metrics.salary_statistics import get_salary_statistics_from_fedstat


BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / 'source_data'


METRICS = {

    'precious_metals_price': {
        'title': 'Драгоценные металлы',
        'path': None,
        'function': get_precious_metals_price,
        'source': None,
        'instructions': 'Достаёт данные по API, работает c выкл. VPN'
    },

    'metals_price': {
        'title': 'Металлы',
        'path': SOURCE_DIR / 'Металлы.xlsx',
        'function': get_metals_price,
        'source': {
            'Nickel': 'https://monetka.com.ru/quotes-metal/?m=Nickel&v=kg',
            'Copper': 'https://monetka.com.ru/quotes-metal/?m=Copper&v=kg',
            'Aluminium': 'https://monetka.com.ru/quotes-metal/?m=Aluminium&v=kg',
            'Tin': 'https://monetka.com.ru/quotes-metal/?m=Tin&v=kg'
                   },
        'instructions': """  
                            С помощью prepare_metals_prices.py можно автоматически получить данные с указанных url
                            с вкл. VPN. Он поместит полученные данные в папку source_data
                            ----
                            Или вручную получить данные с каждой url (выше) и сохранить их в Excel-файле.
                            Excel-файле поместить в папку source_data под именем "Металлы.xlsx" 
                            Назвать листы файла: 'Медь', 'Алюминий', 'Олово', 'Никель'
                            На каждом листе должны быть две колонки с датой и ценой; заголовки не нужны
                        """
    },

    'currency_rate': {
        'title': 'Курсы валют',
        'path': None,
        'function': get_currency_rate,
        'source': None,
        'instructions': 'Достаёт данные по API, работает без VPN'
    },

    'inflation and keyrate': {
        'title': 'Инфляция и ключевая ставка',
        'path': None,
        'function': get_inflation_and_keyrate,
        'source': 'https://www.cbr.ru/hd_base/infl/',
        'instructions': 'Достаёт данные с сайта, работает без VPN'

    },

    'Инд цен производ.': {
            'title': 'Индекс цен производителей',
            'path': BASE_DIR / 'metrics' / 'data' / 'fedstat_57609_raw.csv',
            'function': get_producer_price_index,
            'source': 'https://fedstat.ru/indicator/57609',
            'instructions': 'Данные автоматически загружаются с Fedstat через R-пакет fedstatAPIr'
        },

    'industrial_production_index': {
        'title': 'Индекс промышленн. произв-ва',
        'path': SOURCE_DIR / 'Индекс промышленного производства.xlsx',
        'function': get_index_industrial_production,
        'source': 'https://www.rosstat.gov.ru/enterprise_industrial',
        'instructions': """
                            В разделе "Индексы производства" и подразделе "Данные по ОКВЭД2 (КДЕС Ред.2) (базисный 2018 год)" 
                            скачиваем файл "Индексы производства по отдельным видам экономической деятельности по субъектам Российской Федерации"
                            Вытаскиваем информацию из листов 1,2,3.
                            Во всех трех страницах ищем первую строку "Российская Федерация" и берем крайнее правое значение
                        """
    },

    'salary_statistics': {
        'title': 'Зарплаты ',
        'path': BASE_DIR / 'metrics' / 'data' / 'fedstat_57824_raw.csv',
        'function': get_salary_statistics_from_fedstat,
        'source': 'https://fedstat.ru/indicator/57824',
        'instructions': """
                            Транспонируем.
                            Делаем выгрузку с сайта, предварительно отфильтровав данные на сайте, выбираем:
                            Российская Федерация без учета новых субъектов (с 01.01.2023),
                            Центральный федеральный округ,
                            Северо-Западный федеральный округ,
                            Южный федеральный округ, 
                            Северо-Кавказский федеральный округ,
                            Приволжский федеральный округ, 
                            Уральский федеральный округ,
                            Сибирский федеральный округ,
                            Дальневосточный федеральный округ
                            или 
                            просто выбираем все регионы.
                        """
    },

    'energy_price_trend': {
        'title': 'Динамка цен на энергию',
        'path': SOURCE_DIR / 'Динамка цен на энергию.xlsx',
        'function': get_energy,
        'source': 'https://www.rosstat.gov.ru/statistics/price',
        'instructions': """
                            В разделе "Цены производителей" скачиваем файл 'Средние цены производителей промышленных товаров (услуг) с 1998 г.'
'
                            Выбираем на 9 листе следующие позици:
                            Газ горючий природный (газ естественный), тыс. м3 
                            Электроэнергия, отпущенная промышленным потребителям по регулируемым тарифам, МВт.ч
                        """
    },

    'pipe_and_raw_material_prices': {
        'title': 'Динамка цен на ',
        'path': None,
        'function': get_metals_mining,
        'source': None,
        'instructions': 'Достаёт данные по API. Логин и пароль аккаунта указать в .env файле'
    }
}
