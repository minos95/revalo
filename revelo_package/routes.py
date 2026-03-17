import os
from revelo_package import app,db
from flask import render_template,redirect,url_for,flash,request
from revelo_package.models import Item,User,Company,Offer,Transaction,Category,Quality_attributes,Item_quality_values,Image
from revelo_package.forms import CompanyRegisterForm ,UserRegisterForm,postItemForm,LoginForm,FilterMarketForm,makeOfferForm, rejectOfferForm,validateOfferForm,cancelOfferForm
from werkzeug.utils import secure_filename

from flask_login import login_user ,logout_user,login_required,current_user
from sqlalchemy import desc,or_
from datetime import datetime
@app.route("/")
def home_page():
    return render_template('home.html')
@app.route("/market")
def market_category_page():
    categories=Category.query.all()
    return render_template('market_category.html',categories=categories)

@app.route("/market/category/<int:category_id>",methods=['POST','GET'])
#@login_required
def market_page(category_id):
    
    page = request.args.get("page_num", 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    make_offer_form=makeOfferForm()
    
   
    if make_offer_form.validate_on_submit():
        offer_to_create=Offer(offered_price=make_offer_form.price.data,
                              quantity_requested=make_offer_form.quantity.data,
                              message=make_offer_form.message.data,
                              item_id=request.form['item_id'],
                              buyer_company_id=current_user.company_id,
                              buyer_id=current_user.company_id,
                              seller_id=request.form['seller_id'],
                              seller_company_id=request.form['seller_company_id'],
                              unit=request.form['unit']
                              )
        db.session.add(offer_to_create)
        db.session.commit()
        return redirect(url_for("offers_page"))

    filter_form=FilterMarketForm()
    filters=[]
    filters.append(Item.company_id==current_user.company_id)
    if category_id!='all':
        filters.append(Item.category_id==category_id)
    if request.args.get("name"):
        filters.append(Item.name.ilike(f"%{request.args.get("name")}%"))
    if request.args.get("category"):
        filters.append(Item.category_id==request.args.get("category"))
    if request.args.get("quantity"):
        filters.append(request.args.get("quantity")<=Item.quantity)
    if request.args.get("location"):
        filters.append(Item.location==request.args.get("location"))

    if filters:   
            items=Item.query.filter(*filters).paginate(page=page,per_page=per_page,error_out=False)
    else:
            items=Item.query.paginate(page=page,per_page=per_page,error_out=False)

    attributes=Quality_attributes.query.filter_by(category_id=category_id).all()
 
    return render_template('market.html',items=items,filter_form=filter_form,make_offer_form=make_offer_form,category_id=category_id,attributes=attributes)
@app.route("/summary")
def summary_page():
    transactions=Transaction.query.filter(or_(Transaction.seller_company_id==current_user.id ,Transaction.buyer_company_id==current_user.company_id)).all()
    print(transactions)
    return render_template('summary.html',transactions=transactions)
@app.route("/offers",methods=['POST','GET'])
def offers_page():
    
    offers_send=Offer.query.filter_by(buyer_company_id=current_user.company_id).order_by(desc(Offer.created_at)).all()
    offers_received=Offer.query.filter_by(seller_company_id=current_user.company_id).order_by(desc(Offer.created_at)).all()
    validate_form=validateOfferForm()
    cancel_form=cancelOfferForm()
    reject_form=rejectOfferForm()
    #------------------------------------------------ accept offer
    if validate_form.validate_on_submit() and validate_form.submit1.data:
        print('------------------------------validate form')
        offer=Offer.query.filter_by(id=validate_form.id.data).first()
        item=Item.query.filter_by(id=validate_form.item_id.data).first()
        offer.status="accepted"
        offer.accepted_at=datetime.now()
        offers_to_reject=Offer.query.filter(Offer.item_id==validate_form.item_id.data , Offer.id!=validate_form.id.data,Offer.status=="pending" ).all()
        quantity_avalaibale=item.quantity-validate_form.quantity.data
        item.quantity=quantity_avalaibale     
        if quantity_avalaibale==0:
            item.status="solde"
        
        for offer in offers_to_reject:
            if offer.quantity_requested>quantity_avalaibale:
                offer.status="rejected"

        total_amount=validate_form.price.data*validate_form.quantity.data
        commission_amount=total_amount*0.07

        transaction_to_create=Transaction(offer_id=validate_form.id.data,
                                          item_id=validate_form.item_id.data,
                                          price=validate_form.price.data,
                                          quantity=validate_form.quantity.data,
                                          unit=validate_form.unit.data,
                                          buyer_company_id=validate_form.buyer_company_id.data,
                                          seller_company_id=validate_form.seller_company_id.data,
                                          total_amount=total_amount,
                                          commission_amount=commission_amount
                                          )
  
        
       
        db.session.add(transaction_to_create)
        db.session.commit()
    #---------------------------------------------------end validate offer

    #--------------------------------------------------- cancel offer
    if cancel_form.validate_on_submit() and cancel_form.submit2.data:
        offer_to_cancel=Offer.query.filter_by(id=cancel_form.id.data).first()
        offer_to_cancel.status="canceled"
        db.session.commit()
    #---------------------------------------------------end cancel offer
    
    #---------------------------------------------------reject offer
    if reject_form.validate_on_submit() and reject_form.submit3.data:
        offer_to_reject=Offer.query.filter_by(id=reject_form.id.data).first()
        offer_to_reject.status="canceled"
        db.session.commit()

    return render_template('offers.html',offers=offers_send,offers_received=offers_received,validate_form=validate_form,cancel_form=cancel_form,reject_form=reject_form)

@app.route("/listing")
def listing_page():
    items=Item.query.filter_by(company_id=current_user.company_id).order_by(desc(Item.created_at)).all()
    return render_template('listing.html',items=items)
@app.route("/listing/category")
def choose_category_page():
    categories=Category.query.all()
    return render_template('choose_category.html',categories=categories)
    
@app.route('/listing/category/<int:category_id>/post',methods=['GET','POST'])
def post_page(category_id):
    quality_attributes=Quality_attributes.query.filter_by(category_id=category_id).all()
    form=postItemForm()

   
    if form.validate_on_submit():
        print('+++++++++++++++++validate form')
        print(form.pictures)
        
        quality_item_to_create=[]
        image_to_create=[]
        item_to_create=Item(name=form.name.data,
                            company_id=current_user.company_id,
                            user_id=current_user.id,
                            description=form.description.data,
                            category_id=category_id,
                            unit=form.unit.data,
                            quantity=form.quantity.data,
                            location=form.location.data,
                            price=form.price.data,
                            )
        db.session.add(item_to_create)
        db.session.commit()
        for attribute in quality_attributes:
            attr=attribute.name
            quality_item_to_create.append(Item_quality_values(item_id=item_to_create.id,                                                        
                                                       attribute_id=attribute.id,
                                                        option_id=request.form[attr]
                                                        ))
        for picture in form.pictures.data:
            if picture:
                filename = secure_filename(picture.filename)
                file_path=app.config['UPLOAD_FOLDER']+'listings/'
                file_path = os.path.join(file_path, filename)
                print(file_path)
                picture.save(file_path)
                image_to_create.append(Image(item_id=item_to_create.id, 
                                             uri='uploads/listings/'+filename))
        db.session.add_all(image_to_create)
        db.session.add_all(quality_item_to_create)
        db.session.commit()
        return redirect(url_for(('listing_page')))
    if form.errors!={}:
        for err_msg in form.errors.values():
                flash(f'error {err_msg}',category='danger')
    return render_template('post_item.html',form=form,quality_attributes=quality_attributes)

@app.route("/item/<int:item_id>")
def item_detail_page(item_id):
    item=Item.query.filter_by(id=item_id).first()
    for img in item.images:
        print(img.uri)
    #images=Image.filter_by(item_id=item_id)
    #qualities=Item_quality_values(item_id=item_id)
    return render_template('item_detail.html',item=item)

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

@app.route("/login",methods=['GET','POST'])
def login_page():
   
   
   form=LoginForm()
   if form.validate_on_submit():
       attempted_user=User.query.filter_by(email=form.email.data).first()
       if attempted_user and attempted_user.check_password_correction(
           attempted_password=form.password.data):
           login_user(attempted_user)
           flash("success you are logged in",category='success')
           return redirect(url_for('market_page'))
       else:
           flash('Username or password are incorrect! please try again',category='danger')
   return render_template('login.html',form=form)


@app.route("/logout")
def logout_page():
    logout_user()
    flash("You have been logout!",category="info")
    return redirect(url_for('home_page'))
