from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, IntegerField, MultipleFileField, SelectField, StringField, SubmitField, TextAreaField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import Length,EqualTo,Email,DataRequired, NumberRange, Optional,ValidationError
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
    title = StringField('Title', validators=[
            DataRequired(message='Title is required'),
            Length(min=10, max=200, message='Title must be between 10 and 200 characters')
        ])
    description = TextAreaField('Description', validators=[
            DataRequired(message='Description is required'),
            Length(min=50, max=5000, message='Description must be between 50 and 5000 characters')
        ])
    #category=SelectField(label="Category",choices=[])
    unit = SelectField('Unit', choices=[
            ('kg', 'Kilograms (kg)'),
            ('tons', 'Tons'),
            ('liters', 'Liters'),
            ('pieces', 'Pieces'),
            ('cubic_meters', 'Cubic Meters (m³)'),
            ('pallets', 'Pallets')
        ], validators=[DataRequired()])
    quantity = DecimalField('Quantity', validators=[
            DataRequired(message='Quantity is required'),
            NumberRange(min=0.01, message='Quantity must be greater than 0')
        ])
    price = DecimalField('Price (DA)', validators=[
            Optional(),
            NumberRange(min=0, message='Price cannot be negative')
        ])
        
    price_negotiable = BooleanField('Price is negotiable', default=True)


    pickup_address=StringField(label='PICKUP ADDRESS')
    pickup_city=StringField(label='PICKUP CITY')
    pickup_state=StringField(label='PICKUP STATE')
    pickup_country=StringField(label='PICKUP COUNTRY')
    pickup_postal_code=StringField(label='PICKUP POSTAL CODE')

    images = MultipleFileField('Image',widget=HiddenInput(),validators=[
        FileAllowed(['jpg', 'png'], 'Les fichiers doivent être des images !')
    ])
    submit=SubmitField(label="Continue to Review →")
    
class EditListingForm(FlaskForm):
        """Base form for creating/editing listings"""
        
        name = StringField('Title', validators=[
            DataRequired(message='Title is required'),
            Length(min=5, max=200, message='Title must be between 5 and 200 characters')
        ])
        
        description = TextAreaField('Description', validators=[
            DataRequired(message='Description is required'),
            Length(min=20, max=5000, message='Description must be between 20 and 5000 characters')
        ])

        
        quantity = DecimalField('Quantity', validators=[
            DataRequired(message='Quantity is required'),
            NumberRange(min=0.01, message='Quantity must be greater than 0')
        ])
        
        unit = SelectField('Unit', choices=[
            ('kg', 'Kilograms (kg)'),
            ('tons', 'Tons'),
            ('liters', 'Liters'),
            ('pieces', 'Pieces'),
            ('cubic_meters', 'Cubic Meters (m³)'),
            ('pallets', 'Pallets')
        ], validators=[DataRequired()])
        
        price = DecimalField('Price (DA)', validators=[
            Optional(),
            NumberRange(min=0, message='Price cannot be negative')
        ])
        
        price_negotiable = BooleanField('Price is negotiable', default=True)
        
        # Location fields
        pickup_address = StringField('Address', validators=[Optional(), Length(max=500)])
        pickup_city = StringField('City', validators=[Optional(), Length(max=100)])
        pickup_state = StringField('State/Province', validators=[Optional(), Length(max=50)])
        pickup_country = StringField('Country', validators=[Optional(), Length(max=50)])
        pickup_postal_code = StringField('Postal Code', validators=[Optional(), Length(max=20)])
        
        # Logistics
        pickup_available = BooleanField('Pickup Available', default=True)
        delivery_available = BooleanField('Delivery Available', default=False)
        delivery_cost = DecimalField('Delivery Cost', validators=[Optional(), NumberRange(min=0)])
        
        def validate_price(self, field):
            """Additional validation for price"""
            if field.data and field.data < 0:
                raise ValidationError('Price cannot be negative')



        """Form for editing existing listings with image management"""
        
        # Image management
        delete_images = SelectField('Delete Images', choices=[], coerce=int, validators=[Optional()])
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Set choices for delete_images dynamically
            if hasattr(self, 'listing') and self.listing and self.listing.images:
                choices = [(i, f'Image {i+1}') for i in range(len(self.listing.images))]
                self.delete_images.choices = [('', 'Select image to delete')] + choices