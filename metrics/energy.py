import pandas as pd

n_months_need = 5
code_dct = {
    '06.20.10.110': 'Газ (руб./м³)',
    '35.13.10.004.АГ': 'Электроэнергия, (руб./кВт·ч)'
}


def get_next_row_idx(df, code: str) -> int | None:
    """returns the next index after the index of code in df"""
    matches = df[df.iloc[:, 1].str.contains(code, case=False, na=False)].index.to_list()
    if matches:
        return matches[-1] + 1
    else:
        return None


def df_from_excel(file: pd.ExcelFile, sheet_name: str, header: int) -> pd.DataFrame | None:
    """Reads an Excel sheet and extracts rows based on codes, returning a DataFrame with the extracted data."""
    try:
        df = pd.read_excel(file, sheet_name=sheet_name, header=header)
        idxs_lst = {get_next_row_idx(df, code): name for code, name in code_dct.items()}

        if None not in idxs_lst:
            list_idxs = list(idxs_lst.keys())
            df = df.iloc[list_idxs, 2:]
            df.index = df.index.map(idxs_lst)
            df_numeric = df.apply(lambda x: pd.to_numeric(x, errors='coerce'))
            df_result = (df_numeric / 1_000).round(2)
            return df_result
    except Exception as e:
        print(e)
        return None


def get_energy(path: str) -> pd.DataFrame | None:
    file = pd.ExcelFile(path)
    sheet_names = file.sheet_names
    up_to_date_sheet = sheet_names[-1]
    try:
        result_df = df_from_excel(file, up_to_date_sheet, header=3)
        if result_df is None:
            return None
        len_months_df = len(result_df.columns.to_list())

        if len_months_df < n_months_need:
            need_months = n_months_need - len_months_df
            extra_df = df_from_excel(file, sheet_names[-2], header=3)
            if extra_df is None:
                return result_df
            extra_df = extra_df.iloc[:, -need_months:]
            result_df = extra_df.join(result_df)
            result_df.columns = result_df.columns.str.capitalize()
        return result_df
    except Exception as e:
        print(f'Ошибка в {get_energy.__name__}: {e}')
        return None
