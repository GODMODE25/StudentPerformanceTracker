import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app import app, db
from models import get_sample_data

def initialize_database():
    """
    Deletes the existing database, creates a new one with the correct schema,
    and populates it with sample data.
    """
    with app.app_context():
        db_path = os.path.join(app.instance_path, 'student_tracker.db')
        
        if os.path.exists(db_path):
            os.remove(db_path)
            print("Deleted old database.")
            
        db.create_all()
        print("Created new database tables.")
        get_sample_data()
        print("Populated database with sample data.")

if __name__ == '__main__':
    initialize_database()