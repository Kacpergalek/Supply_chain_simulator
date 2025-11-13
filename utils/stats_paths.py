import os 
from datetime import datetime

def get_newest_stats_path():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(path, "saved_statistics")
    files = [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))]
    if not files:
        raise FileNotFoundError("Files do not exist.")

    dt_now = datetime.now()

    min_time = float("inf")
    full_path = ""
    for file in files:
        try:
            str_time = file[6:26]
            file_dt = datetime.strptime(str_time, "%d_%m_%Y__%H_%M_%S")
        except:
            # pominięcie plików z innym formatem 
            continue
        diff = abs((dt_now - file_dt).total_seconds())
        if min_time > diff:
            min_time = diff
            full_path = os.path.join(path, file)
    if full_path == "":
        raise FileNotFoundError("No data with correct file names.")
    return full_path


def get_old_csvs(days_ago=5):
    seconds_ago = days_ago * 24 * 60 * 60
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(path, "saved_statistics")
    files = [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))]
    if not files:
        raise FileNotFoundError("Files do not exist.")

    dt_now = datetime.now()

    full_paths = []
    for file in files:
        try:
            str_time = file[6:26]
            file_dt = datetime.strptime(str_time, "%d_%m_%Y__%H_%M_%S")
        except:
            # pominięcie plików z innym formatem 
            continue
        diff = abs((dt_now - file_dt).total_seconds())
        if diff >= seconds_ago:
            full_path = os.path.join(path, file)
            full_paths.append(full_path)
    return full_paths