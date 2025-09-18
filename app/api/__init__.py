"""API blueprint initialization."""
from flask import Blueprint
bp = Blueprint('api', __name__)

# Import API routes
from app.api import users, animals, farmers, vets