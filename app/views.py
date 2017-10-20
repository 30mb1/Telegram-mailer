from app import app, forms, process_list, clients_list
from flask import render_template, request, redirect, url_for, session, current_app, flash, send_from_directory
import time
from database import Storage
from telethon import TelegramClient
import logging
from utils import request_sign_in, start_spam, generate_report
import threading
from multiprocessing import Process
from uuid import uuid4
import os
import os.path

logging.basicConfig(level=logging.DEBUG)

@app.route('/login', methods=['GET','POST'])
def login():
    form = forms.LoginForm()

    # check login for for submitting
    if form.validate_on_submit():
        if current_app.database.check_auth(form.username.data, form.password.data):

            # store login data in session
            session['logged_in'] = True
            return redirect(url_for('config'))

    return render_template('login.html', form=form)

@app.route('/')
@app.route('/config', methods=['GET','POST'])
def config():
    spam_form = forms.SpamForm()


    if spam_form.submit_spam.data and spam_form.validate_on_submit():

        #get list of activated accounts
        accs = current_app.database.get_accounts_list()
        accs = [acc for acc in accs if acc['activated'] == True]

        #get list of users
        users = spam_form.users.data.split('\r\n')

        # if there are activated accounts
        if len(accs) > 0:
            current_app.database.insert_spam_job(users, spam_form.message.data)

            # start spamming in another process
            p = Process(
                target=start_spam,
                args=(
                    accs,
                    users,
                    float(spam_form.interval.data),
                    spam_form.message.data,
                )
            )

            # save process object in global dict for tracking it status
            process_list[spam_form.message.data] = { 'process' : p, 'times_checked' : 0, 'default_time' : len(users) * int(spam_form.interval.data) * 2 }

            p.start()
        else:
            flash('You need to add telegram accounts first.')

        #print (spam_form.data)

    # user requested report for current spam job or termiante it
    if len(request.args) != 0:
        args = [i for i in request.args.keys()]
        if 'Report' in args:
            return redirect('report')
        else:
            process_list[args[0]]['process'].terminate()

    # get list of started spam jobs from db
    jobs = current_app.database.get_spam_jobs()
    alive_jobs = []
    for job in jobs:
        # check if job is still alive
        if process_list.get(job['message'], None) != None:
            if process_list[job['message']]['process'].is_alive():
                alive_jobs.append(job)
            else:
                # if process id dead, delete from db
                current_app.database.delete_spam_job(job['message'])
        else:
            # if there is no such process, delete from db
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
                # connect and use given code
                client.connect()
                client.sign_in(code=request.form['code'])

                time.sleep(0.5)
                if not client.is_user_authorized():
                    # authorization failed
                    client.disconnect()
                    raise Exception("Looks like there was a wrong code? user not authorized.")

                client.disconnect()

                # if it is ok, add account to db
                current_app.database.activate_account(request.form['phone'])
                clients_list.pop(request.form['phone'], None)
            except Exception as e:
                print (e)
                client.disconnect()
                flash('Wrong code or some error occured.', 'activating error')

        # user requested deleting of acc
        elif request.form.get('action', None) == 'Remove':
            current_app.database.del_account(request.form['phone'])

    all_accounts = [account for account in current_app.database.get_accounts_list()]

    return render_template('account.html', reg_form=reg_form, new_acc_form=new_acc_form, all_accounts=all_accounts)

@app.route('/report')
def get_report():
    generate_report()
    try:
        return send_from_directory(
            os.path.join(os.getcwd(), 'tmp'),
            'report.txt'
        )
    except Exception as e:
        print (e)
        return redirect(url_for('config'))

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
    current_app.database = Storage()
    return
