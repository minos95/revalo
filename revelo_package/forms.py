from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,IntegerField,SelectField,HiddenField
from wtforms.validators import Length,EqualTo,Email,DataRequired,ValidationError
from revelo_package.models import User,Company,Category

class CompanyRegisterForm(FlaskForm):
    def validate_email(self,email_to_check):
        user=User.query.filter_by(email=email_to_check.data).first()
        if user:
            raise ValidationError('Email already exsit! Please try a different username')
    def validate_name(self,name_to_check):
        name=Company.query.filter_by(name=name_to_check.data).first()
        if name:
            raise ValidationError('The Company already exist')
    name=StringField(label="COMPANY NAME",validators=[Length(min=2,max=30),DataRequired()])
    company_type=StringField(label="COMPANY TYPE",validators=[Length(min=2,max=30),DataRequired()])
    activity=StringField(label="Company Activity",validators=[Length(min=2,max=30),DataRequired()])
    address=StringField(label="ADDRESS",validators=[Length(min=2,max=30),DataRequired()])
    country=StringField(label="COUNTRY",validators=[Length(min=2,max=30),DataRequired()])
    city=StringField(label="CITY",validators=[Length(min=2,max=30),DataRequired()])
    rc=StringField(label="RC")
    nif=StringField(label="NIF")
    nis=StringField(label="NIS")
    full_name=StringField(label="FULL_NAME",validators=[Length(min=2,max=30),DataRequired()])
    email=StringField(label="EMAIL",validators=[Email(),DataRequired()])
    phone=StringField(label="PHONE",validators=[DataRequired()])
    role=StringField(label="ROLE")
    password1=PasswordField(label='PASSWORD',validators=[Length(min=6),DataRequired()])
    password2=PasswordField(label='CONFIRM PASSWORD',validators=[EqualTo('password1')])
    submit=SubmitField(label="Create Account")

class UserRegisterForm(FlaskForm):
    full_name=StringField(label="FULL_NAME",validators=[Length(min=2,max=30),DataRequired()])
    email=StringField(label="EMAIL",validators=[Email(),DataRequired()])
    phone=StringField(label="PHONE",validators=[DataRequired()])
    role=StringField(label="ROLE")
    password1=PasswordField(label='PASSWORD',validators=[Length(min=6),DataRequired()])
    password2=PasswordField(label='CONFIRM PASSWORD',validators=[EqualTo('password1')])
    submit=SubmitField(label="Create Account")
class LoginForm(FlaskForm):
    email=StringField(label="EMAIL",validators=[Email(),DataRequired()])
    password=PasswordField(label="PASSWORD",validators=[DataRequired()])
class postItemForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
            # Populate choices dynamically
        self.category.choices = [(c.id, c.name) for c in Category.query.all()]

    name=StringField(label='TITLE',validators=[Length(min=2,max=30),DataRequired()])
    description=StringField(label='DESCRIPTION',validators=[Length(min=2,max=300)])
    category=SelectField("CATEGORY",choices=[],validators=[DataRequired()])
    unit=SelectField(label='UNIT',choices=[(1,'KG'),(2,'TON')],validators=[DataRequired()])
    quantity=IntegerField(label='QUANTITY',validators=[DataRequired()]) 
    location=StringField(label='PICKUP LOCATION',validators=[DataRequired()])
    price=IntegerField(label='PRICE') 
    submit=SubmitField(label="POST WASTE")
       
    