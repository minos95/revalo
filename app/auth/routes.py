from flask import Blueprint, flash,redirect,render_template, request,url_for
from app import db
from app.auth import bp
from flask_login import current_user, login_required, login_user, logout_user
from app.auth.forms import CompanyRegisterForm, LoginForm
from app.auth.models import User
from app.auth.models import Company




@bp.route("/signup",methods=['GET','POST'])
def signup():
    form=CompanyRegisterForm()
    if form.validate_on_submit():
        company_to_create=Company(name=form.company_name.data,
                                  company_type=form.business_type.data,
                                  activity=form.company_activity.data,
                                  address=form.address.data,
                                  country=form.country.data,
                                  phone=form.company_phone,
                                  city=form.city.data,
                                  rc=form.rc.data,
                                  nif=form.rc.data,
                                  nis=form.nis.data)
        db.session.add(company_to_create)
        
        company_created=Company.query.filter_by(name=form.company_name.data).first().id
        user_to_create=User(full_name=form.full_name.data,
                            email=form.email.data,
                            phone=form.phone.data,
                            role=form.role.data,
                            password=form.password.data,
                            company_id=company_created)
        db.session.add(user_to_create)
        db.session.commit()
        return redirect(url_for('home'))
    if form.errors!={}:
        for err_msg in form.errors.values():
            flash(f'error {err_msg}',category='danger')
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
