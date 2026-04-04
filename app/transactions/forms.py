

       
from typing import NotRequired

from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField


class markInTransitForm(FlaskForm):
    """Form for making an offer on a listing"""
    
   
    submit=SubmitField(label="Confirm")

    

    