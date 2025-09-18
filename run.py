"""Application entry point."""

import os
from app import create_app, db
from app.models.user import User, Farmer, Veterinarian, Admin
from app.models.animal import Animal, HealthRecord

app = create_app(os.getenv('FLASK_CONFIG', 'development'))


@app.shell_context_processor
def make_shell_context():
    """Make database models available in flask shell."""
    return {
        'db': db,
        'User': User,
        'Farmer': Farmer,
        'Veterinarian': Veterinarian,
        'Admin': Admin,
        'Animal': Animal,
        'HealthRecord': HealthRecord
    }


@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database initialized successfully!")


@app.cli.command()
def seed_db():
    """Seed the database with initial data."""
    from seeds import seed_database
    seed_database()
    print("Database seeded successfully!")


@app.cli.command()
def reset_db():
    """Reset the database (drop and recreate)."""
    db.drop_all()
    db.create_all()
    print("Database reset successfully!")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)