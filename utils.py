from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user
from datetime import datetime, date, timedelta
from models import User, Student, Teacher, Grade, Attendance, Message, DisciplineRecord

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    """Decorator to require teacher role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            flash('Access denied. Teacher privileges required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def student_or_parent_required(f):
    """Decorator to require student or parent role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ['student', 'parent']:
            flash('Access denied. Student or parent privileges required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def calculate_performance_stats(student_id):
    """Calculate comprehensive performance statistics for a student"""
    grades = Grade.get_by_student(student_id)
    attendance_records = Attendance.get_by_student(student_id)

    stats = {
        'total_grades': len(grades),
        'average_grade': 0,
        'highest_grade': 0,
        'lowest_grade': 100,
        'total_attendance_days': len(attendance_records),
        'present_days': 0,
        'absent_days': 0,
        'late_days': 0,
        'attendance_percentage': 0,
        'subjects_count': 0,
        'last_updated': None
    }

    if grades:
        percentages = [grade.percentage for grade in grades]
        stats['average_grade'] = round(sum(percentages) / len(percentages), 2)
        stats['highest_grade'] = round(max(percentages), 2)
        stats['lowest_grade'] = round(min(percentages), 2)
        stats['subjects_count'] = len(set(grade.subject for grade in grades))
        stats['last_updated'] = max(grades, key=lambda x: x.created_at).created_at

    if attendance_records:
        stats['present_days'] = len([r for r in attendance_records if r.status == 'present'])
        stats['absent_days'] = len([r for r in attendance_records if r.status == 'absent'])
        stats['late_days'] = len([r for r in attendance_records if r.status == 'late'])

        if stats['total_attendance_days'] > 0:
            stats['attendance_percentage'] = round(
                (stats['present_days'] / stats['total_attendance_days']) * 100, 2
            )

    return stats

def get_sample_data():
    """Initialize the system with sample data for demonstration"""
    print("Initializing sample data...")
    print(f"Current users in system: {len(User.get_all())}")

    # Create admin user
    admin_user = User.get_by_username('admin')
    if not admin_user:
        admin = User.create('admin', 'admin@school.edu', 'admin123', 'admin', 'System Administrator')
        print(f"Created admin user: {admin.username}")
    else:
        print("Admin user already exists")

    # Create sample teachers
    if not User.get_by_username('teacher1'):
        teacher1 = User.create('teacher1', 'john.smith@school.edu', 'teacher123', 'teacher', 'John Smith')
        Teacher.create(teacher1.id, 'TCH001', ['Mathematics', 'Physics'], ['Grade 10', 'Grade 11'])

        teacher2 = User.create('teacher2', 'mary.johnson@school.edu', 'teacher123', 'teacher', 'Mary Johnson')
        Teacher.create(teacher2.id, 'TCH002', ['English', 'Literature'], ['Grade 10', 'Grade 12'])

        teacher3 = User.create('teacher3', 'david.brown@school.edu', 'teacher123', 'teacher', 'David Brown')
        Teacher.create(teacher3.id, 'TCH003', ['Chemistry', 'Biology'], ['Grade 11', 'Grade 12'])

    # Create sample students
    if not User.get_by_username('student1'):
        student1 = User.create('student1', 'alice.wilson@student.edu', 'student123', 'student', 'Alice Wilson')
        Student.create(student1.id, 'STU001', 'Grade 10', 'alice.parent@email.com')

        student2 = User.create('student2', 'bob.davis@student.edu', 'student123', 'student', 'Bob Davis')
        Student.create(student2.id, 'STU002', 'Grade 10', 'bob.parent@email.com')

        student3 = User.create('student3', 'charlie.miller@student.edu', 'student123', 'student', 'Charlie Miller')
        Student.create(student3.id, 'STU003', 'Grade 11', 'charlie.parent@email.com')

        student4 = User.create('student4', 'diana.garcia@student.edu', 'student123', 'student', 'Diana Garcia')
        Student.create(student4.id, 'STU004', 'Grade 11', 'diana.parent@email.com')

    # Create sample parent
    if not User.get_by_username('parent1'):
        parent1 = User.create('parent1', 'parent@email.com', 'parent123', 'parent', 'Parent User')
        # In a real system, we'd link parents to their children properly
        Student.create(parent1.id, 'STU005', 'Grade 10', 'parent@email.com')

    # Create sample grades
    teachers = User.get_by_role('teacher')
    students = User.get_by_role('student')

    if teachers and students and len(Grade.get_all()) == 0:
        teacher1_id = teachers[0].id
        teacher2_id = teachers[1].id if len(teachers) > 1 else teachers[0].id
        teacher3_id = teachers[2].id if len(teachers) > 2 else teachers[0].id

        # Sample grades for different students and subjects
        sample_grades = [
            # Alice Wilson (student1)
            (students[0].id, teacher1_id, 'Mathematics', 'midterm', 85, 100, '2024-03-15'),
            (students[0].id, teacher1_id, 'Mathematics', 'assignment', 92, 100, '2024-03-20'),
            (students[0].id, teacher1_id, 'Physics', 'quiz', 78, 100, '2024-03-25'),
            (students[0].id, teacher2_id, 'English', 'essay', 88, 100, '2024-03-30'),

            # Bob Davis (student2)
            (students[1].id, teacher1_id, 'Mathematics', 'midterm', 76, 100, '2024-03-15'),
            (students[1].id, teacher1_id, 'Mathematics', 'assignment', 82, 100, '2024-03-20'),
            (students[1].id, teacher2_id, 'English', 'midterm', 90, 100, '2024-03-18'),
            (students[1].id, teacher2_id, 'English', 'assignment', 87, 100, '2024-03-28'),
        ]

        if len(students) > 2:
            sample_grades.extend([
                # Charlie Miller (student3)
                (students[2].id, teacher1_id, 'Physics', 'midterm', 91, 100, '2024-03-16'),
                (students[2].id, teacher3_id, 'Chemistry', 'lab', 89, 100, '2024-03-22'),
                (students[2].id, teacher3_id, 'Biology', 'quiz', 94, 100, '2024-03-27'),
            ])

        if len(students) > 3:
            sample_grades.extend([
                # Diana Garcia (student4)
                (students[3].id, teacher2_id, 'Literature', 'essay', 93, 100, '2024-03-19'),
                (students[3].id, teacher3_id, 'Chemistry', 'midterm', 87, 100, '2024-03-21'),
                (students[3].id, teacher3_id, 'Biology', 'assignment', 91, 100, '2024-03-26'),
            ])

        for grade_data in sample_grades:
            student_id, teacher_id, subject, exam_type, marks, max_marks, date_str = grade_data
            exam_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            Grade.create(student_id, teacher_id, subject, exam_type, marks, max_marks, exam_date)

    # Create sample attendance records
    if students and teachers and len(Attendance.get_all()) == 0:
        teacher_id = teachers[0].id

        # Create attendance for the last 30 days
        for i in range(30):
            attendance_date = date.today() - timedelta(days=i)

            for student in students[:4]:  # First 4 students
                # Random attendance pattern (mostly present)
                import random
                status_choice = random.choices(['present', 'absent', 'late'], weights=[85, 10, 5])[0]
                Attendance.create(student.id, teacher_id, attendance_date, status_choice)

    # Create sample messages
    if len(Message.get_all()) == 0 and teachers and students:
        Message.create(
            teachers[0].id, 
            students[0].id, 
            'Progress Update', 
            'Alice has shown great improvement in Mathematics this term. Keep up the good work!'
        )

        if len(teachers) > 1:
            Message.create(
                teachers[1].id, 
                students[1].id, 
                'Assignment Reminder', 
                'Please remind Bob to submit his English essay by Friday.'
            )

    # Create sample discipline records
    if len(DisciplineRecord.get_all()) == 0 and teachers and students:
        DisciplineRecord.create(
            students[1].id, 
            teachers[0].id, 
            'minor', 
            'Late to class', 
            date.today() - timedelta(days=5),
            'Verbal warning given'
        )

def get_grade_color(percentage):
    """Return Bootstrap color class based on grade percentage"""
    if percentage >= 90:
        return 'success'
    elif percentage >= 80:
        return 'info'
    elif percentage >= 70:
        return 'warning'
    elif percentage >= 60:
        return 'secondary'
    else:
        return 'danger'

def get_attendance_color(percentage):
    """Return Bootstrap color class based on attendance percentage"""
    if percentage >= 95:
        return 'success'
    elif percentage >= 90:
        return 'info'
    elif percentage >= 85:
        return 'warning'
    else:
        return 'danger'

def format_date(date_obj):
    """Format date object to readable string"""
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%B %d, %Y')
    elif isinstance(date_obj, date):
        return date_obj.strftime('%B %d, %Y')
    return str(date_obj)

def format_datetime(datetime_obj):
    """Format datetime object to readable string"""
    if isinstance(datetime_obj, datetime):
        return datetime_obj.strftime('%B %d, %Y at %I:%M %p')
    return str(datetime_obj)