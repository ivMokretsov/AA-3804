#!/usr/bin/env python3
import os
import sys
import requests
import json
import urllib3

# Отключаем предупреждения о небезопасном HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_inventory():
    # Получение токена из переменной окружения
    # api_token = os.getenv('AWX_API_TOKEN')
    api_token = 'nyR6ylhV85RVR1GnOU8B5rxI89GmNM'

    # ID шаблона (замените на реальный ID вашего шаблона)
    template_id = 8

    # URL API AWX для получения информации о шаблоне
    api_url = f"https://10.177.185.87/api/v2/job_templates/{template_id}/"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    # Запрос к API для получения информации о шаблоне
    response = requests.get(api_url, headers=headers, verify=False)
    template_data = response.json()

    # Проверяем, есть ли информация о последней джобе
    if "last_job" not in template_data['related']:
        return {}

    # Получаем ID последней джобы
    last_job_url = template_data['related']['last_job']
    last_job_id = last_job_url.split('/')[-2]

    # Запрос к API для получения краткой информации о хостах в последней джобе
    job_host_summaries_url = f"https://10.177.185.87/api/v2/jobs/{last_job_id}/job_host_summaries/"
    job_host_summaries_response = requests.get(job_host_summaries_url, headers=headers, verify=False)
    job_host_summaries_data = job_host_summaries_response.json()

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

    # Обрабатываем информацию о хостах
    for host_summary in job_host_summaries_data['results']:
        host_name = host_summary['summary_fields']['host']['name']
        if host_summary['failed']:
            inventory["failed_hosts"]["hosts"].append(host_name)
        else:
            inventory["successful_hosts"]["hosts"].append(host_name)

    return inventory

def main():
    # Получаем аргумент из командной строки
    if len(sys.argv) == 2 and sys.argv[1] == '--list':
        inventory = fetch_inventory()
        print(json.dumps(inventory, indent=4))
    elif len(sys.argv) == 3 and sys.argv[1] == '--host':
        # Данный сценарий предполагает работу без детальной информации о конкретных хостах
        print(json.dumps({}, indent=4))
    else:
        # Если вызов не содержит корректных аргументов, выводим пустой инвентарь
        print(json.dumps({}, indent=4))

if __name__ == "__main__":
    main()
