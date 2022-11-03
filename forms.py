from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired, EqualTo, Length


# ===== Forms =====
class UserForm(FlaskForm):
    name = StringField("", validators=[DataRequired()])
    email = StringField("", validators=[DataRequired()])
    password = PasswordField("", validators=[DataRequired(), EqualTo("password_confirm", message="Passwords Must Match!")])
    password_confirm = PasswordField("", validators=[DataRequired()])
    submit = SubmitField("Sign Up")
    
class LoginForm(FlaskForm): 
    email = StringField("", validators=[DataRequired()])
    password = PasswordField("", validators=[DataRequired()])
    submit = SubmitField("Login")
    
class TranscriptForm(FlaskForm): 
    title = StringField("", validators=[DataRequired()])
    content = StringField("", validators=[DataRequired()], widget=TextArea())
    author = StringField("", validators=[]) 
    submit = SubmitField("Save") 