library(fedstatAPIr)

if (packageVersion("fedstatAPIr") < "1.1.0") {
  stop("Для текущего API Fedstat требуется fedstatAPIr версии 1.1.0 или новее")
}

fedstat_headers <- httr::add_headers(
  .headers = c(
    "user-agent" = paste(
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
      "AppleWebKit/537.36 (KHTML, like Gecko)",
      "Chrome/130.0.0.0 Safari/537.36"
    ),
    "accept-language" = "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
  )
)

dir.create("data", showWarnings = FALSE)

data <- fedstat_data_load_with_filters(
  indicator_id = "57609",
  fedstat_headers,
  filters = list(
    "Год" = as.character(2022:2026),

    "Период" = c(
      "январь", "февраль", "март", "апрель", "май", "июнь",
      "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"
    ),

    "Каналы реализации" = "Внутренний рынок",

    "Виды показателя" = c(
      "К предыдущему месяцу",
      "Отчетный месяц к соответствующему месяцу предыдущего года"
    ),

    "Классификатор видов экономической деятельности (ОКВЭД2)" = c(
      "ДОБЫЧА ПОЛЕЗНЫХ ИСКОПАЕМЫХ",
      "ОБРАБАТЫВАЮЩИЕ ПРОИЗВОДСТВА",
      paste0(
        "ОБЕСПЕЧЕНИЕ ЭЛЕКТРИЧЕСКОЙ ЭНЕРГИЕЙ, ГАЗОМ И ПАРОМ; ",
        "КОНДИЦИОНИРОВАНИЕ ВОЗДУХА"
      ),
      paste0(
        "ВОДОСНАБЖЕНИЕ; ВОДООТВЕДЕНИЕ, ОРГАНИЗАЦИЯ СБОРА И ",
        "УТИЛИЗАЦИИ ОТХОДОВ, ДЕЯТЕЛЬНОСТЬ ПО ЛИКВИДАЦИИ ЗАГРЯЗНЕНИЙ"
      )
    ),

    "Классификатор объектов административно-территориального деления (ОКАТО)" =
      "Российская Федерация без учета новых субъектов (с 01.01.2023)"
  ),
  timeout_seconds = 300,
  retry_max_times = 5
)

write.csv(
  data,
  "data/fedstat_57609_raw.csv",
  row.names = FALSE,
  fileEncoding = "UTF-8"
)
