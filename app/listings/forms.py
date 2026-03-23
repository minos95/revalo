from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, MultipleFileField, SelectField, StringField, SubmitField, TextAreaField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import Length,EqualTo,Email,DataRequired,ValidationError
from wtforms.widgets import HiddenInput


class FilterMarketForm(FlaskForm):
    #def __init__(self, *args, **kwargs):
     #   super().__init__(*args, **kwargs)
            # Populate choices dynamically
      #  self.category.choices=[("","Tous")]
       # self.category.choices += [(c.id, c.name) for c in Category.query.all()]
    name=StringField(label='TITLE',validators=[Length(min=0,max=30)]) 
    category=SelectField("CATEGORY",choices=[])
    location=SelectField("LOCATION",choices=[("","Tous")])
    min_quantity=IntegerField(label='Min Quantity (kg) ') 
    min_quantity=IntegerField(label='Min Pice') 
    max_quantity=IntegerField(label='Max Price') 
    quality=SelectField("QUALITY",choices=[("","Tous")])
    sorting=SelectField("CATEGORY",choices=["","récemment posté","grande quantité "])
    submit=SubmitField(label="Filtrer")






class postItemForm(FlaskForm):
   # def __init__(self, *args, **kwargs):
        #super().__init__(*args, **kwargs)
            # Populate choices dynamically
       # self.category.choices = [(c.id, c.name) for c in Category.query.all()]
    name=StringField(label='TITLE',validators=[Length(min=2,max=30),DataRequired()])
    description=TextAreaField(label='DESCRIPTION',validators=[Length(min=2,max=300)])
    #category=SelectField(label="Category",choices=[])
    unit=SelectField(label='UNIT',choices=['KG','TON'],validators=[DataRequired()])
    quantity=IntegerField(label='QUANTITY',validators=[DataRequired()]) 
    pickup_address=StringField(label='PICKUP ADDRESS')
    pickup_city=StringField(label='PICKUP CITY')
    pickup_state=StringField(label='PICKUP STATE')
    pickup_country=StringField(label='PICKUP COUNTRY')
    pickup_postal_code=StringField(label='PICKUP POSTAL CODE')
    price_negotiable=BooleanField(label="Negociable price")
    price=IntegerField(label='PRICE') 
    images = MultipleFileField('Image',widget=HiddenInput(),validators=[
        FileAllowed(['jpg', 'png'], 'Les fichiers doivent être des images !')
    ])
    submit=SubmitField(label="Continue to Review →")
    