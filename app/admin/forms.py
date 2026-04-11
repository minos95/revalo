from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, IntegerField, SelectField, DecimalField,SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    icon = StringField('Icon Class', validators=[Optional()])
    parent_id = SelectField('Parent Category', coerce=int, choices=[(0, 'None')], validators=[Optional()])
    sort_order = IntegerField('Sort Order', default=0)
    is_active = BooleanField('Active', default=True)


class ModerationForm(FlaskForm):
    action = SelectField('Action', choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('flag', 'Flag for Review')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])


class AdminSettingsForm(FlaskForm):
    platform_name = StringField('Platform Name', default='EcoWaste')
    contact_email = StringField('Contact Email')
    commission_rate = DecimalField('Commission Rate (%)', default=5.0)
    listing_expiry_days = IntegerField('Listing Expiry (days)', default=30)
    dispute_window_hours = IntegerField('Dispute Window (hours)', default=48)

class acceptCompanyForm(FlaskForm):
    verified_submit=SubmitField(label="Verified")
class refuseCompanyForm(FlaskForm):
    refuse_submit=SubmitField(label="refuse")