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
