from app.subscription.models import SubscriptionPlan
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, IntegerField, SelectField, DecimalField,SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Optional, NumberRange



class SubscriptionPlanForm(FlaskForm):
    """Form for subscription plans"""
    
    name = StringField('Plan Name', validators=[
        DataRequired(message='Plan name is required'),
        Length(min=2, max=50)
    ])
    
    slug = StringField('Slug', validators=[
        Optional(),
        Length(max=50)
    ])
    
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500)
    ])
    
    price_monthly = DecimalField('Monthly Price (USD)', validators=[
        Optional(),
        NumberRange(min=0, message='Price cannot be negative')
    ])
    
    price_yearly = DecimalField('Yearly Price (USD)', validators=[
        Optional(),
        NumberRange(min=0, message='Price cannot be negative')
    ])
    
    currency = SelectField('Currency', choices=[
        ('USD', 'USD - US Dollar'),
        ('EUR', 'EUR - Euro'),
        ('DZD', 'DZD - Algerian Dinar')
    ], validators=[DataRequired()])
    
    # Limits
    max_active_listings = IntegerField('Max Active Listings', validators=[
        Optional(),
        NumberRange(min=0, message='Must be 0 or greater')
    ])
    
    max_featured_listings = IntegerField('Max Featured Listings', validators=[
        Optional(),
        NumberRange(min=0, message='Must be 0 or greater')
    ])
    
    max_team_members = IntegerField('Max Team Members', validators=[
        Optional(),
        NumberRange(min=1, message='At least 1')
    ])
    
    max_monthly_transactions = IntegerField('Max Monthly Transactions', validators=[
        Optional(),
        NumberRange(min=0, message='Must be 0 or greater')
    ])
    
    commission_rate = DecimalField('Commission Rate (%)', validators=[
        Optional(),
        NumberRange(min=0, max=100, message='Must be between 0 and 100')
    ])
    
    # Features
    has_analytics = BooleanField('Advanced Analytics')
    has_api_access = BooleanField('API Access')
    has_priority_support = BooleanField('Priority Support')
    has_bulk_upload = BooleanField('Bulk Upload')
    has_advanced_filters = BooleanField('Advanced Filters')
    has_dedicated_manager = BooleanField('Dedicated Account Manager')
    
    # Display
    sort_order = IntegerField('Sort Order', validators=[Optional(), NumberRange(min=0)])
    is_active = BooleanField('Active', default=True)
    is_popular = BooleanField('Popular (Highlighted)', default=False)
    
    def validate_slug(self, field):
        if field.data:
            existing = SubscriptionPlan.query.filter_by(slug=field.data).first()
            if existing and existing.id != getattr(self, '_plan_id', None):
                raise ValidationError('This slug is already taken.')


class AdminSubscriptionForm(FlaskForm):
    """Form for assigning subscription to company"""
    
    plan_id = SelectField('Subscription Plan', coerce=int, validators=[DataRequired()])
    interval = SelectField('Billing Interval', choices=[
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ], validators=[DataRequired()])
    duration_months = IntegerField('Duration (months)', validators=[
        DataRequired(),
        NumberRange(min=1, max=36)
    ])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])

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





class CategoryForm(FlaskForm):
    """Form for creating/editing categories"""
    
    name = StringField('Category Name', validators=[
        DataRequired(message='Category name is required'),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    
    slug = StringField('Slug', validators=[
        Optional(),
        Length(max=100, message='Slug cannot exceed 100 characters')
    ])
    
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=2000, message='Description cannot exceed 2000 characters')
    ])
    
    icon = StringField('Icon (FontAwesome class)', validators=[
        Optional(),
        Length(max=50)
    ])
    
    color = StringField('Color', validators=[
        Optional(),
        Length(max=20)
    ])
    
    #parent_id = SelectField('Parent Category', coerce=int, validators=[Optional()])
    
    waste_type = SelectField('Waste Type', choices=[
        ('', 'Select Waste Type'),
        ('hazardous', 'Hazardous'),
        ('non-hazardous', 'Non-Hazardous'),
        ('e-waste', 'E-Waste'),
        ('organic', 'Organic'),
        ('recyclable', 'Recyclable')
    ], validators=[Optional()])
    
    requires_license = BooleanField('Requires License')
    requires_special_handling = BooleanField('Requires Special Handling')
    min_quantity_default = DecimalField('Minimum Quantity Default', validators=[Optional(), NumberRange(min=0)])
    
    sort_order = IntegerField('Sort Order', validators=[Optional(), NumberRange(min=0)])
    is_active = BooleanField('Active', default=True)
    is_featured = BooleanField('Featured', default=False)
    
    meta_title = StringField('Meta Title', validators=[Optional(), Length(max=200)])
    meta_description = TextAreaField('Meta Description', validators=[Optional(), Length(max=500)])
    meta_keywords = StringField('Meta Keywords', validators=[Optional(), Length(max=200)])
    submit=SubmitField(label="Save")

class CategoryAttributeForm(FlaskForm):
    """Form for creating/editing quality attributes"""
    
    name = StringField('Attribute Name', validators=[
        DataRequired(message='Attribute name is required'),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    
    attribute_type = SelectField('Field Type', choices=[
        ('text', 'Text Input'),
        ('number', 'Number Input'),
        ('select', 'Dropdown Select'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkboxes'),
        ('textarea', 'Text Area')
    ], validators=[DataRequired()])
    
    is_required = BooleanField('Required Field')
    placeholder = StringField('Placeholder Text', validators=[Optional(), Length(max=200)])
    help_text = TextAreaField('Help Text', validators=[Optional(), Length(max=500)])
    
    sort_order = IntegerField('Sort Order', validators=[Optional(), NumberRange(min=0)])
    is_active = BooleanField('Active', default=True)
    submit=SubmitField(label="Save")
