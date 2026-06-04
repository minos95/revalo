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
    business_type=SelectField('Type of company', choices=[
            'SARL','EURL','SASU','SAS'      
        ], validators=[DataRequired()])
    company_activity=SelectField('Activity', choices=[
            "Recycler",
            "Agriculture",
"Fishing",
"Forestry",
"Mining",
"Oil and Gas Extraction",
"Manufacturing",
"Construction",
"Energy Production",
"Water Supply and Waste Management",
"Food and Beverage Processing",
"Textile and Apparel Production",
"Chemical and Pharmaceutical Production",
"Metallurgy and Steel Production",
"Electronic and Semiconductor Manufacturing",
"Automotive and Aerospace Assembly",
"Transportation and Logistics",
"Wholesale and Retail Trade",
"Information Technology",
"Telecommunications",
"Financial Services",
"Healthcare",
"Education",
"Research and Development   "   
        ], validators=[DataRequired()])
    company_email=StringField(label="COMPANY EMAIL",validators=[Email()])
    company_phone=StringField(label="COMPANY PHONE",validators=[DataRequired()])
    address=StringField(label="ADDRESS",validators=[Length(min=2,max=30),DataRequired()])
    country=SelectField('Role', choices=[
            'Algeria'     
        ], validators=[DataRequired()])
    city=SelectField(label="Wilaya",choices=
    ["Adrar","adrar","Chlef", "Laghouat", "Oum El Bouaghi", "Batna","Béjaïa", "Biskra", "Béchar", "Blida", "Bouira", "Tamanrasset","Tébessa",
            "Tlemcen",
            "Tiaret",
            "Tizi Ouzou",
            "Alger",
            "Djelfa",
            "Jijel",
            "Sétif",
            "Saïda",
            "Skikda",
            "Sidi Bel Abbès",
            "Annaba",
            "Guelma",
            "Constantine",
            "Médéa",
            "Mostaganem",
            "M'Sila",
            "Mascara",
            "Ouargla",
            "Oran",
            "El Bayadh",
            "Illizi",
            "Bordj Bou Arreridj",
            "Boumerdès",
            "El Tarf",
            "Tindouf",
            "Tissemsilt",
            "El Oued",
            "Khenchela",
            "Souk Ahras",
            "Tipaza",
            "Mila",
            "Aïn Defla",
            "Naâma",
            " Aïn Témouchent",
            "Ghardaïa",
            "Relizane",])
    state=StringField(label="STATE")
    postal_code=StringField(label="POSTAL CODE")
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
    referal=StringField(label="Referal")
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