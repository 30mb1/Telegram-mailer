# Telegram mailer

Telegram mailer is a web-application that allows sending messages to list of users from a number of accounts that you have connected to it, so that you don't have to do it manually or worry about ban. It is a great tool for automation of mail distribution for your customer base via telegram.

## Getting started

### Requirements

- Python 3
- MongoDB 3.2+
- Nginx/Apache
- 1+ telegram accounts

### Installation

Clone repository

```bash
git clone https://github.com/30mb1/Telegram-mailer.git
cd Telegram-mailer
```

Create virtual environment and install requirements.

```bash
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
```

Set up proxy server (example for nginx):

- Create new configuration file in save it in */etc/nginx/sites-available/your_app.conf*

  Content of *your_app.conf*:

  ```
  server {
      listen 80;
      server_name some_domain.com;
   
      root /path/to/your_app;
   
      access_log /path/to/your_app/logs/access.log;
      error_log /path/to/your_app/logs/error.log;
   
      location / {
          proxy_set_header X-Forward-For $proxy_add_x_forwarded_for;
          proxy_set_header Host $http_host;
          proxy_redirect off;
          if (!-f $request_filename) {
              proxy_pass http://127.0.0.1:8000; # you can choose another port
              break;
          }
      }
  }
  ```

- Create symbol link for sites-enabled:

  ```
  sudo ln -s /etc/nginx/sites-available/your_app.conf /etc/nginx/sites-enabled/
  ```

- Check configuration for mistakes:

  ```
  nginx -t
  ```

- If it is ok, reload nginx.

  ```
  service nginx reload
  ```

Now you can run application locally with gunicorn, using nginx for handling external requests and redirecting them.

### Setting up

Application use telegram client api, so that we need api keys. Follow instructions on [this](https://core.telegram.org/api/obtaining_api_id) page to get **api_id** and **api_hash**. You then need to install them in app, using *initialize.py* module:

```
> cd Telegram-mailer
> source venv/bin/activate
> python initialize.py
Enter api_id:
YOUR_API_ID
Enter api_hash:
YOUR_API_HASH
```

Now you can run application and check it locally or from external address that we specified in .conf file.

```bash
cd Telegram-mailer
source venv/bin/activate
# choose port, that we used in nginx .conf file earlier
gunicorn app:app -b 127.0.0.1:8000 -w 8 --threads 8 # you can run it in screen too
# you can set another number of workers or threads, depenging on your system characteristics
# more detailed info you can find for example here
# http://docs.gunicorn.org/en/stable/settings.html
```

To make program work we need to attach some telegram accounts to it, so program will use them for message delivery. You can do it on *account* page of our app. There you also can change login-password

![http://pix.toile-libre.org/upload/original/1508499881.png](http://pix.toile-libre.org/upload/original/1508499881.png)

After putting your phone number in form, you will receive a code, that you need to paste in new form, that will appear

![http://pix.toile-libre.org/upload/original/1508500245.png](http://pix.toile-libre.org/upload/original/1508500245.png)

If the code is correct, number will be marked as activated and stay on this page. This account now is added to list that will be used for delivery. It is better to add more accounts, so that chances of their ban will be less, because app use accounts by queue.

### Run

To start message distribution go to config page

![http://pix.toile-libre.org/upload/original/1508502322.png](http://pix.toile-libre.org/upload/original/1508502322.png)

Specify a list of users you want deliver your message to in form @tg_username/phone_number and a message. Interval is used for pause before sending next message in order to avoid ban.

Accounts, attached to app would be used by queue when sending messages. It means, that if we have 10 accounts and want to send message to 20 users, the order will be:

```
acc1 -> user1
pause for some interval
acc2 -> user2
...
acc1 -> user11
acc2 -> user12
```

While app is sending messages, there will be appropriate window on *mailer* tab. You should not start a new distribution before the old one is ended, because of ban possibility. 
