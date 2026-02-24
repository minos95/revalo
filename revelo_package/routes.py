from revelo_package import app,db
from flask import render_template,redirect,url_for,flash
from revelo_package.models import Item,User,Company
from revelo_package.forms import CompanyRegisterForm ,UserRegisterForm,postItemForm,LoginForm
from flask_login import login_user 
@app.route("/")
def home_page():
    return render_template('home.html')
@app.route("/market")
def market_page():
    items=Item.query.all()
    return render_template('market.html',items=items)
@app.route("/summary")
def summary_page():
    return render_template('summary.html')
@app.route("/bids")
def bids_page():
    return render_template('bids.html')

@app.route("/listing")
def listing_page():
    return render_template('listing.html')
@app.route('/listing/post',methods=['GET','POST'])
def post_page():
    form=postItemForm()
    if form.validate_on_submit():
        print('+++++++++++++++++++++')
        print(form.category.data)
        item_to_create=Item(name=form.name.data,
                            description=form.description.data,
                            category_id=form.category.data,
                            unit=form.unit.data,
                            quantity=form.quantity.data,
                            location=form.location.data,
                            price=form.price.data,
                            )
        db.session.add(item_to_create)
        db.session.commit()
        return redirect(url_for(('listing_page')))
    return render_template('post_item.html',form=form)

@app.route("/contact")
def contact_page():
    return render_template('contact.html')

@app.route("/signup",methods=['GET','POST'])
def signup_page():
    form=CompanyRegisterForm()
    if form.validate_on_submit():
        company_to_create=Company(name=form.name.data,
                                  company_type=form.company_type.data,
                                  activity=form.activity.data,
                                  address=form.address.data,
                                  country=form.country.data,
                                  city=form.city.data,
                                  rc=form.rc.data,
                                  nif=form.rc.data,
                                  nis=form.nis.data)
        db.session.add(company_to_create)
        db.session.commit()
        company_created=Company.query.filter_by(name=form.name.data).first().id
        user_to_create=User(full_name=form.full_name.data,
                            email=form.email.data,
                            phone=form.phone.data,
                            role=form.role.data,
                            password=form.password1.data,
                            company_id=company_created)
        db.session.add(user_to_create)
        db.session.commit()
        return redirect(url_for('home_page'))
    if form.errors!={}:
        for err_msg in form.errors.values():
            flash(f'error {err_msg}',category='danger')
    return render_template('signup.html',form=form)

@app.route("/login")
def login_page():
   
   form=LoginForm()
   if form.validate_on_submit():
       attempted_user=User.query.get(form.email.data).first()
       if attempted_user and attempted_user.check_password_corection(
           attempted_password=form.password.data):
           login_user(attempted_user)
           flash("success you are logged in",category='success')
           return redirect(url_for('market_page'))
       else:
           flash('Username or password are incorrect! please try again',category='danger')

        
   return render_template('login.html',form=form)
