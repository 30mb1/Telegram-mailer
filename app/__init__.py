from flask import Flask
from werkzeug.contrib.fixers import ProxyFix
import threading
import time

process_list = {}
clients_list = {}

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

app = Flask(__name__)
app.secret_key = 'L\x16v\xcc\x05\xd5\x10_\xee\xce\xd9\x1b\xaf\x06\xc0\xa4\xe6\x13\x0e\x8a\xad?W\xaf'
app.wsgi_app = ProxyFix(app.wsgi_app)

t = threading.Thread(target=garbage_collector, args=())
t.start()

from app import views
