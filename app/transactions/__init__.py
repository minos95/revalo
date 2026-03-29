from flask import Blueprint

bp = Blueprint('transactions', __name__, url_prefix='/transactions', template_folder='templates')

from app.transactions import routes