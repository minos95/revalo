from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,IntegerField,SelectField,HiddenField,TextAreaField,MultipleFileField,BooleanField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import Length,EqualTo,Email,DataRequired,ValidationError
from app.listings.models import Category
from wtforms.widgets import HiddenInput



       

class makeOfferForm(FlaskForm):
    price=IntegerField(label="Price",validators=[DataRequired()])
    message=TextAreaField(label='MESSAGE',validators=[Length(min=0,max=300)]) 
    quantity=IntegerField(label="Quantity", validators=[DataRequired()])
    submit=SubmitField(label="Make offer")

class validateOfferForm(FlaskForm):
    id=HiddenField(label="Price",validators=[])
    item_id=HiddenField(label="Price",validators=[])
    price=IntegerField(widget=HiddenInput())
    quantity=IntegerField(widget=HiddenInput())
    unit=StringField(widget=HiddenInput())
    seller_company_id=HiddenField(label="Price",validators=[])
    buyer_company_id=HiddenField(label="Price",validators=[])
    submit1=SubmitField(label="Confirm offer")

class cancelOfferForm(FlaskForm):
    id=HiddenField(label="id",validators=[])
    submit2=SubmitField(label="Cancel offer")
class rejectOfferForm(FlaskForm):
    id=HiddenField(label="id",validators=[])
    submit3=SubmitField(label="Cancel offer")