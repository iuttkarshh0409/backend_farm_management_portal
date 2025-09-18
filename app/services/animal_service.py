# 🔧 Fixed app/services/animal_service.py

"""Animal management service."""

from flask import current_app
from app.models.animal import Animal, HealthRecord, AnimalSpecies, Gender, HealthStatus, ProductionStatus
from app.models.user import Farmer, Veterinarian
from app.utils.validators import validate_required_fields
from app.utils.helpers import format_phone_number
from app import db
from datetime import datetime, date
import uuid


class AnimalService:
    """Service for animal management operations."""
    
    @staticmethod
    def create_animal(animal_data, farmer_id):
        """Create a new animal for a farmer."""
        try:
            # Validate required fields
            required_fields = ['tag_id', 'species', 'gender']
            valid, missing = validate_required_fields(animal_data, required_fields)
            if not valid:
                return None, f"Missing required fields: {', '.join(missing)}"
            
            # Check if farmer exists
            farmer = Farmer.query.filter_by(id=farmer_id, is_active=True).first()
            if not farmer:
                return None, "Farmer not found"
            
            # Validate species
            try:
                species = AnimalSpecies(animal_data['species'].lower())
            except ValueError:
                return None, f"Invalid species. Must be one of: {[s.value for s in AnimalSpecies]}"
            
            # Validate gender
            try:
                gender = Gender(animal_data['gender'].lower())
            except ValueError:
                return None, f"Invalid gender. Must be one of: {[g.value for g in Gender]}"
            
            # Check if tag_id is unique for this farmer
            existing_animal = Animal.query.filter_by(
                tag_id=animal_data['tag_id'],
                farmer_id=farmer_id,
                is_active=True
            ).first()
            
            if existing_animal:
                return None, "An animal with this tag ID already exists for this farmer"
            
            # Validate health status if provided
            health_status = HealthStatus.HEALTHY  # default
            if animal_data.get('health_status'):
                try:
                    health_status = HealthStatus(animal_data['health_status'].lower())
                except ValueError:
                    return None, f"Invalid health status. Must be one of: {[s.value for s in HealthStatus]}"
            
            # Validate production status if provided
            production_status = None
            if animal_data.get('production_status'):
                try:
                    production_status = ProductionStatus(animal_data['production_status'].lower())
                except ValueError:
                    return None, f"Invalid production status. Must be one of: {[s.value for s in ProductionStatus]}"
            
            # Parse birth_date if provided
            birth_date = None
            if animal_data.get('birth_date'):
                try:
                    birth_date = datetime.strptime(animal_data['birth_date'], '%Y-%m-%d').date()
                except ValueError:
                    return None, "Invalid birth_date format. Use YYYY-MM-DD"
            
            # Parse purchase_date if provided
            purchase_date = None
            if animal_data.get('purchase_date'):
                try:
                    purchase_date = datetime.strptime(animal_data['purchase_date'], '%Y-%m-%d').date()
                except ValueError:
                    return None, "Invalid purchase_date format. Use YYYY-MM-DD"
            
            # Create animal
            animal = Animal(
                tag_id=animal_data['tag_id'].strip(),
                name=animal_data.get('name', '').strip() if animal_data.get('name') else None,
                species=species,
                breed=animal_data.get('breed', '').strip() if animal_data.get('breed') else None,
                gender=gender,
                age_months=animal_data.get('age_months'),
                birth_date=birth_date,
                weight_kg=animal_data.get('weight_kg'),
                height_cm=animal_data.get('height_cm'),
                color=animal_data.get('color', '').strip() if animal_data.get('color') else None,
                health_status=health_status,
                production_status=production_status,
                farmer_id=farmer_id,
                purchase_date=purchase_date,
                purchase_price=animal_data.get('purchase_price'),
                source=animal_data.get('source', '').strip() if animal_data.get('source') else None,
                vaccination_status=animal_data.get('vaccination_status', '').strip() if animal_data.get('vaccination_status') else None,
                daily_milk_yield=animal_data.get('daily_milk_yield'),
                lactation_number=animal_data.get('lactation_number'),
                notes=animal_data.get('notes', '').strip() if animal_data.get('notes') else None,
                special_conditions=animal_data.get('special_conditions', '').strip() if animal_data.get('special_conditions') else None
            )
            
            db.session.add(animal)
            db.session.commit()
            
            current_app.logger.info(f"Animal created: {animal.tag_id} for farmer {farmer.email}")
            return animal, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create animal: {str(e)}")
            return None, f"Failed to create animal: {str(e)}"
    
    @staticmethod
    def assign_veterinarian(animal_id, vet_id, assigned_by_user_id):
        """Assign a veterinarian to an animal."""
        try:
            # Check if animal exists
            animal = Animal.query.filter_by(id=animal_id, is_active=True).first()
            if not animal:
                return None, "Animal not found"
            
            # Check if veterinarian exists
            vet = Veterinarian.query.filter_by(id=vet_id, is_active=True).first()
            if not vet:
                return None, "Veterinarian not found"
            
            # Check if vet is active
            if vet.status.value != 'active':
                return None, "Veterinarian is not active"
            
            # Assign veterinarian
            animal.veterinarian_id = vet_id
            db.session.commit()
            
            current_app.logger.info(f"Veterinarian {vet.email} assigned to animal {animal.tag_id} by user {assigned_by_user_id}")
            return animal, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to assign veterinarian: {str(e)}")
            return None, f"Failed to assign veterinarian: {str(e)}"
    
    @staticmethod
    def update_animal_profile(animal_id, update_data, updated_by_user_id):
        """Update animal profile data."""
        try:
            animal = Animal.query.filter_by(id=animal_id, is_active=True).first()
            if not animal:
                return None, "Animal not found"
            
            # Fields that can be updated
            updatable_fields = {
                'name', 'breed', 'weight_kg', 'height_cm', 'color', 'health_status',
                'production_status', 'daily_milk_yield', 'lactation_number', 
                'vaccination_status', 'notes', 'special_conditions'
            }
            
            # Update allowed fields
            updated_fields = []
            for field, value in update_data.items():
                if field in updatable_fields and hasattr(animal, field):
                    # Handle enum fields
                    if field == 'health_status' and value:
                        try:
                            setattr(animal, field, HealthStatus(value.lower()))
                            updated_fields.append(field)
                        except ValueError:
                            continue
                    elif field == 'production_status' and value:
                        try:
                            setattr(animal, field, ProductionStatus(value.lower()))
                            updated_fields.append(field)
                        except ValueError:
                            continue
                    else:
                        setattr(animal, field, value)
                        updated_fields.append(field)
            
            if updated_fields:
                db.session.commit()
                current_app.logger.info(f"Animal {animal.tag_id} updated by user {updated_by_user_id}: {', '.join(updated_fields)}")
                return animal, f"Animal profile updated: {', '.join(updated_fields)}"
            else:
                return None, "No valid fields to update"
                
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to update animal profile: {str(e)}")
            return None, f"Animal profile update failed: {str(e)}"
    
    @staticmethod
    def create_health_record(health_record_data, recorded_by_user_id):
        """Create a health record for an animal."""
        try:
            # Validate required fields
            required_fields = ['animal_id']
            valid, missing = validate_required_fields(health_record_data, required_fields)
            if not valid:
                return None, f"Missing required fields: {', '.join(missing)}"
            
            # Check if animal exists
            animal = Animal.query.filter_by(id=health_record_data['animal_id'], is_active=True).first()
            if not animal:
                return None, "Animal not found"
            
            # Parse checkup_date if provided
            checkup_date = date.today()
            if health_record_data.get('checkup_date'):
                try:
                    checkup_date = datetime.strptime(health_record_data['checkup_date'], '%Y-%m-%d').date()
                except ValueError:
                    return None, "Invalid checkup_date format. Use YYYY-MM-DD"
            
            # Parse next_checkup_date if provided
            next_checkup_date = None
            if health_record_data.get('next_checkup_date'):
                try:
                    next_checkup_date = datetime.strptime(health_record_data['next_checkup_date'], '%Y-%m-%d').date()
                except ValueError:
                    return None, "Invalid next_checkup_date format. Use YYYY-MM-DD"
            
            # Validate overall_condition if provided
            overall_condition = None
            if health_record_data.get('overall_condition'):
                try:
                    overall_condition = HealthStatus(health_record_data['overall_condition'].lower())
                except ValueError:
                    return None, f"Invalid overall_condition. Must be one of: {[s.value for s in HealthStatus]}"
            
            # Create health record
            health_record = HealthRecord(
                animal_id=health_record_data['animal_id'],
                recorded_by_id=recorded_by_user_id,
                checkup_date=checkup_date,
                temperature=health_record_data.get('temperature'),
                weight_kg=health_record_data.get('weight_kg'),
                heart_rate=health_record_data.get('heart_rate'),
                respiratory_rate=health_record_data.get('respiratory_rate'),
                symptoms=health_record_data.get('symptoms', '').strip() if health_record_data.get('symptoms') else None,
                diagnosis=health_record_data.get('diagnosis', '').strip() if health_record_data.get('diagnosis') else None,
                treatment_given=health_record_data.get('treatment_given', '').strip() if health_record_data.get('treatment_given') else None,
                next_checkup_date=next_checkup_date,
                recommendations=health_record_data.get('recommendations', '').strip() if health_record_data.get('recommendations') else None,
                overall_condition=overall_condition,
                notes=health_record_data.get('notes', '').strip() if health_record_data.get('notes') else None
            )
            
            db.session.add(health_record)
            
            # Update animal's health status and last checkup date if overall_condition provided
            if overall_condition:
                animal.health_status = overall_condition
                animal.last_checkup_date = checkup_date
            
            db.session.commit()
            
            current_app.logger.info(f"Health record created for animal {animal.tag_id} by user {recorded_by_user_id}")
            return health_record, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create health record: {str(e)}")
            return None, f"Failed to create health record: {str(e)}"
    
    @staticmethod
    def get_animal_health_history(animal_id, limit=10):
        """Get health history for an animal."""
        try:
            animal = Animal.query.filter_by(id=animal_id, is_active=True).first()
            if not animal:
                return None, "Animal not found"
            
            health_records = HealthRecord.query.filter_by(
                animal_id=animal_id, 
                is_active=True
            ).order_by(HealthRecord.checkup_date.desc()).limit(limit).all()
            
            return health_records, None
            
        except Exception as e:
            current_app.logger.error(f"Failed to get health history: {str(e)}")
            return None, f"Failed to get health history: {str(e)}"
    
    @staticmethod
    def get_farmer_animals_summary(farmer_id):
        """Get summary of animals for a farmer."""
        try:
            farmer = Farmer.query.filter_by(id=farmer_id, is_active=True).first()
            if not farmer:
                return None, "Farmer not found"
            
            animals = Animal.query.filter_by(farmer_id=farmer_id, is_active=True).all()
            
            # Calculate summary statistics
            total_animals = len(animals)
            species_count = {}
            health_status_count = {}
            production_status_count = {}
            
            for animal in animals:
                # Count by species
                species = animal.species.value
                species_count[species] = species_count.get(species, 0) + 1
                
                # Count by health status
                health = animal.health_status.value
                health_status_count[health] = health_status_count.get(health, 0) + 1
                
                # Count by production status
                if animal.production_status:
                    production = animal.production_status.value
                    production_status_count[production] = production_status_count.get(production, 0) + 1
            
            summary = {
                'total_animals': total_animals,
                'species_breakdown': species_count,
                'health_status_breakdown': health_status_count,
                'production_status_breakdown': production_status_count,
                'healthy_animals': health_status_count.get('healthy', 0),
                'animals_needing_attention': (
                    health_status_count.get('sick', 0) + 
                    health_status_count.get('under_treatment', 0) + 
                    health_status_count.get('quarantine', 0)
                )
            }
            
            return summary, None
            
        except Exception as e:
            current_app.logger.error(f"Failed to get farmer animals summary: {str(e)}")
            return None, f"Failed to get farmer animals summary: {str(e)}"
    
    @staticmethod
    def get_vet_assigned_animals(vet_id):
        """Get animals assigned to a veterinarian."""
        try:
            vet = Veterinarian.query.filter_by(id=vet_id, is_active=True).first()
            if not vet:
                return None, "Veterinarian not found"
            
            animals = Animal.query.filter_by(
                veterinarian_id=vet_id, 
                is_active=True
            ).order_by(Animal.created_at.desc()).all()
            
            # Group by health status
            animals_by_status = {}
            for animal in animals:
                status = animal.health_status.value
                if status not in animals_by_status:
                    animals_by_status[status] = []
                animals_by_status[status].append(animal)
            
            # Count animals needing attention
            attention_count = 0
            for animal in animals:
                if animal.health_status.value in ['sick', 'under_treatment', 'quarantine']:
                    attention_count += 1
            
            summary = {
                'total_assigned': len(animals),
                'animals_by_status': animals_by_status,
                'animals_needing_attention': attention_count,
                'animals': animals
            }
            
            return summary, None
            
        except Exception as e:
            current_app.logger.error(f"Failed to get vet assigned animals: {str(e)}")
            return None, f"Failed to get vet assigned animals: {str(e)}"
    
    @staticmethod
    def deactivate_animal(animal_id, reason=None, deactivated_by_user_id=None):
        """Deactivate (soft delete) an animal."""
        try:
            animal = Animal.query.filter_by(id=animal_id, is_active=True).first()
            if not animal:
                return None, "Animal not found"
            
            animal.soft_delete()
            
            current_app.logger.info(f"Animal {animal.tag_id} deactivated by user {deactivated_by_user_id}, Reason: {reason}")
            return animal, "Animal deactivated successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to deactivate animal: {str(e)}")
            return None, f"Failed to deactivate animal: {str(e)}"
    
    @staticmethod
    def search_animals(search_params):
        """Search animals based on various criteria."""
        try:
            query = Animal.query.filter_by(is_active=True)
            
            # Filter by farmer
            if search_params.get('farmer_id'):
                query = query.filter_by(farmer_id=search_params['farmer_id'])
            
            # Filter by veterinarian
            if search_params.get('veterinarian_id'):
                query = query.filter_by(veterinarian_id=search_params['veterinarian_id'])
            
            # Filter by species
            if search_params.get('species'):
                try:
                    species = AnimalSpecies(search_params['species'].lower())
                    query = query.filter_by(species=species)
                except ValueError:
                    return None, "Invalid species"
            
            # Filter by health status
            if search_params.get('health_status'):
                try:
                    health_status = HealthStatus(search_params['health_status'].lower())
                    query = query.filter_by(health_status=health_status)
                except ValueError:
                    return None, "Invalid health status"
            
            # Filter by tag ID or name
            if search_params.get('search'):
                search_term = f"%{search_params['search']}%"
                query = query.filter(
                    (Animal.tag_id.ilike(search_term)) | 
                    (Animal.name.ilike(search_term))
                )
            
            # Order results
            order_by = search_params.get('order_by', 'created_at')
            if hasattr(Animal, order_by):
                query = query.order_by(getattr(Animal, order_by).desc())
            
            animals = query.all()
            return animals, None
            
        except Exception as e:
            current_app.logger.error(f"Failed to search animals: {str(e)}")
            return None, f"Failed to search animals: {str(e)}"