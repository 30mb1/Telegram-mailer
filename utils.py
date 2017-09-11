from threading import Thread
import time
from app import process_list, clients_list
import logging
from uuid import uuid4
from telethon import TelegramClient
from database import Storage
import time

logging.basicConfig(level=logging.DEBUG)

def make_request(phone):
    clients_list[phone].connect()

    clients_list[phone].send_code_request(phone)

    clients_list[phone].disconnect()

def request_sign_in(phone):
    p = Thread(target=make_request, args=(phone, ))
    p.start()

def send_msg(client, user, message, interval):
    try:
        client.send_message(user, message)
        print ('Message sent to {}'.format(user))

        res = True
    except Exception as e:
        print ('Trouble while sending message to {}'.format(user))
        print (e)
        res = False
    finally:
        return res

def start_spam(accounts, user_list, interval, message):
    s = Storage()
    keys = s.get_api_keys()

    clients = [TelegramClient(acc['session_id'], keys['api_id'], keys['api_hash']) for acc in accounts]

    for idx, client in enumerate(clients):
        try:
            client.connect()
            print ('Client {} connected.'.format(idx))
            print ('Client authorized: {}'.format(client.is_user_authorized()))
        except Exception as e:
            print ("Client {} can't connect: ".format(idx))
            print (e)

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
