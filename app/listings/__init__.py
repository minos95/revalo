from flask import Blueprint

bp = Blueprint('listings', __name__, url_prefix='/listings', template_folder='templates')

from app.listings import routes