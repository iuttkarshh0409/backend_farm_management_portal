# 🔧 Fixed app/api/vets.py

"""Veterinarian-specific API endpoints."""

from flask import request, jsonify
from app.api import bp
from app.models.user import Veterinarian, UserRole
from app.models.animal import Animal, HealthRecord
from app.services.animal_service import AnimalService
from app.utils.decorators import auth_required, admin_required, vet_required
from app.utils.helpers import success_response, error_response, paginate_query
from app import db
from datetime import datetime, date, timedelta


@bp.route('/veterinarians', methods=['GET'])
@auth_required
def list_veterinarians(current_user):
    """List veterinarians."""
    # Only admins and farmers can view vet list
    if current_user.user_type not in [UserRole.ADMIN, UserRole.FARMER]:
        return error_response("Access denied", status_code=403)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search')
    specialization = request.args.get('specialization')
    
    query = Veterinarian.query.filter_by(is_active=True, status='active')
    
    # Search by name, email, or clinic name
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Veterinarian.name.ilike(search_term)) | 
            (Veterinarian.email.ilike(search_term)) |
            (Veterinarian.clinic_name.ilike(search_term))
        )
    
    # Filter by specialization
    if specialization:
        query = query.filter(Veterinarian.specialization.ilike(f"%{specialization}%"))
    
    # Order by creation date
    query = query.order_by(Veterinarian.created_at.desc())
    
    # Paginate results
    pagination = paginate_query(query, page, per_page)
    
    # Add assigned animal count for each vet
    vets_data = []
    for vet in pagination['items']:
        vet_dict = vet.to_dict()
        
        # Get assigned animal counts
        assigned_count = Animal.query.filter_by(veterinarian_id=vet.id, is_active=True).count()
        active_treatments = Animal.query.filter_by(
            veterinarian_id=vet.id, 
            is_active=True, 
            health_status='under_treatment'
        ).count()
        
        vet_dict['assigned_animals_count'] = assigned_count
        vet_dict['active_treatments_count'] = active_treatments
        vets_data.append(vet_dict)
    
    return success_response(
        "Veterinarians retrieved successfully",
        data={
            'veterinarians': vets_data,
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


@bp.route('/veterinarians/<vet_id>', methods=['GET'])
@auth_required
def get_veterinarian(current_user, vet_id):
    """Get veterinarian details."""
    # Vets can view their own profile, others need proper access
    if current_user.user_type == UserRole.VETERINARIAN:
        if str(current_user.id) != vet_id:
            return error_response("Access denied", status_code=403)
    elif current_user.user_type not in [UserRole.ADMIN, UserRole.FARMER]:
        return error_response("Access denied", status_code=403)
    
    vet = Veterinarian.query.filter_by(id=vet_id, is_active=True).first()
    if not vet:
        return error_response("Veterinarian not found", status_code=404)
    
    vet_data = vet.to_dict()
    
    # Get assigned animal counts
    assigned_count = Animal.query.filter_by(veterinarian_id=vet.id, is_active=True).count()
    active_treatments = Animal.query.filter_by(
        veterinarian_id=vet.id, 
        is_active=True, 
        health_status='under_treatment'
    ).count()
    
    vet_data['assigned_animals_count'] = assigned_count
    vet_data['active_treatments_count'] = active_treatments
    
    return success_response("Veterinarian retrieved successfully", data=vet_data)


@bp.route('/veterinarians/<vet_id>/dashboard', methods=['GET'])
@auth_required
def get_vet_dashboard(current_user, vet_id):
    """Get veterinarian dashboard data."""
    # Access control
    if current_user.user_type == UserRole.VETERINARIAN:
        if str(current_user.id) != vet_id:
            return error_response("Access denied", status_code=403)
    elif current_user.user_type != UserRole.ADMIN:
        return error_response("Access denied", status_code=403)
    
    vet = Veterinarian.query.filter_by(id=vet_id, is_active=True).first()
    if not vet:
        return error_response("Veterinarian not found", status_code=404)
    
    # Get assigned animals summary
    summary, error_msg = AnimalService.get_vet_assigned_animals(vet_id)
    if not summary:
        return error_response(error_msg, status_code=500)
    
    # Get recent health records created by this vet
    recent_health_records = HealthRecord.query.filter_by(
        recorded_by_id=vet_id,
        is_active=True
    ).order_by(HealthRecord.created_at.desc()).limit(10).all()
    
    # Get upcoming checkups (animals with next_checkup_date)
    upcoming_checkups = db.session.query(Animal, HealthRecord).join(
        HealthRecord, Animal.id == HealthRecord.animal_id
    ).filter(
        Animal.veterinarian_id == vet_id,
        Animal.is_active == True,
        HealthRecord.next_checkup_date.isnot(None),
        HealthRecord.next_checkup_date >= db.func.current_date()
    ).order_by(HealthRecord.next_checkup_date.asc()).limit(10).all()
    
    # Convert animals in summary to dict (already handled in service)
    dashboard_data = {
        'veterinarian': vet.to_dict(),
        'assigned_animals_summary': summary,
        'recent_health_records': [record.to_dict() for record in recent_health_records],
        'upcoming_checkups': [
            {
                'animal': animal.to_dict(),
                'next_checkup_date': record.next_checkup_date.isoformat() if record.next_checkup_date else None
            }
            for animal, record in upcoming_checkups
        ],
        'total_assigned': summary['total_assigned'],
        'animals_needing_attention': summary['animals_needing_attention']
    }
    
    return success_response("Veterinarian dashboard data retrieved successfully", data=dashboard_data)


@bp.route('/veterinarians/<vet_id>/health-records', methods=['GET'])
@auth_required
def get_vet_health_records(current_user, vet_id):
    """Get health records created by a veterinarian."""
    # Access control
    if current_user.user_type == UserRole.VETERINARIAN:
        if str(current_user.id) != vet_id:
            return error_response("Access denied", status_code=403)
    elif current_user.user_type != UserRole.ADMIN:
        return error_response("Access denied", status_code=403)
    
    vet = Veterinarian.query.filter_by(id=vet_id, is_active=True).first()
    if not vet:
        return error_response("Veterinarian not found", status_code=404)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = HealthRecord.query.filter_by(
        recorded_by_id=vet_id,
        is_active=True
    ).order_by(HealthRecord.created_at.desc())
    
    # Paginate results
    pagination = paginate_query(query, page, per_page)
    
    return success_response(
        "Veterinarian health records retrieved successfully",
        data={
            'veterinarian': vet.to_dict(),
            'health_records': [record.to_dict() for record in pagination['items']],
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


@bp.route('/veterinarians/<vet_id>/schedule', methods=['GET'])
@auth_required
def get_vet_schedule(current_user, vet_id):
    """Get veterinarian's schedule/appointments."""
    # Only the vet themselves or admin can view schedule
    if current_user.user_type == UserRole.VETERINARIAN:
        if str(current_user.id) != vet_id:
            return error_response("Access denied", status_code=403)
    elif current_user.user_type != UserRole.ADMIN:
        return error_response("Access denied", status_code=403)
    
    vet = Veterinarian.query.filter_by(id=vet_id, is_active=True).first()
    if not vet:
        return error_response("Veterinarian not found", status_code=404)
    
    # Get upcoming checkups for animals assigned to this vet
    start_date = request.args.get('start_date', date.today().isoformat())
    end_date = request.args.get('end_date', (date.today() + timedelta(days=30)).isoformat())
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return error_response("Invalid date format. Use YYYY-MM-DD", status_code=400)
    
    # Get scheduled checkups
    scheduled_checkups = db.session.query(Animal, HealthRecord).join(
        HealthRecord, Animal.id == HealthRecord.animal_id
    ).filter(
        Animal.veterinarian_id == vet_id,
        Animal.is_active == True,
        HealthRecord.next_checkup_date.between(start_date, end_date)
    ).order_by(HealthRecord.next_checkup_date.asc()).all()
    
    schedule_data = []
    for animal, record in scheduled_checkups:
        schedule_data.append({
            'date': record.next_checkup_date.isoformat(),
            'animal': animal.to_dict(),
            'last_checkup_date': record.checkup_date.isoformat(),
            'notes': record.recommendations or record.notes,
            'farmer': {
                'name': animal.farmer.name,
                'phone': animal.farmer.phone,
                'email': animal.farmer.email
            }
        })
    
    return success_response(
        "Veterinarian schedule retrieved successfully",
        data={
            'veterinarian': vet.to_dict(),
            'schedule': schedule_data,
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'total_appointments': len(schedule_data)
        }
    )