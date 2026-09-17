import sys
import locale


def set_rus_locale():
    locale.setlocale(locale.LC_ALL, 'rus_rus' if sys.platform == 'win32' else 'ru_RU.UTF-8')


def set_eng_locale():
    locale.setlocale(locale.LC_TIME, 'C')
