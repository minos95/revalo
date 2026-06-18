import app
from flask import Blueprint, flash,redirect,render_template, request,url_for
from app import db
from app.auth import bp
from flask_login import current_user, login_required, login_user, logout_user
from app.auth.forms import CompanyRegisterForm, ForgotPasswordForm, LoginForm, ResetPasswordForm
from app.auth.models import Notification, User
from app.auth.models import Company
from flask_mail import  Message
from extensions import mail  # <-- CRITICAL: Import the same mail object here


@bp.route("/signup",methods=['GET','POST'])
def signup():
    form=CompanyRegisterForm()
    if form.validate_on_submit():
        company_to_create=Company(name=form.company_name.data,
                                  company_type=form.business_type.data,
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
        
        company_created=Company.query.filter_by(name=form.company_name.data).first().id
        user_to_create=User(full_name=form.full_name.data,
                            email=form.email.data,
                            phone=form.phone.data,
                            role=form.role.data,
                            password=form.password.data,
                            company_id=company_created)
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
        db.session.add(user_to_create)
        db.session.commit()
        return redirect(url_for('home'))
    if form.errors!={}:
        for field,err_msg in form.errors.items():
            flash(f'error {getattr(form, field).label.text}: {err_msg}',category='danger')
    return render_template('register.html',form=form)

@bp.route("/login",methods=['GET','POST'])
def login():
   
   
   form=LoginForm()
   if form.validate_on_submit():
       attempted_user=User.query.filter_by(email=form.email.data).first()
       if attempted_user  and attempted_user.check_password_correction(
           attempted_password=form.password.data):
           if  attempted_user.owned_company.verified:
            login_user(attempted_user)
            flash("success you are logged in",category='success')
            return redirect(url_for('dashboard'))
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
@bp.route("/settings/company", methods=["POST"])
@login_required
def update_company():

    company = Company.query.get(current_user.company_id)

    company.name = request.form["company_name"]
    company.description = request.form["description"]

    db.session.commit()

    return redirect(url_for("setting"))

@bp.route("/settings/profile", methods=["POST"])
@login_required
def update_profile():

    user = User.query.get(current_user.id) 
    print(user)
    user.full_name = request.form["name"]
    user.email = request.form["email"]
    user.email_verified=False
    db.session.commit()

    return redirect(url_for("setting"))




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
        print('---------------------------------')
        mail.send(msg)
    except Exception as e:
        print('-----------------------------------')
        print(f'Failed to send reset email: {str(e)}')