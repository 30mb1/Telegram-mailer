from pymongo import MongoClient
from datetime import datetime


class Storage(object):
    def __init__(self):
        self.database = MongoClient()['tg_spamer']

    def check_auth(self, user, password):
        keys = self.database['keys'].find_one(
            { 'type' : 'usr_pswd' }
        )

        #first use, no keys in database, defaut is [admin, admin]
        if keys == None:
            if user == 'admin' == password:
                return True
            return False

        if user == keys['username'] and password == keys['password']:
            return True
        return False

    def registration(self, new_user, new_pass):
        self.database['keys'].update_one(
            { 'type' : 'usr_pswd' },
            {
                '$set' : { 'username' : new_user, 'password' : new_pass }
            },
            upsert=True
        )

    def add_account(self, data, key):
        data['activated'] = False
        data['session_id'] = key
        self.database['accounts'].insert_one(
            data
        )

    def get_session_id_by_phone(self, phone):
        doc = self.database['accounts'].find_one(
            { 'phone' : phone }
        )

        return doc['session_id']

    def get_accounts_list(self):
        return self.database['accounts'].find()

    def del_account(self, phone):
        self.database['accounts'].delete_one(
            {
                'phone' : phone
            }
        )

    def activate_account(self, phone):
        self.database['accounts'].update_one(
            {
                'phone' : phone
            },
            {
                '$set' : { 'activated' : True }
            }
        )

    def register_api(self, api_id, api_hash):
        self.database['keys'].update_one(
            { 'type' : 'api_keys' },
            {
                '$set' : { 'api_id' : api_id, 'api_hash' : api_hash }
            },
            upsert=True
        )

    def get_api_keys(self):
        return self.database['keys'].find_one(
            { 'type' : 'api_keys' },
        )

    def insert_spam_job(self, users, message):
        self.database['spam_jobs'].update_one(
            { 'message' : message },
            {
                '$set' : {
                    'delivery' : { user : False for user in users }
                }
            },
            upsert=True
        )

    def user_invoiced(self, message, user):
        self.database['spam_jobs'].update_one(
            { 'message' : message },
            {
                '$set' : {
                    'delivery.{}'.format(user) : True
                }
            }
        )

    def get_spam_jobs(self):
        return self.database['spam_jobs'].find()
