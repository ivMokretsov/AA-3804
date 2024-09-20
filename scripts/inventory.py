#!/usr/bin/env python3
import os
import sys
import requests
import json
import urllib3
import configparser

# Отключаем предупреждения о небезопасном HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Вынесенные переменные
api_token = os.getenv('AWX_API_TOKEN')  # Токен берется из переменной окружения
# template_id = os.getenv('AWX_TEMPLATE_ID')  # Template ID также может быть передано через переменную окружения
# Путь к локальному INI-файлу
inventory_file_path = os.path.join(os.path.dirname(__file__), 'local_inventory.ini')


def extract_ansible_vars(variables):
    """Извлечение ansible_host и ansible_user из переменных"""
    ansible_host = None
    ansible_user = None

    try:
        var_data = json.loads(variables)
        ansible_host = var_data.get('ansible_host', None)
        ansible_user = var_data.get('ansible_user', None)
    except json.JSONDecodeError:
        # Если строка не в формате JSON, пробуем разобрать как строки
        for line in variables.splitlines():
            if line.startswith("ansible_host:"):
                ansible_host = line.split(":")[1].strip()
            if line.startswith("ansible_user:"):
                ansible_user = line.split(":")[1].strip()

    return ansible_host, ansible_user


def fetch_host_details(host_id, api_token):
    """Получение ansible_host и ansible_user для конкретного хоста"""
    host_url = f"https://10.177.185.87/api/v2/hosts/{host_id}/"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    response = requests.get(host_url, headers=headers, verify=False)
    host_data = response.json()

    variables = host_data.get('variables', '')
    ansible_host, ansible_user = extract_ansible_vars(variables)

    return ansible_host, ansible_user


def load_inventory_from_file(file_path):
    """Загрузка инвентаря из локального INI-файла с хостами и переменными"""
    inventory = {
        "_meta": {
            "hostvars": {}
        },
        "all": {  # Все хосты будут находиться в одной группе
            "hosts": []
        }
    }

    # Открываем INI-файл построчно
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith('['):  # Пропускаем пустые строки и заголовки секций
                continue
            
            # Разбиваем строку на хост и переменные
            parts = line.split()
            host_name = parts[0]
            inventory["all"]["hosts"].append(host_name)
            inventory["_meta"]["hostvars"][host_name] = {}

            # Обрабатываем переменные для хоста
            for var in parts[1:]:
                if "=" in var:
                    key, value = var.split("=", 1)
                    inventory["_meta"]["hostvars"][host_name][key] = value

    return inventory

def fetch_inventory_from_awx(api_token, template_id):
    """Получение информации о последней джобе и хостах с неудачным завершением"""
    api_url = f"https://10.177.185.87/api/v2/job_templates/{template_id}/"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }


    response = requests.get(api_url, headers=headers, verify=False)
    template_data = response.json()

    if "last_job" not in template_data['related']:
        return load_inventory_from_file(inventory_file_path)

    last_job_url = template_data['related']['last_job']
    last_job_id = last_job_url.split('/')[-2]

    job_host_summaries_url = f"https://10.177.185.87/api/v2/jobs/{last_job_id}/job_host_summaries/"
    job_host_summaries_response = requests.get(job_host_summaries_url, headers=headers, verify=False)
    job_host_summaries_data = job_host_summaries_response.json()

    inventory = {
        "_meta": {
            "hostvars": {}
        },
        "all": {  # Все хосты будут находиться в одной группе "all"
            "hosts": []
        }
    }

    for host_summary in job_host_summaries_data['results']:
        if host_summary['failed']:  # Учитываем только неудачно завершившиеся хосты
            host_name = host_summary['summary_fields']['host']['name']
            host_id = host_summary['summary_fields']['host']['id']
            ansible_host, ansible_user = fetch_host_details(host_id, api_token)

            inventory["_meta"]["hostvars"][host_name] = {
                "ansible_host": ansible_host,
                "ansible_user": ansible_user
            }

            inventory["all"]["hosts"].append(host_name)

    return inventory


def fetch_inventory():
    """Формирование инвентаря в зависимости от состояния"""
    if not template_id:
        return load_inventory_from_file(inventory_file_path)
    else:
        return fetch_inventory_from_awx(api_token, template_id)


def main():
    if len(sys.argv) == 2 and sys.argv[1] == '--list':
        inventory = fetch_inventory()
        print(json.dumps(inventory, indent=4))
    elif len(sys.argv) == 3 and sys.argv[1] == '--host':
        print(json.dumps({}, indent=4))
    else:
        print(json.dumps({}, indent=4))


if __name__ == "__main__":
    main()
