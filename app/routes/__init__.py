# Routes package
from flask import Blueprint

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return "✅ Flask app is running!"
