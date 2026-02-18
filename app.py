from flask import Flask,render_template

app = Flask(__name__)

@app.route("/")
def home_page():
    return render_template('home.html')
@app.route("/market")
def market_page():
    items=[{'id':1,'name':'lot de zinc','description':'description de lot','location':'oran','category':'zinc','subcategory':'pe','price':50,'added_date':'14-01-01'}]
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


if __name__ == "__main__":
    app.run()