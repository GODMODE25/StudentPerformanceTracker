import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Import models and database
from database import db
from models import User, Student, Teacher, Grade, Attendance, Message, DisciplineRecord, Course, Program, Enrollment, AuditLog, get_sample_data
from validation import validate_student_data, validate_course_data, validate_program_data, validate_enrollment_data

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Configure the database - using local SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///student_tracker.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.get(int(user_id))

# Import blueprints
from auth import auth_bp
from admin import admin_bp
from teacher import teacher_bp
from student import student_bp
from parent import parent_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(teacher_bp, url_prefix='/teacher')
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(parent_bp, url_prefix='/parent')

# Sample data is initialized during table creation above

@app.route('/')
def index():
    """Home page with role-based redirect"""
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        elif current_user.role in ['student', 'parent']:
            return redirect(url_for('student.dashboard'))
    
    return render_template('index.html')

@app.route('/api/performance-data/<int:student_id>')
@login_required
def api_performance_data(student_id):
    """API endpoint for performance chart data"""
    if current_user.role not in ['admin', 'teacher'] and current_user.id != student_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    student = Student.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    grades = Grade.get_by_student(student_id)
    subjects = list(set(grade.subject for grade in grades))
    
    chart_data = {
        'labels': subjects,
        'data': []
    }
    
    for subject in subjects:
        subject_grades = [g for g in grades if g.subject == subject]
        if subject_grades:
            avg_grade = sum(g.marks for g in subject_grades) / len(subject_grades)
            chart_data['data'].append(round(avg_grade, 2))
        else:
            chart_data['data'].append(0)
    
    return jsonify(chart_data)

@app.route('/api/attendance-data/<int:student_id>')
@login_required
def api_attendance_data(student_id):
    """API endpoint for attendance chart data"""
    if current_user.role not in ['admin', 'teacher'] and current_user.id != student_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    student = Student.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    attendance_records = Attendance.get_by_student(student_id)
    
    # Calculate monthly attendance
    monthly_data = {}
    for record in attendance_records:
        month_key = record.date.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = {'present': 0, 'total': 0}
        
        monthly_data[month_key]['total'] += 1
        if record.status == 'present':
            monthly_data[month_key]['present'] += 1
    
    chart_data = {
        'labels': list(monthly_data.keys()),
        'data': []
    }
    
    for month in monthly_data:
        percentage = (monthly_data[month]['present'] / monthly_data[month]['total']) * 100
        chart_data['data'].append(round(percentage, 2))
    
    return jsonify(chart_data)


@app.route('/api/students', methods=['GET'])
@login_required
def api_get_students():
    """API endpoint to get all students"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    students = Student.get_all()
    student_data = []
    
    for student in students:
        user = User.get(student.user_id)
        student_data.append({
            'id': student.id,
            'user_id': student.user_id,
            'student_id': student.student_id,
            'full_name': user.full_name if user else '',
            'email': user.email if user else '',
            'class_name': student.class_name,
            'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
            'address': student.address,
            'parent_contact': student.parent_contact,
            'emergency_contact': student.emergency_contact
        })
    
    return jsonify(student_data)


@app.route('/api/students/<int:student_id>', methods=['GET'])
@login_required
def api_get_student(student_id):
    """API endpoint to get a specific student by ID"""
    if current_user.role not in ['admin', 'teacher'] and current_user.id != student_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    student = Student.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    user = User.get(student.user_id)
    student_data = {
        'id': student.id,
        'user_id': student.user_id,
        'student_id': student.student_id,
        'full_name': user.full_name if user else '',
        'email': user.email if user else '',
        'class_name': student.class_name,
        'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
        'address': student.address,
        'parent_contact': student.parent_contact,
        'emergency_contact': student.emergency_contact
    }
    
    return jsonify(student_data)


@app.route('/api/students', methods=['POST'])
@login_required
def api_create_student():
    """API endpoint to create a new student"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validation
    errors = validate_student_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        # Create user
        user = User.create(
            username=data.get('username', data['email'].split('@')[0]),
            email=data['email'],
            password=data.get('password', 'student123'),
            role='student',
            full_name=data['full_name']
        )
        
        # Create student profile
        student = Student.create(
            user_id=user.id,
            student_id=data.get('student_id', f'STU{user.id:04d}'),
            class_name=data['class_name'],
            parent_contact=data.get('parent_contact'),
            date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date() if data.get('date_of_birth') else None,
            address=data.get('address'),
            emergency_contact=data.get('emergency_contact')
        )
        
        # Return created student
        student_data = {
            'id': student.id,
            'user_id': student.user_id,
            'student_id': student.student_id,
            'full_name': user.full_name,
            'email': user.email,
            'class_name': student.class_name,
            'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
            'address': student.address,
            'parent_contact': student.parent_contact,
            'emergency_contact': student.emergency_contact
        }
        
        return jsonify(student_data), 201
    except Exception as e:
        return jsonify({'error': f'Error creating student: {str(e)}'}), 500


@app.route('/api/students/<int:student_id>', methods=['PUT'])
@login_required
def api_update_student(student_id):
    """API endpoint to update a student"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    student = Student.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    user = User.get(student.user_id)
    data = request.get_json()
    
    # Validation
    errors = validate_student_data(data, is_update=True)
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        # Update user details
        user.update(
            full_name=data.get('full_name', user.full_name),
            email=data.get('email', user.email)
        )
        
        # Handle date of birth
        date_of_birth = None
        if 'date_of_birth' in data and data['date_of_birth']:
            try:
                date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format for date of birth'}), 400
        
        # Update student details
        student.update(
            student_id=data.get('student_id', student.student_id),
            class_name=data.get('class_name', student.class_name),
            parent_contact=data.get('parent_contact', student.parent_contact),
            date_of_birth=date_of_birth,
            address=data.get('address', student.address),
            emergency_contact=data.get('emergency_contact', student.emergency_contact)
        )
        
        # Return updated student
        student_data = {
            'id': student.id,
            'user_id': student.user_id,
            'student_id': student.student_id,
            'full_name': user.full_name,
            'email': user.email,
            'class_name': student.class_name,
            'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
            'address': student.address,
            'parent_contact': student.parent_contact,
            'emergency_contact': student.emergency_contact
        }
        
        return jsonify(student_data)
    except Exception as e:
        return jsonify({'error': f'Error updating student: {str(e)}'}), 500


@app.route('/api/students/<int:student_id>', methods=['DELETE'])
@login_required
def api_delete_student(student_id):
    """API endpoint to delete a student"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    student = Student.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    user = User.get(student.user_id)
    
    try:
        # Delete student and user
        db.session.delete(student)
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'Student deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error deleting student: {str(e)}'}), 500


@app.route('/api/courses', methods=['GET'])
@login_required
def api_get_courses():
    """API endpoint to get all courses"""
    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    courses = Course.get_all()
    course_data = []
    
    for course in courses:
        teacher = User.get(course.teacher_id) if course.teacher_id else None
        course_data.append({
            'id': course.id,
            'name': course.name,
            'code': course.code,
            'description': course.description,
            'credits': course.credits,
            'teacher_id': course.teacher_id,
            'teacher_name': teacher.full_name if teacher else None
        })
    
    return jsonify(course_data)


@app.route('/api/programs', methods=['GET'])
@login_required
def api_get_programs():
    """API endpoint to get all programs"""
    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    programs = Program.get_all()
    program_data = []
    
    for program in programs:
        program_data.append({
            'id': program.id,
            'name': program.name,
            'code': program.code,
            'description': program.description,
            'duration': program.duration
        })
    
    return jsonify(program_data)


@app.route('/api/enrollments', methods=['GET'])
@login_required
def api_get_enrollments():
    """API endpoint to get all enrollments"""
    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    enrollments = Enrollment.get_all()
    enrollment_data = []
    
    for enrollment in enrollments:
        student = User.get(enrollment.student_id)
        course = Course.get(enrollment.course_id)
        enrollment_data.append({
            'id': enrollment.id,
            'student_id': enrollment.student_id,
            'student_name': student.full_name if student else None,
            'course_id': enrollment.course_id,
            'course_name': course.name if course else None,
            'enrollment_date': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None,
            'status': enrollment.status,
            'grade': enrollment.grade
        })
    
    return jsonify(enrollment_data)


@app.route('/api/courses', methods=['POST'])
@login_required
def api_create_course():
    """API endpoint to create a new course"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validation
    errors = validate_course_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        # Create course
        course = Course.create(
            name=data['name'],
            code=data['code'],
            description=data.get('description'),
            credits=int(data.get('credits', 3)),
            teacher_id=data.get('teacher_id')
        )
        
        # Return created course
        teacher = User.get(course.teacher_id) if course.teacher_id else None
        course_data = {
            'id': course.id,
            'name': course.name,
            'code': course.code,
            'description': course.description,
            'credits': course.credits,
            'teacher_id': course.teacher_id,
            'teacher_name': teacher.full_name if teacher else None
        }
        
        return jsonify(course_data), 201
    except Exception as e:
        return jsonify({'error': f'Error creating course: {str(e)}'}), 500


@app.route('/api/courses/<int:course_id>', methods=['PUT'])
@login_required
def api_update_course(course_id):
    """API endpoint to update a course"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    course = Course.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    data = request.get_json()
    
    # Validation
    errors = validate_course_data(data, is_update=True)
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        # Check if code is unique (excluding current course)
        if 'code' in data and data['code'] != course.code:
            existing_course = Course.get_by_code(data['code'])
            if existing_course and existing_course.id != course.id:
                return jsonify({'error': 'Course code already exists'}), 400
        
        # Update course
        course.name = data.get('name', course.name)
        course.code = data.get('code', course.code)
        course.description = data.get('description', course.description)
        course.credits = int(data.get('credits', course.credits))
        course.teacher_id = data.get('teacher_id', course.teacher_id)
        db.session.commit()
        
        # Return updated course
        teacher = User.get(course.teacher_id) if course.teacher_id else None
        course_data = {
            'id': course.id,
            'name': course.name,
            'code': course.code,
            'description': course.description,
            'credits': course.credits,
            'teacher_id': course.teacher_id,
            'teacher_name': teacher.full_name if teacher else None
        }
        
        return jsonify(course_data)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error updating course: {str(e)}'}), 500


@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
@login_required
def api_delete_course(course_id):
    """API endpoint to delete a course"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    course = Course.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    # Check if there are enrollments for this course
    enrollments = Enrollment.get_by_course(course_id)
    if enrollments:
        return jsonify({'error': 'Cannot delete course with existing enrollments'}), 400
    
    try:
        db.session.delete(course)
        db.session.commit()
        return jsonify({'message': 'Course deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error deleting course: {str(e)}'}), 500


@app.route('/api/programs', methods=['POST'])
@login_required
def api_create_program():
    """API endpoint to create a new program"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validation
    errors = validate_program_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        # Create program
        program = Program.create(
            name=data['name'],
            code=data['code'],
            description=data.get('description'),
            duration=int(data.get('duration')) if data.get('duration') else None
        )
        
        # Return created program
        program_data = {
            'id': program.id,
            'name': program.name,
            'code': program.code,
            'description': program.description,
            'duration': program.duration
        }
        
        return jsonify(program_data), 201
    except Exception as e:
        return jsonify({'error': f'Error creating program: {str(e)}'}), 500


@app.route('/api/programs/<int:program_id>', methods=['PUT'])
@login_required
def api_update_program(program_id):
    """API endpoint to update a program"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    program = Program.get(program_id)
    if not program:
        return jsonify({'error': 'Program not found'}), 404
    
    data = request.get_json()
    
    # Validation
    errors = validate_program_data(data, is_update=True)
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        # Check if code is unique (excluding current program)
        if 'code' in data and data['code'] != program.code:
            existing_program = Program.get_by_code(data['code'])
            if existing_program and existing_program.id != program.id:
                return jsonify({'error': 'Program code already exists'}), 400
        
        # Update program
        program.name = data.get('name', program.name)
        program.code = data.get('code', program.code)
        program.description = data.get('description', program.description)
        program.duration = int(data.get('duration', program.duration)) if data.get('duration') else None
        db.session.commit()
        
        # Return updated program
        program_data = {
            'id': program.id,
            'name': program.name,
            'code': program.code,
            'description': program.description,
            'duration': program.duration
        }
        
        return jsonify(program_data)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error updating program: {str(e)}'}), 500


@app.route('/api/programs/<int:program_id>', methods=['DELETE'])
@login_required
def api_delete_program(program_id):
    """API endpoint to delete a program"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    program = Program.get(program_id)
    if not program:
        return jsonify({'error': 'Program not found'}), 404
    
    try:
        db.session.delete(program)
        db.session.commit()
        return jsonify({'message': 'Program deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error deleting program: {str(e)}'}), 500


@app.route('/api/enrollments', methods=['POST'])
@login_required
def api_create_enrollment():
    """API endpoint to create a new enrollment"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validation
    errors = validate_enrollment_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    # Check if enrollment already exists
    existing_enrollment = Enrollment.query.filter_by(student_id=data['student_id'], course_id=data['course_id']).first()
    if existing_enrollment:
        return jsonify({'error': 'Student is already enrolled in this course'}), 400
    
    try:
        # Create enrollment
        enrollment = Enrollment.create(
            student_id=data['student_id'],
            course_id=data['course_id'],
            enrollment_date=datetime.strptime(data['enrollment_date'], '%Y-%m-%d').date() if data.get('enrollment_date') else None,
            status=data.get('status', 'active'),
            grade=data.get('grade')
        )
        
        # Return created enrollment
        student = User.get(enrollment.student_id)
        course = Course.get(enrollment.course_id)
        enrollment_data = {
            'id': enrollment.id,
            'student_id': enrollment.student_id,
            'student_name': student.full_name if student else None,
            'course_id': enrollment.course_id,
            'course_name': course.name if course else None,
            'enrollment_date': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None,
            'status': enrollment.status,
            'grade': enrollment.grade
        }
        
        return jsonify(enrollment_data), 201
    except Exception as e:
        return jsonify({'error': f'Error creating enrollment: {str(e)}'}), 500


@app.route('/api/enrollments/<int:enrollment_id>', methods=['PUT'])
@login_required
def api_update_enrollment(enrollment_id):
    """API endpoint to update an enrollment"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    enrollment = Enrollment.get(enrollment_id)
    if not enrollment:
        return jsonify({'error': 'Enrollment not found'}), 404
    
    data = request.get_json()
    
    # Validation
    errors = validate_enrollment_data(data, is_update=True)
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        # Update enrollment
        if 'status' in data:
            enrollment.status = data['status']
        if 'grade' in data:
            enrollment.grade = data['grade']
        if 'enrollment_date' in data and data['enrollment_date']:
            enrollment.enrollment_date = datetime.strptime(data['enrollment_date'], '%Y-%m-%d').date()
        db.session.commit()
        
        # Return updated enrollment
        student = User.get(enrollment.student_id)
        course = Course.get(enrollment.course_id)
        enrollment_data = {
            'id': enrollment.id,
            'student_id': enrollment.student_id,
            'student_name': student.full_name if student else None,
            'course_id': enrollment.course_id,
            'course_name': course.name if course else None,
            'enrollment_date': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None,
            'status': enrollment.status,
            'grade': enrollment.grade
        }
        
        return jsonify(enrollment_data)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error updating enrollment: {str(e)}'}), 500


@app.route('/api/enrollments/<int:enrollment_id>', methods=['DELETE'])
@login_required
def api_delete_enrollment(enrollment_id):
    """API endpoint to delete an enrollment"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    enrollment = Enrollment.get(enrollment_id)
    if not enrollment:
        return jsonify({'error': 'Enrollment not found'}), 404
    
    try:
        db.session.delete(enrollment)
        db.session.commit()
        return jsonify({'message': 'Enrollment deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error deleting enrollment: {str(e)}'}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        get_sample_data()
    app.run(host='0.0.0.0', port=5000, debug=True)
