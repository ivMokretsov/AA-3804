import os
import requests
import json

# Получение токена из переменной окружения
api_token = os.getenv('AWX_API_TOKEN')

# URL API AWX
api_url = "https://awx.example.com/api/v2/jobs/"
headers = {
    "Authorization": f"Bearer {api_token}"
}

# Запрос к API для получения списка последних джобов
response = requests.get(api_url, headers=headers)
jobs_data = response.json()

# Инициализация инвентаря
inventory = {
    "_meta": {
        "hostvars": {}
    },
    "successful_hosts": {
        "hosts": []
    },
    "failed_hosts": {
        "hosts": []
    }
}

# Обработка данных о джобах
for job in jobs_data['results']:
    if job['status'] == 'successful':
        for host in job['hosts']:
            inventory["successful_hosts"]["hosts"].append(host['name'])
    elif job['status'] == 'failed':
        for host in job['hosts']:
            inventory["failed_hosts"]["hosts"].append(host['name'])

# Вывод инвентаря в формате JSON
print(json.dumps(inventory))