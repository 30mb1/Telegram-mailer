from app import app, forms, process_list, clients_list
from flask import render_template, request, redirect, url_for, session, current_app, flash
import time
from database import Storage
from telethon import TelegramClient
import logging
from utils import request_sign_in, garbage_collector, start_spam
import threading
from multiprocessing import Process
from uuid import uuid4

logging.basicConfig(level=logging.DEBUG)

@app.route('/login', methods=['GET','POST'])
def login():
    form = forms.LoginForm()

    if form.validate_on_submit():
        if current_app.database.check_auth(form.username.data, form.password.data):
            session['logged_in'] = True
            return redirect(url_for('index'))

    return render_template('login.html', form=form)

@app.route('/config', methods=['GET','POST'])
def config():
    spam_form = forms.SpamForm()

    if spam_form.submit_spam.data and spam_form.validate_on_submit():

        #get list of activated accounts
        accs = current_app.database.get_accounts_list()
        accs = [acc for acc in accs if acc['activated'] == True]

        #get list of users
        users = spam_form.users.data.split('\r\n')

        #split list into smaller pieces for every account
        if len(accs) > 0:
            current_app.database.insert_spam_job(users, spam_form.message.data)

            #start spamming in another process
            p = Process(
                target=start_spam,
                args=(
                    accs,
                    users,
                    float(spam_form.interval.data),
                    spam_form.message.data,
                )
            )

            process_list[spam_form.message.data] = { 'process' : p, 'times_checked' : 0, 'default_time' : len(users) * int(spam_form.interval.data) * 2}
            p.start()
        else:
            flash('You need to add telegram accounts first.')

        #print (spam_form.data)

    if len(request.args) != 0:
        process_list[next(request.args.keys())].terminate()

    jobs = current_app.database.get_spam_jobs()
    alive_jobs = []
    for job in jobs:
        if process_list.get(job['message'], None) != None:
            if process_list[job['message']]['process'].is_alive():
                alive_jobs.append(job)
            else:
                current_app.database.delete_spam_job(job['message'])
        else:
            current_app.database.delete_spam_job(job['message'])

    return render_template('config.html', spam_form=spam_form, jobs=alive_jobs)

@app.route('/account', methods=['GET','POST'])
def account():
    reg_form = forms.RegistrationForm()
    new_acc_form = forms.newAccountForm()

    #check if registration form was submitted
    if reg_form.submit_reg.data and reg_form.validate_on_submit():
        current_app.database.registration(reg_form.username.data, reg_form.password.data)
        return redirect(url_for('account'))

    #check if new telegram acc form was submitted
    if new_acc_form.submit_acc.data and new_acc_form.validate_on_submit():
        api_keys = current_app.database.get_api_keys()
        api_id, api_hash = api_keys['api_id'], api_keys['api_hash']

        #create new TelegramClient for this number and request activation
        try:
            data = new_acc_form.data
            unique_key = str(uuid4())
            client = TelegramClient(unique_key, api_id, api_hash)

            clients_list[data['phone']] = client

            #creating another process in case of laggs
            request_sign_in(data['phone'])

            current_app.database.add_account(new_acc_form.data, unique_key)

        except:
            flash('Some error occured, try again.', 'registration error')
            pass

        return redirect(url_for('account'))

    #activating or removing account
    if request.form:
        if request.form.get('action', None) == 'Activate' and request.form['code'] != '':
            #activating account through TelegramClient that we created earlier for this number
            client = clients_list[request.form['phone']]

            try:
                client.connect()
                client.sign_in(code=request.form['code'])

                time.sleep(0.5)
                if not client.is_user_authorized():
                    client.disconnect()
                    raise Exception("Looks like there was a wrong code? user not authorized.")

                client.disconnect()

                current_app.database.activate_account(request.form['phone'])
                clients_list.pop(request.form['phone'], None)
            except Exception as e:
                print (e)
                client.disconnect()
                flash('Wrong code or some error occured.', 'activating error')

        elif request.form.get('action', None) == 'Remove':
            current_app.database.del_account(request.form['phone'])

    all_accounts = [account for account in current_app.database.get_accounts_list()]

    return render_template('account.html', reg_form=reg_form, new_acc_form=new_acc_form, all_accounts=all_accounts)

@app.route('/')
@app.route('/index')
def index():

    return render_template('index.html')

@app.route('/logout')
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))

@app.before_request
def before_request():
    if not session.get('logged_in', False) and request.endpoint != 'login':
        return redirect(url_for('login'))


@app.before_first_request
def before_first_request():
    current_app.telegram_clients = {}
    t = threading.Thread(target=garbage_collector, args=())
    t.start()
    current_app.database = Storage()
    return
