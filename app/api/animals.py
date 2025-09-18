# 🔧 Fixed app/api/animals.py

"""Animal management API endpoints."""

from flask import request, jsonify
from app.api import bp
from app.models.animal import Animal, HealthRecord, AnimalSpecies, HealthStatus
from app.models.user import Farmer, Veterinarian, UserRole
from app.services.animal_service import AnimalService
from app.utils.decorators import auth_required, admin_required, role_required, farmer_required, vet_required
from app.utils.helpers import success_response, error_response, handle_db_error, paginate_query
from app.utils.validators import validate_required_fields
from app import db


@bp.route('/animals', methods=['POST'])
@auth_required
@handle_db_error
def create_animal(current_user):
    """Create a new animal (farmer only)."""
    # Only farmers can create animals, or admins on behalf of farmers
    if current_user.user_type == UserRole.FARMER:
        farmer_id = current_user.id
    elif current_user.user_type == UserRole.ADMIN:
        data = request.get_json()
        farmer_id = data.get('farmer_id')
        if not farmer_id:
            return error_response("farmer_id is required for admin users", status_code=400)
    else:
        return error_response("Only farmers and admins can create animals", status_code=403)
    
    data = request.get_json()
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Create animal using service
    animal, error_msg = AnimalService.create_animal(data, farmer_id)
    
    if not animal:
        return error_response(error_msg, status_code=400)
    
    return success_response(
        message="Animal registered successfully",
        data={'animal': animal.to_dict()},
        status_code=201
    )


@bp.route('/animals', methods=['GET'])
@auth_required
def list_animals(current_user):
    """List animals based on user role and filters."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    species = request.args.get('species')
    health_status = request.args.get('health_status')
    search = request.args.get('search')
    
    # Build query based on user role
    if current_user.user_type == UserRole.FARMER:
        # Farmers can only see their own animals
        query = Animal.query.filter_by(farmer_id=current_user.id, is_active=True)
    elif current_user.user_type == UserRole.VETERINARIAN:
        # Vets can see animals assigned to them
        query = Animal.query.filter_by(veterinarian_id=current_user.id, is_active=True)
    elif current_user.user_type == UserRole.ADMIN:
        # Admins can see all animals
        query = Animal.query.filter_by(is_active=True)
        # Admin can filter by farmer
        farmer_id = request.args.get('farmer_id')
        if farmer_id:
            query = query.filter_by(farmer_id=farmer_id)
    else:
        return error_response("Unauthorized access", status_code=403)
    
    # Apply filters
    if species:
        try:
            species_enum = AnimalSpecies(species.lower())
            query = query.filter_by(species=species_enum)
        except ValueError:
            return error_response("Invalid species", status_code=400)
    
    if health_status:
        try:
            health_enum = HealthStatus(health_status.lower())
            query = query.filter_by(health_status=health_enum)
        except ValueError:
            return error_response("Invalid health status", status_code=400)
    
    # Search by tag ID or name
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Animal.tag_id.ilike(search_term)) | 
            (Animal.name.ilike(search_term))
        )
    
    # Order by creation date
    query = query.order_by(Animal.created_at.desc())
    
    # Paginate results
    pagination = paginate_query(query, page, per_page)
    
    return success_response(
        "Animals retrieved successfully",
        data={
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


@bp.route('/animals/<animal_id>', methods=['GET'])
@auth_required
def get_animal(current_user, animal_id):
    """Get specific animal details."""
    animal = Animal.query.filter_by(id=animal_id, is_active=True).first()
    if not animal:
        return error_response("Animal not found", status_code=404)
    
    # Check access permissions
    if current_user.user_type == UserRole.FARMER:
        if str(animal.farmer_id) != str(current_user.id):
            return error_response("Access denied", status_code=403)
    elif current_user.user_type == UserRole.VETERINARIAN:
        if str(animal.veterinarian_id) != str(current_user.id):
            return error_response("Access denied", status_code=403)
    # Admins can access any animal
    
    return success_response("Animal retrieved successfully", data=animal.to_dict())


@bp.route('/animals/<animal_id>', methods=['PUT'])
@auth_required
@handle_db_error
def update_animal(current_user, animal_id):
    """Update animal profile."""
    animal = Animal.query.filter_by(id=animal_id, is_active=True).first()
    if not animal:
        return error_response("Animal not found", status_code=404)
    
    # Check access permissions
    if current_user.user_type == UserRole.FARMER:
        if str(animal.farmer_id) != str(current_user.id):
            return error_response("Access denied", status_code=403)
    elif current_user.user_type == UserRole.VETERINARIAN:
        if str(animal.veterinarian_id) != str(current_user.id):
            return error_response("Access denied", status_code=403)
    # Admins can update any animal
    
    data = request.get_json()
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Update animal using service
    updated_animal, message = AnimalService.update_animal_profile(animal_id, data, current_user.id)
    
    if updated_animal:
        return success_response(message, data=updated_animal.to_dict())
    else:
        return error_response(message, status_code=400)


@bp.route('/animals/<animal_id>/assign-vet', methods=['POST'])
@auth_required
@handle_db_error
def assign_veterinarian(current_user, animal_id):
    """Assign veterinarian to animal (farmer or admin only)."""
    if current_user.user_type not in [UserRole.FARMER, UserRole.ADMIN]:
        return error_response("Only farmers and admins can assign veterinarians", status_code=403)
    
    animal = Animal.query.filter_by(id=animal_id, is_active=True).first()
    if not animal:
        return error_response("Animal not found", status_code=404)
    
    # Farmers can only assign vets to their own animals
    if current_user.user_type == UserRole.FARMER:
        if str(animal.farmer_id) != str(current_user.id):
            return error_response("Access denied", status_code=403)
    
    data = request.get_json()
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Validate required fields
    valid, missing = validate_required_fields(data, ['veterinarian_id'])
    if not valid:
        return error_response("Missing required fields", errors=missing, status_code=400)
    
    vet_id = data['veterinarian_id']
    
    # Assign veterinarian using service
    updated_animal, error_msg = AnimalService.assign_veterinarian(animal_id, vet_id, current_user.id)
    
    if updated_animal:
        return success_response(
            "Veterinarian assigned successfully",
            data=updated_animal.to_dict()
        )
    else:
        return error_response(error_msg, status_code=400)


@bp.route('/animals/<animal_id>/health-records', methods=['POST'])
@auth_required
@handle_db_error
def create_health_record(current_user, animal_id):
    """Create health record for animal (vet or admin only)."""
    if current_user.user_type not in [UserRole.VETERINARIAN, UserRole.ADMIN]:
        return error_response("Only veterinarians and admins can create health records", status_code=403)
    
    animal = Animal.query.filter_by(id=animal_id, is_active=True).first()
    if not animal:
        return error_response("Animal not found", status_code=404)
    
    # Vets can only create records for animals assigned to them
    if current_user.user_type == UserRole.VETERINARIAN:
        if str(animal.veterinarian_id) != str(current_user.id):
            return error_response("Access denied. Animal not assigned to you", status_code=403)
    
    data = request.get_json()
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Add animal_id to data
    data['animal_id'] = animal_id
    
    # Create health record using service
    health_record, error_msg = AnimalService.create_health_record(data, current_user.id)
    
    if health_record:
        return success_response(
            "Health record created successfully",
            data=health_record.to_dict(),
            status_code=201
        )
    else:
        return error_response(error_msg, status_code=400)


@bp.route('/animals/<animal_id>/health-records', methods=['GET'])
@auth_required
def get_animal_health_records(current_user, animal_id):
    """Get health records for an animal."""
    animal = Animal.query.filter_by(id=animal_id, is_active=True).first()
    if not animal:
        return error_response("Animal not found", status_code=404)
    
    # Check access permissions
    if current_user.user_type == UserRole.FARMER:
        if str(animal.farmer_id) != str(current_user.id):
            return error_response("Access denied", status_code=403)
    elif current_user.user_type == UserRole.VETERINARIAN:
        if str(animal.veterinarian_id) != str(current_user.id):
            return error_response("Access denied", status_code=403)
    # Admins can access any records
    
    limit = request.args.get('limit', 10, type=int)
    health_records, error_msg = AnimalService.get_animal_health_history(animal_id, limit)
    
    if health_records is not None:
        return success_response(
            "Health records retrieved successfully",
            data={
                'animal': animal.to_dict(),
                'health_records': [record.to_dict() for record in health_records]
            }
        )
    else:
        return error_response(error_msg, status_code=500)


@bp.route('/animals/<animal_id>', methods=['DELETE'])
@auth_required
@handle_db_error
def delete_animal(current_user, animal_id):
    """Soft delete animal (farmer or admin only)."""
    if current_user.user_type not in [UserRole.FARMER, UserRole.ADMIN]:
        return error_response("Only farmers and admins can delete animals", status_code=403)
    
    animal = Animal.query.filter_by(id=animal_id, is_active=True).first()
    if not animal:
        return error_response("Animal not found", status_code=404)
    
    # Farmers can only delete their own animals
    if current_user.user_type == UserRole.FARMER:
        if str(animal.farmer_id) != str(current_user.id):
            return error_response("Access denied", status_code=403)
    
    # Delete animal using service
    deleted_animal, message = AnimalService.deactivate_animal(animal_id, "Deleted by user", current_user.id)
    
    if deleted_animal:
        return success_response(message)
    else:
        return error_response(message, status_code=500)


@bp.route('/farmers/<farmer_id>/animals/summary', methods=['GET'])
@auth_required
def get_farmer_animals_summary(current_user, farmer_id):
    """Get animal summary for a farmer."""
    # Access control
    if current_user.user_type == UserRole.FARMER:
        if str(current_user.id) != farmer_id:
            return error_response("Access denied", status_code=403)
    elif current_user.user_type not in [UserRole.ADMIN, UserRole.VETERINARIAN]:
        return error_response("Access denied", status_code=403)
    
    summary, error_msg = AnimalService.get_farmer_animals_summary(farmer_id)
    
    if summary:
        return success_response("Animals summary retrieved successfully", data=summary)
    else:
        return error_response(error_msg, status_code=404 if "not found" in error_msg else 500)


@bp.route('/veterinarians/<vet_id>/animals', methods=['GET'])
@auth_required
def get_vet_assigned_animals(current_user, vet_id):
    """Get animals assigned to a veterinarian."""
    # Vets can only see their own assignments, admins can see any
    if current_user.user_type == UserRole.VETERINARIAN:
        if str(current_user.id) != vet_id:
            return error_response("Access denied", status_code=403)
    elif current_user.user_type != UserRole.ADMIN:
        return error_response("Access denied", status_code=403)
    
    summary, error_msg = AnimalService.get_vet_assigned_animals(vet_id)
    
    if summary:
        # Convert animals to dict for JSON response
        summary['animals'] = [animal.to_dict() for animal in summary['animals']]
        
        # Convert animals_by_status to dict
        for status, animals in summary['animals_by_status'].items():
            summary['animals_by_status'][status] = [animal.to_dict() for animal in animals]
        
        return success_response("Assigned animals retrieved successfully", data=summary)
    else:
        return error_response(error_msg, status_code=404 if "not found" in error_msg else 500)


@bp.route('/animals/search', methods=['GET'])
@auth_required
def search_animals(current_user):
    """Search animals with various filters."""
    search_params = {
        'species': request.args.get('species'),
        'health_status': request.args.get('health_status'),
        'search': request.args.get('search'),
        'order_by': request.args.get('order_by', 'created_at')
    }
    
    # Add user-specific filters
    if current_user.user_type == UserRole.FARMER:
        search_params['farmer_id'] = current_user.id
    elif current_user.user_type == UserRole.VETERINARIAN:
        search_params['veterinarian_id'] = current_user.id
    elif current_user.user_type == UserRole.ADMIN:
        # Admin can specify farmer_id in query
        farmer_id = request.args.get('farmer_id')
        if farmer_id:
            search_params['farmer_id'] = farmer_id
    
    animals, error_msg = AnimalService.search_animals(search_params)
    
    if animals is not None:
        return success_response(
            "Animals search completed",
            data={
                'animals': [animal.to_dict() for animal in animals],
                'total': len(animals)
            }
        )
    else:
        return error_response(error_msg, status_code=400)


@bp.route('/animals/stats', methods=['GET'])
@admin_required
def get_animals_stats(current_user):
    """Get animal statistics (admin only)."""
    try:
        # Overall statistics
        total_animals = Animal.query.filter_by(is_active=True).count()
        
        # By species
        species_stats = {}
        for species in AnimalSpecies:
            count = Animal.query.filter_by(species=species, is_active=True).count()
            species_stats[species.value] = count
        
        # By health status
        health_stats = {}
        for status in HealthStatus:
            count = Animal.query.filter_by(health_status=status, is_active=True).count()
            health_stats[status.value] = count
        
        # Animals needing attention
        attention_statuses = [HealthStatus.SICK, HealthStatus.UNDER_TREATMENT, HealthStatus.QUARANTINE]
        animals_needing_attention = Animal.query.filter(
            Animal.health_status.in_(attention_statuses),
            Animal.is_active == True
        ).count()
        
        # Animals without assigned vet
        unassigned_animals = Animal.query.filter_by(
            veterinarian_id=None,
            is_active=True
        ).count()
        
        stats = {
            'total_animals': total_animals,
            'species_breakdown': species_stats,
            'health_status_breakdown': health_stats,
            'animals_needing_attention': animals_needing_attention,
            'unassigned_animals': unassigned_animals,
            'healthy_animals': health_stats.get('healthy', 0)
        }
        
        return success_response("Animal statistics retrieved successfully", data=stats)
    
    except Exception as e:
        return error_response(f"Failed to get statistics: {str(e)}", status_code=500)