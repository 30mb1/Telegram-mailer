from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import Required, Optional


class LoginForm(FlaskForm):
    username = StringField('Username', [Required()])
    password = PasswordField('Password', [Required()])

class RegistrationForm(FlaskForm):
    username = StringField('Username', [Required()])
    password = PasswordField('Password', [Required()])
    submit_reg = SubmitField('Add')

class newAccountForm(FlaskForm):
    phone = StringField('Phone number', [Required()])
    submit_acc = SubmitField('Add')

class SpamForm(FlaskForm):
    users = TextAreaField('Users', [Required()])
    message = TextAreaField('Message', [Required()])
    interval = IntegerField('Interval', [Required()])
    submit_spam = SubmitField('Add')
