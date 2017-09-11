from multiprocessing import Process, Lock
import time
from app import process_list
from uuid import uuid4
from telethon import TelegramClient
from database import Storage

def make_request(tg_client, phone):

    tg_client.connect()

    tg_client.send_code_request(phone)

    tg_client.disconnect()

def request_sign_in(tg_client, phone):

    p = Process(target=make_request, args=(tg_client, phone, ))
    process_list[uuid4()] = { 'process' : p, 'times_checked' : 0, 'default_time' : 60 }
    p.start()

def send_msg(client, user, message, interval):
    try:
        client.send_msg(user, message)
        res = True
    except:
        res = False
    finally:
        return res

def start_spam(accounts, user_list, interval, message):
    s = Storage()
    keys = s.get_api_keys()

    clients = [TelegramClient(acc['session_id'], keys['api_id'], keys['api_hash']) for acc in accounts]

    for idx, client in enumerate(clients):
        print ('Client {} connected.'.format(idx))
        client.connect()

    for idx, user in enumerate(user_list):
        not_edited = user
        if user[0] == '@':
            user = user[1:]

        if send_msg(clients[idx % len(accounts)], user, message, interval):
            s.user_invoiced(message, not_edited)

        time.sleep(interval)

    for client in clients:
        client.disconnect()


def garbage_collector():
    print ('garbage_collector started.')
    while True:
        for key, item in process_list.items():
            #process dead
            if not item['process'].is_alive():
                item['process'].terminate()
                item['process'].join()
                process_list.pop(key, None)
                continue

            #check if process already wasted its time
            if (item['times_checked'] - 1) * 3600 > item['default_time']:
                item['process'].terminate()
                item['process'].join()
                process_list.pop(key, None)
                continue

            item['times_checked'] += 1

        time.sleep(3600)
