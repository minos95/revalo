from flask import Blueprint

bp = Blueprint('messages', __name__, url_prefix='/messages', template_folder='templates')

from app.messages import routes