import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
# ... your existing code (Flask app, db = SQLAlchemy(app), etc.)
metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s"
})

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'   
app.config['SECRET_KEY']='fb0dcdeb3a4223be7c444a52'
UPLOAD_FOLDER="app/static/uploads/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"]=UPLOAD_FOLDER
ALLOWED_EXTENSIONS = { 'pdf', 'png', 'jpg', 'jpeg'}
db=SQLAlchemy(app,metadata=metadata)
bcrypt=Bcrypt(app)
login_manager=LoginManager(app)
login_manager.login_view="home_page"
login_manager.login_message_category='info'
migrate = Migrate(app, db)

#Register blueprint
from app.auth import bp as auth_bp
from app.listings import bp as listings_bp
from app.offers import bp as offers_bp
from app.transactions import bp as transactions_bp

app.register_blueprint(auth_bp)
app.register_blueprint(listings_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(offers_bp)


from app import routes
from app import dashboard_route
