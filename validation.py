from datetime import datetime
from models import User, Student, Course, Program


def validate_student_data(data, is_update=False):
    """Validate student data"""
    errors = []
    
    # For creation, these fields are required
    if not is_update:
        required_fields = ['full_name', 'email', 'class_name']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f'Missing required field: {field}')
    
    # Validate email format
    if 'email' in data and data['email']:
        if '@' not in data['email']:
            errors.append('Invalid email format')
        # Check if email already exists (for creation)
        elif not is_update:
            if User.get_by_email(data['email']):
                errors.append('Email already registered')
    
    # Validate date of birth format
    if 'date_of_birth' in data and data['date_of_birth']:
        try:
            datetime.strptime(data['date_of_birth'], '%Y-%m-%d')
        except ValueError:
            errors.append('Invalid date format for date of birth (expected YYYY-MM-DD)')
    
    return errors


def validate_course_data(data, is_update=False):
    """Validate course data"""
    errors = []
    
    # For creation, these fields are required
    if not is_update:
        required_fields = ['name', 'code']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f'Missing required field: {field}')
    
    # Validate credits
    if 'credits' in data and data['credits'] is not None:
        try:
            credits = int(data['credits'])
            if credits < 0:
                errors.append('Credits must be a positive number')
        except ValueError:
            errors.append('Credits must be a number')
    
    # Check if code already exists (for creation)
    if 'code' in data and data['code'] and not is_update:
        if Course.get_by_code(data['code']):
            errors.append('Course code already exists')
    
    return errors


def validate_program_data(data, is_update=False):
    """Validate program data"""
    errors = []
    
    # For creation, these fields are required
    if not is_update:
        required_fields = ['name', 'code']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f'Missing required field: {field}')
    
    # Validate duration
    if 'duration' in data and data['duration'] is not None:
        try:
            duration = int(data['duration'])
            if duration < 0:
                errors.append('Duration must be a positive number')
        except ValueError:
            errors.append('Duration must be a number')
    
    # Check if code already exists (for creation)
    if 'code' in data and data['code'] and not is_update:
        if Program.get_by_code(data['code']):
            errors.append('Program code already exists')
    
    return errors


def validate_enrollment_data(data, is_update=False):
    """Validate enrollment data"""
    errors = []
    
    # For creation, these fields are required
    if not is_update:
        required_fields = ['student_id', 'course_id']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f'Missing required field: {field}')
    
    # Validate status
    if 'status' in data and data['status']:
        valid_statuses = ['active', 'completed', 'dropped']
        if data['status'] not in valid_statuses:
            errors.append(f'Invalid status. Must be one of: {", ".join(valid_statuses)}')
    
    # Validate grade
    if 'grade' in data and data['grade']:
        valid_grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F']
        if data['grade'] not in valid_grades:
            errors.append(f'Invalid grade. Must be one of: {", ".join(valid_grades)}')
    
    return errors