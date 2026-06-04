from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class MessageForm(FlaskForm):
    """Form for sending messages"""
    
    content = TextAreaField('Message', validators=[
        DataRequired(message='Message cannot be empty'),
        Length(min=1, max=2000, message='Message must be between 1 and 2000 characters')
    ])
    submit = SubmitField('Send Message')


class StartConversationForm(FlaskForm):
    """Form for starting a new conversation"""
    
    content = TextAreaField('Message', validators=[
        DataRequired(message='Message cannot be empty'),
        Length(min=1, max=2000, message='Message must be between 1 and 2000 characters')
    ])
    submit = SubmitField('Start Conversation')