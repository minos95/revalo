#-----------------------------------admin routes
from flask import  render_template,Blueprint
from flask_login import login_required
from sqlalchemy import Transaction

from app.auth.models import Company, User
from app.listings.models import Item

app= Blueprint('admin', __name__, url_prefix='/admin',template_folder='templates')

@app.route("/admin")
@login_required
def admin_page():
   users_count=User.query.count()
   companies_count=Company.query.count()
   listings_count=Item.query.count()
   transactions_count=Transaction.query.count()
   return render_template('admin/dashboard.html',users_count=users_count,companies_count=companies_count,listings_count=listings_count,transactions_count=transactions_count)

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