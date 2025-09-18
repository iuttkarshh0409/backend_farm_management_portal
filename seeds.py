"""Database seeding script with initial data."""

from app import create_app, db
from app.models.user import User, Farmer, Veterinarian, Admin, UserRole, UserStatus
from app.models.animal import Animal, HealthRecord, AnimalSpecies, Gender, HealthStatus, ProductionStatus
from datetime import date, datetime
import uuid


def seed_database():
    """Seed the database with initial test data."""
    
    print("🌱 Seeding database with initial data...")
    
    # Create sample admin user
    admin = Admin(
        name="System Administrator",
        email="admin@farmportal.com",
        phone="9876543210",
        user_type=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        email_verified=True,
        phone_verified=True,
        employee_id="ADM001",
        department="IT",
        designation="System Admin",
        permissions='["all"]'
    )
    admin.set_password("admin123")
    db.session.add(admin)
    
    # Create sample veterinarian
    vet = Veterinarian(
        name="Dr. Rajesh Kumar",
        email="rajesh.vet@farmportal.com",
        phone="9876543211",
        user_type=UserRole.VETERINARIAN,
        status=UserStatus.ACTIVE,
        email_verified=True,
        phone_verified=True,
        license_no="VET2024001",
        specialization="Large Animal Medicine",
        qualification="BVSc & AH, MVSc",
        experience_years=8,
        clinic_name="Rural Veterinary Clinic",
        consultation_fee=500.00
    )
    vet.set_password("vet123")
    db.session.add(vet)
    
    # Create sample farmers
    farmer1 = Farmer(
        name="Ramesh Patel",
        email="ramesh@farmportal.com",
        phone="9876543212",
        user_type=UserRole.FARMER,
        status=UserStatus.ACTIVE,
        email_verified=True,
        phone_verified=True,
        aadhar_no="123456789012",
        farm_name="Patel Dairy Farm",
        farm_size="25 cattle",
        farm_type="dairy",
        district="Mehsana",
        state="Gujarat",
        pincode="384002"
    )
    farmer1.set_password("farmer123")
    db.session.add(farmer1)
    
    farmer2 = Farmer(
        name="Sunita Sharma",
        email="sunita@farmportal.com",
        phone="9876543213",
        user_type=UserRole.FARMER,
        status=UserStatus.ACTIVE,
        email_verified=True,
        phone_verified=True,
        aadhar_no="123456789013",
        farm_name="Sharma Poultry Farm",
        farm_size="500 birds",
        farm_type="poultry",
        district="Jaipur",
        state="Rajasthan",
        pincode="302001"
    )
    farmer2.set_password("farmer123")
    db.session.add(farmer2)
    
    # Commit users first to get their IDs
    db.session.commit()
    
    # Create sample animals
    animal1 = Animal(
        tag_id="COW001",
        name="Lakshmi",
        species=AnimalSpecies.CATTLE,
        breed="Holstein Friesian",
        gender=Gender.FEMALE,
        age_months=36,
        birth_date=date(2021, 6, 15),
        weight_kg=450.0,
        health_status=HealthStatus.HEALTHY,
        production_status=ProductionStatus.LACTATING,
        farmer_id=farmer1.id,
        veterinarian_id=vet.id,
        daily_milk_yield=25.5,
        lactation_number=2,
        last_calving_date=date(2024, 3, 10)
    )
    db.session.add(animal1)
    
    animal2 = Animal(
        tag_id="COW002",
        name="Ganga",
        species=AnimalSpecies.CATTLE,
        breed="Gir",
        gender=Gender.FEMALE,
        age_months=48,
        birth_date=date(2020, 8, 20),
        weight_kg=380.0,
        health_status=HealthStatus.HEALTHY,
        production_status=ProductionStatus.DRY,
        farmer_id=farmer1.id,
        veterinarian_id=vet.id,
        lactation_number=3
    )
    db.session.add(animal2)
    
    animal3 = Animal(
        tag_id="HEN001",
        species=AnimalSpecies.POULTRY,
        breed="White Leghorn",
        gender=Gender.FEMALE,
        age_months=18,
        weight_kg=1.8,
        health_status=HealthStatus.HEALTHY,
        production_status=ProductionStatus.ACTIVE,
        farmer_id=farmer2.id,
        veterinarian_id=vet.id
    )
    db.session.add(animal3)
    
    # Commit animals to get their IDs
    db.session.commit()
    
    # Create sample health records
    health_record1 = HealthRecord(
        animal_id=animal1.id,
        recorded_by_id=vet.id,
        checkup_date=date.today(),
        temperature=101.5,
        weight_kg=450.0,
        heart_rate=70,
        diagnosis="Routine checkup - healthy",
        overall_condition=HealthStatus.HEALTHY,
        recommendations="Continue current feeding schedule",
        notes="Animal in good health, milk production normal"
    )
    db.session.add(health_record1)
    
    health_record2 = HealthRecord(
        animal_id=animal2.id,
        recorded_by_id=vet.id,
        checkup_date=date.today(),
        temperature=101.2,
        weight_kg=380.0,
        heart_rate=68,
        diagnosis="Routine checkup - healthy",
        overall_condition=HealthStatus.HEALTHY,
        recommendations="Monitor for signs of pregnancy",
        notes="Animal ready for breeding"
    )
    db.session.add(health_record2)
    
    # Commit all changes
    db.session.commit()
    
    print("✅ Database seeded successfully!")
    print(f"   • Created 1 Admin user")
    print(f"   • Created 1 Veterinarian")
    print(f"   • Created 2 Farmers")
    print(f"   • Created 3 Animals")
    print(f"   • Created 2 Health records")
    print()
    print("🔑 Default login credentials:")
    print("   Admin: admin@farmportal.com / admin123")
    print("   Vet: rajesh.vet@farmportal.com / vet123")
    print("   Farmer: ramesh@farmportal.com / farmer123")
    print("   Farmer: sunita@farmportal.com / farmer123")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # Drop and recreate tables
        db.drop_all()
        db.create_all()
        seed_database()