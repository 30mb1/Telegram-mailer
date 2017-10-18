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
    # request code in another thread, because sometimes it got stuck for no reason
    p = Thread(target=make_request, args=(phone, ))
    p.start()

def send_msg(client, user, message):
    res = False
    try:
        client.send_message(user, message)
        print ('Message sent to {}'.format(user))

        res = True
    except Exception as e:
        print ('Trouble while sending message to {}'.format(user))
        print (e)
    finally:
        return res

def start_spam(accounts, user_list, interval, message):
    s = Storage()
    keys = s.get_api_keys()

    # get all available accounts
    clients = [TelegramClient(acc['session_id'], keys['api_id'], keys['api_hash']) for acc in accounts]

    # iterate over all accounts
    # save only working clients (they may be banned for some reasond)
    on_clients = []
    for idx, client in enumerate(clients):
        try:
            #try connecting account
            client.connect()
            on_clients.append(client)
            print ('Client {} connected.'.format(idx))
            print ('Client authorized: {}'.format(client.is_user_authorized()))
        except Exception as e:
            print ("Client {} can't connect: ".format(idx))
            print (e)
            # try one more time
            try:
                client.connect()
                on_clients.append(client)
                print ('Client {} connected.'.format(idx))
                print ('Client authorized: {}'.format(client.is_user_authorized()))
            except Exception as e:
                # if
                print ("Client {} can't connect: ".format(idx))



    for idx, user in enumerate(user_list):
        not_edited = user
        if user[0] == '@':
            # check if it is username, not phone number
            user = user[1:]

        try:
            # send message from client N
            if send_msg(on_clients[idx % len(accounts)], user, message):
                s.user_invoiced(message, not_edited)
        except Exception as e:
            print (e) # set logger later

        time.sleep(interval)

    for client in on_clients:
        try:
            client.disconnect()
        except Exception as e:
            print (e) # set logger later

def generate_report():
    s = Storage()
    data = next(s.get_spam_jobs())
    print (data)
    filename = './tmp/report.txt'
    with open(filename, 'w') as f:
        for user, delivered in data['delivery'].items():
            f.write('{} - {}\n'.format(user, delivered))

def garbage_collector():
    # kill all processes that got stuck
    while True:
        processes_to_delete = []
        for key, item in list(process_list.items()):
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
