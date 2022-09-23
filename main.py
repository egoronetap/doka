import json
import datetime
import time

import requests
import schedule as schedule

import sqlite3

print('Script is working...')

SERVER = 'https://ofd.ru/api/Authorization/CreateAuthToken'
ABOUT = 'https://ofd.ru/api/integration/v1/inn/5027242359/kkt/0005861087048356/receipts'

count_of_data = 0


def get_token():
    data_for_log = {
        'Login': '89166919800',
        'Password': 'Ghjcnjgfhjkm890!@#'
    }

    req = requests.post(SERVER, json=data_for_log)

    token = req.json()['AuthToken']

    return token


def get_info():
    url = 'https://ofd.ru/api/integration/v1/inn/5027242359/kkt/0005861087048356/receipts'

    data_for_info = {
        'dateFrom': str(datetime.datetime.now()),
        'dateTo': str(datetime.datetime.now()),
        'AuthToken': get_token()
    }

    req = requests.get(url, params=data_for_info)

    return req.json()


def to_json():
    with open('file.json', mode='w') as file:
        json.dump(get_info(), file, indent=4)


def main():
    global count_of_data

    info = get_info()
    to_json()

    if count_of_data < len(info['Data']):
        print('Count of data: ', count_of_data)
        print('Len info: ', len(info['Data']))

        cn = sqlite3.connect('db/database.db')
        cur = cn.cursor()

        results = cur.execute('''SELECT * FROM bills''').fetchall()

        for check in info['Data'][:len(info['Data']) - count_of_data:]:
            print(check['ReceiptNumber'])

            out_of_date = []
            list_of_ids = []

            for bill_id in results:

                if datetime.datetime.now() - datetime.timedelta(hours=1) >\
                        datetime.datetime.strptime(bill_id[2], '%Y-%m-%d %H:%M:%S.%f'):
                    out_of_date.append(bill_id[1])
                list_of_ids.append(bill_id[1])

            if check['Id'] not in list_of_ids:
                cur.execute('''INSERT INTO bills (bill_id, bill_date) VALUES (?,?)''', [check['Id'],
                                                                                        datetime.datetime.now()])

            for bill in out_of_date:
                cur.execute(f'''DELETE FROM bills WHERE bill_id = ?''', [bill])

        cn.commit()
        cn.close()

        print(results)

        count_of_data = len(info['Data'])

    current_time = str(datetime.datetime.now().time()).split(':')[0] + ':' + \
                   str(datetime.datetime.now().time()).split(':')[1]
    print(current_time)

    if current_time == '00:00':
        print('Now count_of_data = 0')
        count_of_data = 0

    print('ok')


schedule.every(10).seconds.do(main)

if __name__ == '__main__':
    while True:
        schedule.run_pending()
        time.sleep(1)
