
from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, HiddenField, IntegerField, StringField, SubmitField, TextAreaField
from wtforms.validators import Length,EqualTo,Email,DataRequired, Optional,ValidationError,NumberRange
from wtforms.widgets import HiddenInput

from app.listings.models import Item

class makeOfferForm(FlaskForm):
    """Form for making an offer on a listing"""
    
    price = DecimalField('Price', validators=[
        DataRequired(message='Please enter an offer price'),
        NumberRange(min=1, message='Price must be greater than 0')
    ])
    
    quantity = DecimalField('Quantity', validators=[
        Optional(),
        NumberRange(min=1, message='Quantity must be greater than 0')
    ])
    
    message = TextAreaField('Message', validators=[
        Optional(),
    ])
    submit=SubmitField(label="Submit Offer")
    
    requires_delivery = BooleanField('Requires Delivery', default=False)
    delivery_address = TextAreaField('Delivery Address', validators=[Optional()])
    
    def __init__(self, listing=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing = listing
    
   # def validate_price(self, field):
    #    """Validate offer price against listing"""
     #   if self.listing and self.listing.price and field.data > self.listing.price * 2:
      #      raise ValidationError(f'Offer price seems too high. Maximum suggested: ${self.listing.price * 2:.2f}')
       # 
        #if self.listing and self.listing.price and field.data < self.listing.price * 0.1:
         #   raise ValidationError(f'Offer price seems too low. Minimum suggested: ${self.listing.price * 0.1:.2f}')
    
    def validate_quantity(self, field):
        """Validate offer quantity against available quantity"""
        if self.listing and field.data:
            if field.data > self.listing.quantity:
                raise ValidationError(f'Quantity cannot exceed available {self.listing.quantity} {self.listing.unit}')
    
    def validate_delivery_address(self, field):
        """Validate delivery address if delivery is required"""
        if self.requires_delivery.data and not field.data:
            raise ValidationError('Please provide a delivery address')

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