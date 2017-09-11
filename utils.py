from multiprocessing import Process, Lock
import time
from app import process_list, mutex_list
from uuid import uuid4
from telethon import TelegramClient
from database import Storage

def make_request(tg_client, phone):

    tg_client.connect()

    tg_client.sign_in(phone)

    tg_client.disconnect()

def request_sign_in(tg_client, phone):

    p = Process(target=make_request, args=(tg_client, phone, ))
    process_list[uuid4()] = { 'process' : p, 'times_checked' : 0 }
    p.start()

def send_msg(client, user, message, mutex, interval):
    mutex.acquire()
    try:
        client.send_msg(user, message)
        res = True
    except:
        res = False
    finally:
        time.sleep(interval)
        mutex.release()
        return res

def start_spam(phone, user_list, interval, message):
    s = Storage()
    keys = s.get_api_keys()

    session_id = s.get_session_id_by_phone(phone)

    client = TelegramClient(session_id, keys['api_id'], keys['api_hash'])
    client.connect()

    mutex = mutex_list.setdefault(phone, Lock())

    for user in user_list:
        not_edited = user
        if user[0] == '@':
            user = user[1:]
        if send_msg(client, user, message, mutex, interval):
            s.user_invoiced(message, not_edited)


def garbage_collector():
    print ('garbage_collector started.')
    while True:
        for key, item in process_list.items():
            if item['times_checked'] <= 5:
                item['times_checked'] += 1
                continue

            item['process'].terminate()
            item['process'].join()

            process_list.pop(key, None)
        time.sleep(3600)
