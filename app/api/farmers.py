# 🔧 Fixed app/api/farmers.py

"""Farmer-specific API endpoints."""

from flask import request, jsonify
from app.api import bp
from app.models.user import Farmer, UserRole
from app.models.animal import Animal, HealthRecord
from app.services.animal_service import AnimalService
from app.utils.decorators import auth_required, admin_required, farmer_required
from app.utils.helpers import success_response, error_response, paginate_query
from app import db


@bp.route('/farmers', methods=['GET'])
@admin_required
def list_farmers(current_user):
    """List all farmers (admin only)."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search')
    
    query = Farmer.query.filter_by(is_active=True)
    
    # Search by name, email, or farm name
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Farmer.name.ilike(search_term)) | 
            (Farmer.email.ilike(search_term)) |
            (Farmer.farm_name.ilike(search_term))
        )
    
    # Order by creation date
    query = query.order_by(Farmer.created_at.desc())
    
    # Paginate results
    pagination = paginate_query(query, page, per_page)
    
    # Add animal count for each farmer
    farmers_data = []
    for farmer in pagination['items']:
        farmer_dict = farmer.to_dict()
        
        # Get animal counts
        total_animals = Animal.query.filter_by(farmer_id=farmer.id, is_active=True).count()
        healthy_animals = Animal.query.filter_by(
            farmer_id=farmer.id, 
            is_active=True, 
            health_status='healthy'
        ).count()
        
        farmer_dict['animal_count'] = total_animals
        farmer_dict['healthy_animals'] = healthy_animals
        farmers_data.append(farmer_dict)
    
    return success_response(
        "Farmers retrieved successfully",
        data={
            'farmers': farmers_data,
            'pagination': {
                'page': pagination['page'],
                'per_page': pagination['per_page'],
                'total': pagination['total'],
                'pages': pagination['pages'],
                'has_next': pagination['has_next'],
                'has_prev': pagination['has_prev']
            }
        }
    )


@bp.route('/farmers/<farmer_id>', methods=['GET'])
@auth_required
def get_farmer(current_user, farmer_id):
    """Get farmer details."""
    # Farmers can only view their own profile, admins can view any
    if current_user.user_type == UserRole.FARMER:
        if str(current_user.id) != farmer_id:
            return error_response("Access denied", status_code=403)
    elif current_user.user_type not in [UserRole.ADMIN, UserRole.VETERINARIAN]:
        return error_response("Access denied", status_code=403)
    
    farmer = Farmer.query.filter_by(id=farmer_id, is_active=True).first()
    if not farmer:
        return error_response("Farmer not found", status_code=404)
    
    farmer_data = farmer.to_dict()
    
    # Get animal counts
    total_animals = Animal.query.filter_by(farmer_id=farmer.id, is_active=True).count()
    healthy_animals = Animal.query.filter_by(
        farmer_id=farmer.id, 
        is_active=True, 
        health_status='healthy'
    ).count()
    
    farmer_data['animal_count'] = total_animals
    farmer_data['healthy_animals'] = healthy_animals
    
    return success_response("Farmer retrieved successfully", data=farmer_data)


@bp.route('/farmers/<farmer_id>/animals', methods=['GET'])
@auth_required
def get_farmer_animals(current_user, farmer_id):
    """Get animals for a specific farmer."""
    # Access control
    if current_user.user_type == UserRole.FARMER:
        if str(current_user.id) != farmer_id:
            return error_response("Access denied", status_code=403)
    elif current_user.user_type not in [UserRole.ADMIN, UserRole.VETERINARIAN]:
        return error_response("Access denied", status_code=403)
    
    farmer = Farmer.query.filter_by(id=farmer_id, is_active=True).first()
    if not farmer:
        return error_response("Farmer not found", status_code=404)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    species = request.args.get('species')
    health_status = request.args.get('health_status')
    
    query = Animal.query.filter_by(farmer_id=farmer_id, is_active=True)
    
    # Apply filters
    if species:
        from app.models.animal import AnimalSpecies
        try:
            species_enum = AnimalSpecies(species.lower())
            query = query.filter_by(species=species_enum)
        except ValueError:
            return error_response("Invalid species", status_code=400)
    
    if health_status:
        from app.models.animal import HealthStatus
        try:
            health_enum = HealthStatus(health_status.lower())
            query = query.filter_by(health_status=health_enum)
        except ValueError:
            return error_response("Invalid health status", status_code=400)
    
    # Order by creation date
    query = query.order_by(Animal.created_at.desc())
    
    # Paginate results
    pagination = paginate_query(query, page, per_page)
    
    return success_response(
        "Farmer animals retrieved successfully",
        data={
            'farmer': farmer.to_dict(),
            'animals': [animal.to_dict() for animal in pagination['items']],
            'pagination': {
                'page': pagination['page'],
                'per_page': pagination['per_page'],
                'total': pagination['total'],
                'pages': pagination['pages'],
                'has_next': pagination['has_next'],
                'has_prev': pagination['has_prev']
            }
        }
    )


@bp.route('/farmers/<farmer_id>/dashboard', methods=['GET'])
@auth_required
def get_farmer_dashboard(current_user, farmer_id):
    """Get farmer dashboard data."""
    # Access control
    if current_user.user_type == UserRole.FARMER:
        if str(current_user.id) != farmer_id:
            return error_response("Access denied", status_code=403)
    elif current_user.user_type not in [UserRole.ADMIN]:
        return error_response("Access denied", status_code=403)
    
    farmer = Farmer.query.filter_by(id=farmer_id, is_active=True).first()
    if not farmer:
        return error_response("Farmer not found", status_code=404)
    
    # Get animal summary
    summary, error_msg = AnimalService.get_farmer_animals_summary(farmer_id)
    if not summary:
        return error_response(error_msg, status_code=500)
    
    # Get recent health records for farmer's animals
    recent_health_records = db.session.query(HealthRecord).join(Animal).filter(
        Animal.farmer_id == farmer_id,
        Animal.is_active == True,
        HealthRecord.is_active == True
    ).order_by(HealthRecord.created_at.desc()).limit(10).all()
    
    # Get animals needing attention
    from app.models.animal import HealthStatus
    attention_statuses = [HealthStatus.SICK, HealthStatus.UNDER_TREATMENT, HealthStatus.QUARANTINE]
    animals_needing_attention = Animal.query.filter(
        Animal.farmer_id == farmer_id,
        Animal.health_status.in_(attention_statuses),
        Animal.is_active == True
    ).all()
    
    dashboard_data = {
        'farmer': farmer.to_dict(),
        'animal_summary': summary,
        'recent_health_records': [record.to_dict() for record in recent_health_records],
        'animals_needing_attention': [animal.to_dict() for animal in animals_needing_attention],
        'total_animals': summary['total_animals'],
        'healthy_animals': summary['healthy_animals'],
        'alerts_count': len(animals_needing_attention)
    }
    
    return success_response("Farmer dashboard data retrieved successfully", data=dashboard_data)