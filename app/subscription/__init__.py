from flask import Blueprint

bp = Blueprint('subscription', __name__, url_prefix='/subscription', template_folder='templates')

from app.subscription import routes