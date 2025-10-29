import json
import os


def convert_csv_to_json(filepath):
    with open(f'{filepath}.csv', mode='r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    with open(f'{filepath}.json', mode='w', encoding='utf-8') as jsonfile:
        json.dump(list(content.split(',')), jsonfile, indent=4)

if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), '../form_data')

    convert_csv_to_json(f'{path}\\disruption_type')
    convert_csv_to_json(f'{path}\\disruption_severity')
    convert_csv_to_json(f'{path}\\duration')
    convert_csv_to_json(f'{path}\\day_of_start')
    convert_csv_to_json(f'{path}\\place_of_disruption')