from flask import current_app, render_template,url_for
from flask_mail import Message
from extensions import mail

class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def send_verification_email(user, token):
        """Send email verification link"""
                
        verification_url =  url_for('auth.verify_email', token=token , _external=True)
        html_content = render_template('verify_email.html',
                                     user=user,
                                     verification_url=verification_url)
        
        msg = Message(
            subject='Verify Your Email Address - EcoWaste',
            recipients=[user.email],
            html=html_content,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@ecowaste.com')
        )
        
        try:
            mail.send(msg)
            return True
        except Exception as e:
            current_app.logger.error(f'Failed to send verification email: {str(e)}')
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email after verification"""
        
        html_content = render_template('welcome.html', user=user)
        
        msg = Message(
            subject='Welcome to EcoWaste!',
            recipients=[user.email],
            html=html_content,
        )
        
        try:
            mail.send(msg)
            return True
        except Exception as e:
            current_app.logger.error(f'Failed to send welcome email: {str(e)}')
            return False