import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from extensions import mail  # Import the global mail object
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
login_manager.login_view="home"
login_manager.login_message_category='info'
migrate = Migrate(app, db)

    
# Email Server Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'rahal.aminos@gmail.com'
app.config['MAIL_PASSWORD'] = 'dwad wryg hysx mizb'
app.config['MAIL_DEFAULT_SENDER'] =  ('Ecowaste', 'rahal.aminos@gmail.com')

mail.init_app(app)


#Register blueprint
from app.auth import bp as auth_bp
from app.listings import bp as listings_bp
from app.offers import bp as offers_bp
from app.transactions import bp as transactions_bp
from app.admin import bp as admin_bp
from app.messages import bp as messages_bp
from app.subscription import bp as subscription_bp
app.register_blueprint(subscription_bp)
app.register_blueprint(messages_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(listings_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(offers_bp)
from app.context_processors import inject_notifications, inject_notification_service
# Register context processors for notifications
app.context_processor(inject_notifications)
app.context_processor(inject_notification_service)
from app import routes

