from flask import Blueprint

bp = Blueprint('offers', __name__, url_prefix='/offers', template_folder='templates')

from app.offers import routes