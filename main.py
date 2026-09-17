from pathlib import Path

import pandas as pd
from pandas import ExcelWriter

from config import METRICS

pd.set_option('future.no_silent_downcasting', True)


RESULT_FILE = Path(__file__).resolve().parent / 'results.xlsx'


def main():
    """Main function to process metrics data"""

    metric_results = {}
    for metric_info in METRICS.values():
        path = metric_info['path']
        title = metric_info['title']
        args = (path,) if path else ()
        function = metric_info['function']
        metric_result = function(*args)
        if isinstance(metric_result, dict):
            for sub_title, df in metric_result.items():
                metric_results[f"{title}{sub_title}"] = df
        else:
            metric_results[title] = metric_result
    return metric_results


def write_results(results: dict[str, pd.DataFrame], path: Path = RESULT_FILE) -> None:
    """Write all metric tables, including salary statistics, to one workbook."""
    with ExcelWriter(path) as writer:
        for sheet_name, df in results.items():
            print(sheet_name)
            df.to_excel(writer, sheet_name=sheet_name)


if __name__ == '__main__':
    results = main()
    write_results(results)
