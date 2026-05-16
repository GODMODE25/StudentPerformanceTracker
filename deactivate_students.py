import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from app import app, db
from models import User

def deactivate_student_users():
    """
    Finds all users with the 'student' role and sets their is_active status to False.
    """
    try:
        students_to_deactivate = User.query.filter_by(role='student').all()
        
        if not students_to_deactivate:
            print("No student users found to deactivate.")
            return
        
        for user in students_to_deactivate:
            user.is_active = False
        
        db.session.commit()
        print(f"Successfully deactivated {len(students_to_deactivate)} student users.")
        
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    with app.app_context():
        deactivate_student_users()