import json
import datetime
import time

import requests
import schedule as schedule

import sqlite3

import re


from message import send_mes

db_name = 'date_' + '_'.join(str(datetime.datetime.now()).split()[0].split('-'))
old_db = 'date_' + '_'.join(str(datetime.datetime.now()).split()[0].split('-'))
print(db_name)

cn = sqlite3.connect('db/database.db')
cur = cn.cursor()

cur.execute(f'''CREATE TABLE IF NOT EXISTS {db_name} (id INTEGER PRIMARY KEY UNIQUE NOT NULL, region STRING,
                city STRING, adress STRING, cash STRING, noncash STRING, terminal_id STRING, money_limit INTEGER,
                token_limit INTEGER, summ_all INTEGER, summ_cash INTEGER, summ_noncash INTEGER, current_tokens INTEGER,
                count_of_sells INTEGER, count_of_money INTEGER, count_of_returns INTEGER)''')
try:

    cur.execute(f'''INSERT INTO {db_name} SELECT * FROM terminals''')
    cur.execute(f'''UPDATE {db_name} SET summ_all = 0, summ_cash = 0, summ_noncash = 0, count_of_sells = 0,
    count_of_returns = 0''')

except Exception as ex:

    pass

print('ok')

cn.commit()
cn.close()

SERVER = 'https://ofd.ru/api/Authorization/CreateAuthToken'
ABOUT = 'https://ofd.ru/api/integration/v1/inn/5027242359/kkt/0005861087048356/receipts'
GET_CHECK_INFO = 'https://ofd.ru/api/integration/v1/inn/5027242359/kkt/0005861087048356/receipt/'

count_of_data = 0

now_date = datetime.date.today()


def get_token():
    data_for_log = {
        'Login': '****',
        'Password': '****'
    }

    req = requests.post(SERVER, json=data_for_log)

    token = req.json()['AuthToken']

    return token


def get_info():
    url = 'https://ofd.ru/api/integration/v1/inn/5027242359/kkt/0005861087048356/receipts'
    print(str(datetime.datetime.now()))
    data_for_info = {
        'dateFrom': str(datetime.datetime.now()),
        'dateTo': str(datetime.datetime.now()),
        # 'dateFrom': '2022-11-02 17:06:01.739239',
        # 'dateTo': '2022-11-02 17:06:01.739239',
        'AuthToken': get_token()
    }

    req = requests.get(url, params=data_for_info)

    # url = 'https://ofd.ru/api/integration/v1/inn/5027242359/kkt/0005861087048356/receipts'
    #
    # dataf = {
    #     'ShiftNumber': '240',
    #     'FnNumber': '9961440300201023',
    #     'AuthToken': get_token()
    # }
    # req = requests.get(url, params=dataf)
    return req.json()


def to_json(info):
    with open('file.json', mode='w') as file:
        json.dump(info, file, indent=4)


def function(check, city=False):
    res = requests.get(GET_CHECK_INFO + f'{check["DocRawId"]}?AuthToken={get_token()}')

    if city:
        print(res.json()['Data']['CalculationPlace'])
        return res.json()['Data']['CalculationPlace']

    return res.json()


def main():
    global count_of_data
    global db_name
    global old_db
    global now_date

    ccount = 0

    info = get_info()

    to_json(info)

    print('Count of data:', count_of_data)
    print('Len info:', len(info['Data']))

    if count_of_data < len(info['Data']):

        cn = sqlite3.connect('db/database.db')
        cur = cn.cursor()

        results = cur.execute('''SELECT * FROM bills''').fetchall()

        for check in info['Data'][:len(info['Data']) - count_of_data:]:
            check_id = check['Id']
            ccount += 1

            out_of_date = []
            list_of_ids = []

            for bill_id in results:

                if datetime.datetime.now() - datetime.timedelta(days=3) > \
                        datetime.datetime.strptime(bill_id[2], '%Y-%m-%d %H:%M:%S.%f'):
                    out_of_date.append(bill_id[1])
                list_of_ids.append(bill_id[1])
            if check['Id'] not in list_of_ids:
                cur.execute('''INSERT INTO bills (bill_id, bill_date) VALUES (?,?)''', [check['Id'],
                                                                                        datetime.datetime.now()])

            for bill in out_of_date:
                cur.execute(f'''DELETE FROM bills WHERE bill_id=?''', [bill])

            path = f'{check["DocRawId"]}?AuthToken={get_token()}'
            print(path)
            print(ccount)
            res = requests.get(GET_CHECK_INFO + path)

            time.sleep(1)

            check = function(check)

            flag = True
            inf = []
            print(res.json())
            try:
                print(res.json()['Data']['Calculation_Place'])
            except:
                continue

            for first in range(1, len(res.json()['Data']['Calculation_Place'].split()) + 1):
                if not flag:
                    break
                for second in range(2, len(res.json()['Data']['Calculation_Place'].split()) + 1):
                    if flag:
                        if not inf:
                            g = re.sub(r',', '',
                                       res.json()['Data']['Calculation_Place'].split()[-first].capitalize())
                            v = re.sub(r',', '',
                                       res.json()['Data']['Calculation_Place'].split()[-second].capitalize())
                            inf = cur.execute(f'''SELECT *
                            FROM {db_name} WHERE adress LIKE ('%' || ? || '%')
                            AND adress LIKE ('%' || ? || '%')''',
                                              [g, v]).fetchall()
                        if inf:
                            flag = False

                            money_limit = inf[0][7]
                            token_limit = inf[0][8]
                            current_tokens = inf[0][12]
                            count_of_money = inf[0][14]

                            # if current_tokens - 1 <= token_limit:
                            #     send_mes('1', f"{inf[0][1]} {inf[0][2]} {inf[0][3]}")
                            # if count_of_money >= money_limit:
                            #     send_mes('2', f"{inf[0][1]} {inf[0][2]} {inf[0][3]}")

                            print(check)

                            datas = [x for x in inf[0]]
                            datas[10] += check['Data']['Amount_Cash'] // 100
                            datas[11] += check['Data']['Amount_ECash'] // 100
                            datas[9] = datas[10] + datas[11]
                            datas[12] -= 1
                            datas[13] += 1
                            datas[14] += check['Data']['Amount_Cash'] // 100
                            datas.pop(0)
                            datas[-1] = datas[2]
                            # abv = [datas[0], datas[1], datas[2], datas[6], datas[7],
                            #        (check['Data']['Amount_Cash'] // 100) + (check['Data']['Amount_ECash'] // 100),
                            #        check['Data']['Amount_Cash'] // 100, check['Data']['Amount_ECash'] // 100,
                            #        datas[11], datas[12], check['Data']['Amount_Cash'] // 100, datetime.date.today()]
                            abv = [datas[0], datas[1], datas[2],
                                   (check['Data']['Amount_Cash'] // 100) + (check['Data']['Amount_ECash'] // 100),
                                   check['Data']['Amount_Cash'] // 100, check['Data']['Amount_ECash'] // 100, 1,
                                   datetime.datetime.now()]
                            datas = datas[8::]

                            if check['Data']['Amount_Cash'] // 100 < 1000 and \
                                    check['Data']['Amount_ECash'] // 100 < 1000:
                                continue

                            cur.execute('''UPDATE bills SET address = ?, price_e = ?, price_c = ? WHERE bill_id = ?''',
                                        [datas[-1], check['Data']['Amount_ECash'] // 100,
                                         check['Data']['Amount_Cash'] // 100, check_id])

                            cur.execute(f'''UPDATE {db_name} SET summ_all = ?, summ_cash = ?, summ_noncash = ?,
                            current_tokens = ?, count_of_sells = ?, count_of_money = ?, count_of_returns = 0
                            WHERE adress = ?''', datas)

                            abv.append(0)

                            cur.execute(f'''INSERT INTO sum_of_tables(region, city, adress,
                            summ_all, summ_cash, summ_noncash, count_of_sells,
                            date, count_of_returns) VALUES(?,?,?,?,?,?,?,?,?)''', abv)

                            print(datas)

                            break

        cn.commit()
        cn.close()

        count_of_data = len(info['Data'])

    new_date = datetime.date.today()

    if now_date != new_date:

        count_of_data = 0
        db_name = 'date_' + '_'.join(str(datetime.datetime.now()).split()[0].split('-'))

        cn = sqlite3.connect('db/database.db')
        cur = cn.cursor()

        cur.execute(f'''CREATE TABLE IF NOT EXISTS {db_name} (id INTEGER PRIMARY KEY UNIQUE NOT NULL, region STRING,
                city STRING, adress STRING, cash STRING, noncash STRING, terminal_id STRING, money_limit INTEGER,
                token_limit INTEGER, summ_all INTEGER, summ_cash INTEGER, summ_noncash INTEGER, current_tokens INTEGER,
                count_of_sells INTEGER, count_of_money INTEGER, count_of_returns INTEGER)''')

        cur.execute(f'''INSERT INTO {db_name} SELECT * FROM {old_db}''')

        cur.execute(f'''UPDATE {db_name} SET summ_all = 0, summ_cash = 0, summ_noncash = 0, count_of_sells = 0,
        count_of_returns = 0''')

        cn.commit()
        cn.close()

        old_db = db_name
        now_date = new_date

    print('ok')


schedule.every(10).seconds.do(main)

while True:
    schedule.run_pending()
    time.sleep(1)
