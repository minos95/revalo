import os
from app import app,db
from flask import render_template,request
from app.auth.models import Company, User
from app.listings.models import Category,Item, Quality_attributes
from app.transactions.models import Transaction


from flask_login import login_required,current_user
from sqlalchemy import desc,or_
from datetime import datetime

from app.offers.models import Offer

@app.route("/")
def home():

    recent_listings=Item.query.order_by(desc(Item.created_at)).limit(4).all()
    categories=Category.query.all()
    featured_companies=Company.query.limit(5).all()
    total_listings=Item.query.count()
    total_companies=Company.query.count()
    total_transactions=Transaction.query.count()
    return render_template('home.html',recent_listings=recent_listings,categories=categories,featured_companies=featured_companies,total_companies=total_companies,total_listings=total_listings,total_transactions=total_transactions)

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