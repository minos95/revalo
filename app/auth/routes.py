from datetime import datetime
import os

import app
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from flask import Blueprint, flash,redirect,render_template, request,url_for,current_app
from app import db
from app.auth import bp
from flask_login import current_user, login_required, login_user, logout_user
from app.auth.forms import CompanyRegisterForm, EditUserForm, ForgotPasswordForm, LoginForm, ResetPasswordForm,EditCompanyForm
from app.auth.models import Notification, User
from app.auth.models import Company
from flask_mail import  Message
from extensions import mail  # <-- CRITICAL: Import the same mail object here
from werkzeug.utils import secure_filename

@bp.route("/signup",methods=['GET','POST'])
def signup():
    form=CompanyRegisterForm()

    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if form.validate_on_submit():
         # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('A user with this email already exists.', 'danger')
            return redirect(url_for('login'))
            
        company_to_create=Company(name=form.company_name.data,
                                  business_type=form.business_type.data,
                                  business_size=form.business_size.data,
                                  activity=form.company_activity.data,
                                  address=form.address.data,
                                  country=form.country.data,
                                  email=form.company_email.data,
                                  phone=form.company_phone.data,
                                  city=form.city.data,
                                  Postal_code=form.postal_code.data,
                                  rc=form.rc.data,
                                  nif=form.nif.data,
                                  nis=form.nis.data,
                                  referal=form.referal.data)
  
        
        db.session.add(company_to_create)
        
        company_created=Company.query.filter_by(name=form.company_name.data).first()

        # Handle logo upload
        
        if form.documents.data and allowed_file:
            documents=form.documents.data
            documents_name = secure_filename(form.documents.data.filename)
            if documents :
                
                # Save new documents
                filename = secure_filename(f"company_{company_created.id}_{datetime.utcnow().timestamp()}_{documents_name}")
                documents_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'companies/'+company_created.name+'/documents', filename)
                os.makedirs(os.path.dirname(documents_path), exist_ok=True)
                documents.save(documents_path)
                company_created.documents = filename

        user_to_create=User(full_name=form.full_name.data,
                            email=form.email.data,
                            phone=form.phone.data,
                            role=form.role.data,
                            password=form.password.data,
                            company_id=company_created.id)
        
        
        db.session.add(user_to_create)
        db.session.flush()
        
        notification1=Notification(user_id=1,
                                type="new_company",
                                title="New Company",
                                message=f'New Company has been added {form.company_name.data}',
                                related_type="company",
                                )
        notification2=Notification(user_id=1,
                                type="new_user",
                                title="New User",
                                message=f'New User has been added {form.full_name.data}',
                                related_type="User",
                                
                                )
        db.session.add(notification1)
        db.session.add(notification2)
       
        # Generate verification token
        token = user_to_create.generate_verification_token()
        db.session.commit()
         # Send verification email
        EmailService.send_verification_email(user_to_create, token)
        return redirect(url_for('home'))
    if form.errors!={}:
        for field,err_msg in form.errors.items():
            flash(f'error {getattr(form, field).label.text}: {err_msg}',category='danger')
    return render_template('register.html',form=form)

# ============================================
# HELPER FUNCTION
# ============================================

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf', 'jpg', 'jpeg', 'png', 'gif', 'webp'}


@bp.route("/login",methods=['GET','POST'])
def login():
   
   
   form=LoginForm()
   if form.validate_on_submit():
       attempted_user=User.query.filter_by(email=form.email.data).first()
       if attempted_user  and attempted_user.check_password_correction(
           attempted_password=form.password.data):
            if  attempted_user.owned_company.status=="active":
                    if attempted_user.status=="active":
                        if attempted_user.email_verified:
                            login_user(attempted_user)
                            flash("success you are logged in",category='success')
                            return redirect(url_for('dashboard'))
                        else:
                            flash('Verify you email',category='danger')
                    elif attempted_user.status=="suspended":
                        flash('You are suspended',category='danger')
                    elif attempted_user.status=="suspended":
                        flash('You are suspended',category='danger')
                   
            
            elif attempted_user.owned_company.status=="suspended":
                flash(f'{attempted_user.owned_company.name} suspended by EcoWaste admin',category='danger')
            else:
                flash(f'{attempted_user.owned_company.name} still in verification by EcoWaste admin',category='danger')
       else:
           flash('Username or password are incorrect! please try again',category='danger')
   return render_template('login.html',form=form)


@bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logout!",category="info")
    return redirect(url_for('home'))
@bp.route("/setting")
def setting():
    company=Company.query.filter(User.company_id==current_user.company_id).first()

    return render_template('setting.html',user=current_user,company=company)

@bp.route('/detail', methods=['GET', 'POST'])
@login_required
def detail_company():
    """detail company profile"""

    return render_template('detail_company.html')

@bp.route('/edit-company', methods=['GET', 'POST'])
@login_required
def edit_company():
    """Edit company profile"""
    company = current_user.owned_company
    
    # Check permission - only owner or admin can edit company
    if current_user.role not in ['Owner','owner','Admin','admin',"super_admin"]:
        flash('You do not have permission to edit company profile.', 'danger')
        return redirect(url_for('home'))
    
    form = EditCompanyForm(obj=company, company=company)
    
    if form.validate_on_submit():
       
        # Update company fields
        company.name = form.name.data
        company.email = form.email.data
        company.phone = form.phone.data
        company.website = form.website.data
        company.description = form.description.data
        
        # Address
        company.address= form.address.data
        
        company.city = form.city.data
        company.country = form.country.data
        company.postal_code = form.postal_code.data
        
        # Business details
        company.business_type = form.business_type.data
        company.business_size = form.business_size.data
        company.year_established = form.year_established.data
        
        # Social Links
        company.facebook = form.facebook.data
        company.linkedin = form.linkedin.data
        company.twitter = form.twitter.data
        
        # Handle logo upload
        if form.logo_url.data:
            logo_file = form.logo_url.data
            if logo_file :
                # Delete old logo if exists
                if company.logo:
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'companies/'+company.name+'logos', company.logo)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                # Save new logo
                filename = secure_filename(f"company_{company.id}_{datetime.utcnow().timestamp()}_{logo_file.filename}")
                logo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'companies/'+company.name+'/logos', filename)
                os.makedirs(os.path.dirname(logo_path), exist_ok=True)
                logo_file.save(logo_path)
                company.logo = filename

        # handle documents upload
        if form.documents.data and allowed_file:
                    documents=form.documents.data
                    documents_name = secure_filename(form.documents.data.filename)
                    if documents :
                        
                        # Save new documents
                        filename = secure_filename(f"company_{company.id}_{datetime.utcnow().timestamp()}_{documents_name}")
                        documents_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'companies/'+company.name+'/documents', filename)
                        os.makedirs(os.path.dirname(documents_path), exist_ok=True)
                        documents.save(documents_path)
                        company.documents = filename
        
        company.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Company profile updated successfully!', 'success')
        return redirect(url_for('auth.edit_company'))
    
    return render_template('edit_company.html', form=form, company=company)

@bp.route("/settings/profile", methods=["POST","GET"])
@login_required
def update_profile():

    user = User.query.get(current_user.id)
    form=EditUserForm(obj=user)
    if form.validate_on_submit():
        user.full_name = request.form["full_name"]
        user.phone = request.form["phone"]
        user.job_title = request.form["job_title"]
        user.department = request.form["department"]

         # Handle avatar upload
        if form.avatar.data:
            avatar_file = form.avatar.data
            if avatar_file :
                # Delete old avatar if exists
                if current_user.avatar_url:
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars', current_user.avatar_url)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                # Save new avatar
                filename = secure_filename(f"user_{current_user.id}_{datetime.utcnow().timestamp()}_{avatar_file.filename}")
                avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars', filename)
                os.makedirs(os.path.dirname(avatar_path), exist_ok=True)
                avatar_file.save(avatar_path)
                current_user.avatar_url = filename
        
        db.session.commit()

        return redirect(url_for("auth.update_profile"))
    
    return render_template('edit_user.html',form=form,user=current_user)




@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset link"""
    
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            # Generate reset token
            token = user.generate_reset_token()
            
            # Send reset email
            send_reset_email(user.email, token, user.full_name)
            
            flash('Password reset link has been sent to your email address.', 'success')
            return redirect(url_for('auth.reset_sent'))
        else:
            # Don't reveal if email exists
            flash('If an account exists with that email, you will receive a reset link.', 'info')
            return redirect(url_for('auth.reset_sent'))
    
    return render_template('forgot_password.html', form=form)
@bp.route('/reset-sent')
def reset_sent():
    """Show confirmation that reset email was sent"""
    return render_template('reset_sent.html')


# ============================================
# RESET PASSWORD - SET NEW PASSWORD
# ============================================

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    # Find user with valid token
    user = User.query.filter_by(reset_password_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        # Set new password
        user.set_password(form.password.data)
        user.clear_reset_token()
        db.session.commit()
        
        flash('Your password has been reset successfully. Please login with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', form=form, token=token)


# ============================================
# CHANGE PASSWORD (Authenticated Users)
# ============================================

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password for logged in users"""
    
    from app.auth.forms import ChangePasswordForm
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been changed successfully.', 'success')
            return redirect(url_for('profile.index'))
        else:
            flash('Current password is incorrect.', 'danger')
    
    return render_template('change_password.html', form=form)


# ============================================
# EMAIL SENDING FUNCTION
# ============================================

def send_reset_email(email, token, name):
    """Send password reset email"""
    
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #1e5f45 0%, #2c8e64 100%);
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f9f9f9;
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .button {{
                display: inline-block;
                background: #2c8e64;
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                font-size: 12px;
                color: #999;
                margin-top: 20px;
            }}
            .warning {{
                background: #fff3cd;
                border: 1px solid #ffc107;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Password Reset Request</h2>
            </div>
            <div class="content">
                <p>Hello <strong>{name}</strong>,</p>
                <p>We received a request to reset your password for your EcoWaste account.</p>
                <p>Click the button below to create a new password:</p>
                <div style="text-align: center;">
                    <a href="{reset_url}" class="button">Reset Password</a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; font-size: 12px; color: #666;">{reset_url}</p>
                <div class="warning">
                    <strong>⚠️ Security Note:</strong> This link will expire in 24 hours. 
                    If you did not request this password reset, please ignore this email.
                </div>
            </div>
            <div class="footer">
                <p>© 2024 EcoWaste. All rights reserved.</p>
                <p>This is an automated message, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    msg = Message(
        subject='Reset Your EcoWaste Password',
        recipients=[email],
        html=html_content
    )
    
    try:
        
        mail.send(msg)
    except Exception as e:
        print('-----------------------------------')
        print(f'Failed to send reset email: {str(e)}')




# ============================================
# VERIFY EMAIL
# ============================================

@bp.route('/verify-email/<token>', methods=['GET', 'POST'])
def verify_email(token):
    """Verify email address with token"""
    
    # Find user with this token
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        flash('Invalid verification link.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Check if already verified
    if user.email_verified:
        flash('Email already verified. Please login.', 'info')
        return redirect(url_for('auth.login'))
    
    # Verify email
    result = user.verify_email(token)
    
    if result['success']:
        # Send welcome email
        EmailService.send_welcome_email(user)
        
        # Create notification
        NotificationService.create_notification(
            user_id=user.id,
            notification_type='email_verified',
            title='Email Verified!',
            message='Your email address has been verified successfully.',
            priority='normal'
        )
        
        flash('Email verified successfully! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    else:
        flash(result['message'], 'danger')
        return redirect(url_for('auth.login'))


# ============================================
# VERIFICATION SENT PAGE
# ============================================

@bp.route('/verification-sent')
def verification_sent():
    """Page showing verification email was sent"""
    
    email = request.args.get('email', '')
    return render_template('verification_sent.html', email=email)


# ============================================
# RESEND VERIFICATION EMAIL
# ============================================

@bp.route('/resend-verification', methods=['GET', 'POST'])
@login_required
def resend_verification():
    """Resend verification email"""
    
    if current_user.email_verified:
        flash('Email already verified.', 'info')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        result = current_user.resend_verification_email()
        
        if result['success']:
            # Send email
            EmailService.send_verification_email(current_user, current_user.verification_token)
            flash('Verification email sent. Please check your inbox.', 'success')
            return redirect(url_for('auth.verification_sent', email=current_user.email))
        else:
            flash(result['message'], 'danger')
    
    return render_template('auth/resend_verification.html')


# ============================================
# VERIFICATION SUCCESS PAGE
# ============================================

@bp.route('/verification-success')
def verification_success():
    """Email verification success page"""
    return render_template('auth/verification_success.html')


# ============================================
# VERIFICATION REQUIRED DECORATOR (Optional)
# ============================================

def verification_required(f):
    """Decorator to require email verification"""
    from functools import wraps
    from flask import abort
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.email_verified:
            flash('Please verify your email address to access this feature.', 'warning')
            return redirect(url_for('auth.resend_verification'))
        
        return f(*args, **kwargs)
    
    return decorated_function