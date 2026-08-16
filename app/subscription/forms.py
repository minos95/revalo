from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, TextAreaField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

class UpgradeForm(FlaskForm):
    """Form for upgrading subscription"""
    
    plan_id = SelectField('Select Plan', coerce=int, validators=[DataRequired()])
    interval = SelectField('Billing Interval', choices=[
        ('yearly', 'Yearly (Save 15%)'),
        ('monthly', 'Monthly')
        
    ], validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[
        ('stripe', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer')
    ], validators=[DataRequired()])


class CancelForm(FlaskForm):
    """Form for cancelling subscription"""
    
    reason = SelectField('Reason for Cancelling', choices=[
        ('', 'Select a reason...'),
        ('too_expensive', 'Too expensive'),
        ('not_using', 'Not using enough'),
        ('features_missing', 'Missing features'),
        ('technical_issues', 'Technical issues'),
        ('customer_support', 'Poor customer support'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    cancel_immediately = BooleanField('Cancel immediately (lose remaining time)')
    feedback = TextAreaField('Additional Feedback', validators=[Optional(), Length(max=500)])
    confirm = BooleanField('I understand that cancelling will remove access to paid features', validators=[DataRequired()])


class PaymentMethodForm(FlaskForm):
    """Form for updating payment method"""
    
    payment_method = SelectField('Payment Method', choices=[
        ('stripe', 'Credit Card'),
        ('paypal', 'PayPal')
    ], validators=[DataRequired()])
    card_number = StringField('Card Number', validators=[Optional()])
    card_expiry_month = SelectField('Expiry Month', choices=[(str(i), str(i)) for i in range(1, 13)], validators=[Optional()])
    card_expiry_year = SelectField('Expiry Year', choices=[(str(i), str(i)) for i in range(2024, 2035)], validators=[Optional()])
    card_cvc = StringField('CVC', validators=[Optional()])
    card_last4 = StringField('Last 4 Digits', validators=[Optional()])
    card_brand = StringField('Card Brand', validators=[Optional()])