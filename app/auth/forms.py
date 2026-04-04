from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, PasswordField, SelectField, StringField, SubmitField, ValidationError
from wtforms.validators import Length,EqualTo,Email,DataRequired,ValidationError

from app.auth.models import Company, User


class CompanyRegisterForm(FlaskForm):
    def validate_email(self,email_to_check):
        user=User.query.filter_by(email=email_to_check.data).first()
        if user:
            raise ValidationError('Email already exsit! Please try a different username')
    def validate_name(self,name_to_check):
        name=Company.query.filter_by(name=name_to_check.data).first()
        if name:
            raise ValidationError('The Company already exist')
    company_name=StringField(label="COMPANY NAME",validators=[Length(min=2,max=30),DataRequired()])
    business_type=StringField(label="Busniss type",validators=[Length(min=2,max=30),DataRequired()])
    company_activity=StringField(label="BUSINESS ACTIVITY",validators=[Length(min=2,max=30),DataRequired()])
    company_email=StringField(label="COMPANY EMAIL",validators=[Email(),DataRequired()])
    company_phone=StringField(label="COMPANY PHONE",validators=[DataRequired()])
    address=StringField(label="ADDRESS",validators=[Length(min=2,max=30),DataRequired()])
    country=StringField(label="COUNTRY",validators=[Length(min=2,max=30),DataRequired()])
    city=StringField(label="CITY",validators=[Length(min=2,max=30),DataRequired()])
    state=StringField(label="STATE",validators=[Length(min=2,max=30)])
    postal_code=IntegerField(label="POSTAL CODE")
    rc=StringField(label="RC")
    nif=StringField(label="NIF")
    nis=StringField(label="NIS")
    full_name=StringField(label="FULL_NAME",validators=[Length(min=2,max=30),DataRequired()])
    email=StringField(label="EMAIL",validators=[Email(),DataRequired()])
    phone=StringField(label="PHONE",validators=[DataRequired()])
    role = SelectField('Role', choices=[
            'Owner','Manager','employee'
           
            
        ], validators=[DataRequired()])
    password=PasswordField(label='PASSWORD',validators=[Length(min=6),DataRequired()])
    confirm_password=PasswordField(label='CONFIRM PASSWORD',validators=[EqualTo('password')])
    submit=SubmitField(label="Create Account")

class UserRegisterForm(FlaskForm):
    full_name=StringField(label="FULL_NAME",validators=[Length(min=2,max=30),DataRequired()])
    email=StringField(label="EMAIL",validators=[Email(),DataRequired()])
    phone=StringField(label="PHONE",validators=[DataRequired()])
    role=StringField(label="ROLE")
    password=PasswordField(label='PASSWORD',validators=[Length(min=6),DataRequired()])
    confirm_password=PasswordField(label='CONFIRM PASSWORD',validators=[EqualTo('password1')])
    submit=SubmitField(label="Create Account")
class LoginForm(FlaskForm):
    email=StringField(label="EMAIL",validators=[Email(),DataRequired()])
    password=PasswordField(label="PASSWORD",validators=[DataRequired()])
    remember_me=BooleanField()
    submit=SubmitField(label="LOGIN")