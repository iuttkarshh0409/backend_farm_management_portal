"""Main application routes."""

from flask import jsonify
from app.main import bp


@bp.route('/')
def index():
    """Application root endpoint."""
    return jsonify({
        'message': 'Welcome to Farm Management Portal API',
        'version': '1.0.0',
        'status': 'active',
        'endpoints': {
            'health': '/health',
            'api': '/api/v1/',
            'auth': '/api/v1/auth/',
        }
    })


@bp.route('/status')
def status():
    """Application status endpoint."""
    return jsonify({
        'status': 'running',
        'environment': 'development',
        'database': 'connected'
    })

@bp.route('/debug/routes')
def list_routes():
    from flask import current_app
    routes = []
    for rule in current_app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': rule.rule
        })
    return jsonify({'routes': routes})

@bp.route('/debug/test-registration')
def test_registration():
    return jsonify({
        "message": "Registration endpoint exists!",
        "expected_url": "/api/v1/users/register/farmer"
    })

