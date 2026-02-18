from revelo_package import app
from flask import render_template
from revelo_package.models import Item 
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

@app.route("/contact")
def contact_page():
    return render_template('contact.html')

@app.route("/signup")
def signup_page():
    return render_template('signup.html')

@app.route("/signin")
def signin_page():
    return render_template('signin.html')
