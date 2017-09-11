from flask import Flask
from multiprocessing import Lock
from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__)
app.secret_key = 'L\x16v\xcc\x05\xd5\x10_\xee\xce\xd9\x1b\xaf\x06\xc0\xa4\xe6\x13\x0e\x8a\xad?W\xaf'
app.wsgi_app = ProxyFix(app.wsgi_app)

process_list = {}
mutex_list = {}


from app import views
