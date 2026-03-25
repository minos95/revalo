import os
from app import app,db
from flask import render_template,request
from app.auth.models import Company, User
from app.listings.models import Category,Item, Quality_attributes
from app.models import Offer,Transaction
from app.forms import  rejectOfferForm,validateOfferForm,cancelOfferForm


from flask_login import login_required,current_user
from sqlalchemy import desc,or_
from datetime import datetime

@app.route("/")
def home_page():

    recent_listings=Item.query.order_by(desc(Item.created_at)).limit(4).all()
    categories=Category.query.all()
    featured_companies=Company.query.limit(5).all()
    total_listings=Item.query.count()
    total_companies=Company.query.count()
    total_transactions=Transaction.query.count()
    return render_template('home2.html',recent_listings=recent_listings,categories=categories,featured_companies=featured_companies,total_companies=total_companies,total_listings=total_listings,total_transactions=total_transactions)

'''@app.route("/dashboard")
def dashboard_page():
    listings=Item.query.filter_by(company_id=current_user.company_id).limit(5).all()
    listings_count=Item.query.filter_by(company_id=current_user.company_id).count()
    offers_sent_count=Offer.query.filter_by(buyer_company_id=current_user.company_id).count()
    offers_received_count=Offer.query.filter_by(buyer_company_id=current_user.company_id).count()
    buying_count = Transaction.query.filter_by( buyer_company_id = current_user.company_id ).count()
    selling_count = Transaction.query.filter_by( seller_company_id = current_user.company_id ).count()
    return render_template('dashboard.html',listings=listings,listings_count=listings_count,offers_received_count=offers_received_count,offers_sent_count=offers_sent_count,buying_count=buying_count,selling_count=selling_count)
'''


@app.route("/transactions")
def transactions_page():
    transactions=Transaction.query.filter(or_(Transaction.seller_company_id==current_user.id ,Transaction.buyer_company_id==current_user.company_id)).all()
    print(transactions)
    return render_template('transactions.html',transactions=transactions)
@app.route("/offers",methods=['POST','GET'])
def offers_page():
    
    offers_sent=Offer.query.filter_by(buyer_company_id=current_user.company_id).order_by(desc(Offer.created_at)).all()
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
        seller_net_amount=total_amount-commission_amount
        transaction_to_create=Transaction(offer_id=validate_form.id.data,
                                          item_id=validate_form.item_id.data,
                                          price=validate_form.price.data,
                                          quantity=validate_form.quantity.data,
                                          unit=validate_form.unit.data,
                                          buyer_company_id=validate_form.buyer_company_id.data,
                                          seller_company_id=validate_form.seller_company_id.data,
                                         
                                          total_amount=total_amount,
                                          commission_amount=commission_amount,
                                          seller_net_amount=seller_net_amount
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

    return render_template('offers.html',offers_sent=offers_sent,offers_received=offers_received,validate_form=validate_form,cancel_form=cancel_form,reject_form=reject_form)


@app.route("/contact")
def contact_page():
    return render_template('contact.html')



@app.route("/admin/offers")
@login_required
def admin_offers_page():
   offers=Offer.query.all()
   return render_template('admin/offers.html',offers=offers)

@app.route("/admin/companies")
@login_required
def admin_companies_page():
    companies = Company.query.all()
   
    return render_template("admin/companies.html", companies=companies)

@app.route("/admin/listings")
@login_required
def admin_listings_page():
    listings = Item.query.all()
    return render_template("admin/listings.html", listings=listings)

@app.route("/admin/transactions")
@login_required
def admin_transactions_page():
   transactions=Transaction.query.all()
   return  render_template('admin/transactions.html',transactions=transactions)