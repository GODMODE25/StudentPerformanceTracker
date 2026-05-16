from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from models import User, Student, Teacher, Grade, Attendance, Message, DisciplineRecord, Course, Program, Enrollment, AuditLog
from utils import admin_required, calculate_performance_stats
from validation import validate_student_data, validate_course_data, validate_program_data, validate_enrollment_data
from database import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with overview statistics"""
    stats = {
        'total_users': len(User.get_all()),
        'total_students': len(Student.get_all()),
        'total_teachers': len(Teacher.get_all()),
        'total_grades': len(Grade.get_all()),
        'total_attendance': len(Attendance.get_all()),
        'total_messages': len(Message.get_all()),
        'total_discipline_records': len(DisciplineRecord.get_all()),
        'total_courses': len(Course.get_all()),
        'total_programs': len(Program.get_all()),
        'total_enrollments': len(Enrollment.get_all()),
        'total_audit_logs': len(AuditLog.get_all())
    }
    
    # Recent activities
    recent_grades = sorted(Grade.get_all(), key=lambda x: x.created_at, reverse=True)[:5]
    recent_messages = sorted(Message.get_all(), key=lambda x: x.created_at, reverse=True)[:5]
    
    return render_template('admin/dashboard.html', stats=stats,
                         recent_grades=recent_grades, recent_messages=recent_messages)

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    """Manage all users in the system"""
    users = User.get_all()
    students = Student.get_all()
    teachers = Teacher.get_all()
    
    return render_template('admin/manage_users.html', users=users,
                         students=students, teachers=teachers)


@admin_bp.route('/api/students')
@login_required
@admin_required
def api_students():
    """API endpoint to get all students with their details"""
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

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create a new user"""
    print("Attempting to create a user from the admin panel.")
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        role = request.form.get('role')
        
        # Validation
        if not all([username, email, password, full_name, role]):
            flash('All fields are required.', 'error')
            return redirect(url_for('admin.create_user'))
        
        if User.get_by_username(username):
            flash('Username already exists.', 'error')
            return redirect(url_for('admin.create_user'))
        
        if User.get_by_email(email):
            flash('Email already registered.', 'error')
            return redirect(url_for('admin.create_user'))
        
        # Create user
        user = User.create(username, email, password, role, full_name)
        
        # Get IP address
        ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        
        # Log user creation
        AuditLog.log_action(
            user_id=current_user.id,
            action='CREATE_USER',
            table_name='users',
            record_id=user.id,
            new_values={
                'username': username,
                'email': email,
                'role': role,
                'full_name': full_name
            },
            ip_address=ip_address
        )
        
        # Create role-specific profile
        if role == 'student':
            student_id = request.form.get('student_id') or f'STU{user.id:04d}'
            class_name = request.form.get('class_name') or 'Grade 10'
            parent_contact = request.form.get('parent_contact')
            date_of_birth_str = request.form.get('date_of_birth')
            address = request.form.get('address')
            emergency_contact = request.form.get('emergency_contact')
            
            # Prepare data for validation
            student_data = {
                'full_name': full_name,
                'email': email,
                'class_name': class_name,
                'date_of_birth': date_of_birth_str,
                'address': address,
                'parent_contact': parent_contact,
                'emergency_contact': emergency_contact
            }
            
            # Validate student data
            errors = validate_student_data(student_data)
            if errors:
                for error in errors:
                    flash(error, 'error')
                return redirect(url_for('admin.create_user'))
            
            # Parse date of birth if provided
            date_of_birth = None
            if date_of_birth_str:
                try:
                    date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid date format for date of birth.', 'error')
                    return redirect(url_for('admin.create_user'))
            
            student = Student.create(user.id, student_id, class_name, parent_contact, date_of_birth, address, emergency_contact)
            
            # Log student creation
            AuditLog.log_action(
                user_id=current_user.id,
                action='CREATE_STUDENT',
                table_name='students',
                record_id=student.id,
                new_values={
                    'user_id': user.id,
                    'student_id': student_id,
                    'class_name': class_name,
                    'parent_contact': parent_contact,
                    'date_of_birth': date_of_birth.isoformat() if date_of_birth else None,
                    'address': address,
                    'emergency_contact': emergency_contact
                },
                ip_address=ip_address
            )
        elif role == 'teacher':
            employee_id = request.form.get('employee_id') or f'TCH{user.id:04d}'
            subjects = request.form.get('subjects', '').split(',')
            classes = request.form.get('classes', '').split(',')
            subjects = [s.strip() for s in subjects if s.strip()]
            classes = [c.strip() for c in classes if c.strip()]
            teacher = Teacher.create(user.id, employee_id, subjects, classes)
            
            # Log teacher creation
            AuditLog.log_action(
                user_id=current_user.id,
                action='CREATE_TEACHER',
                table_name='teachers',
                record_id=teacher.id,
                new_values={
                    'user_id': user.id,
                    'employee_id': employee_id,
                    'subjects': subjects,
                    'classes': classes
                },
                ip_address=ip_address
            )
        
        flash(f'User {username} created successfully!', 'success')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/create_user.html')

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user"""
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    user = User.get(user_id)
    if user:
        # Store user details for audit log
        user_details = {
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'full_name': user.full_name
        }
        
        # Get IP address
        ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        
        # Log user deletion
        AuditLog.log_action(
            user_id=current_user.id,
            action='DELETE_USER',
            table_name='users',
            record_id=user.id,
            old_values=user_details,
            ip_address=ip_address
        )
        
        user.delete()
        flash(f'User {user.username} deleted successfully!', 'success')
    else:
        flash('User not found.', 'error')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Generate various reports"""
    # Performance statistics
    all_grades = Grade.get_all()
    all_attendance = Attendance.get_all()
    
    # Calculate overall statistics
    if all_grades:
        avg_performance = sum(grade.percentage for grade in all_grades) / len(all_grades)
    else:
        avg_performance = 0
    
    if all_attendance:
        present_count = sum(1 for record in all_attendance if record.status == 'present')
        attendance_rate = (present_count / len(all_attendance)) * 100
    else:
        attendance_rate = 0
    
    # Subject-wise performance
    subject_stats = {}
    for grade in all_grades:
        if grade.subject not in subject_stats:
            subject_stats[grade.subject] = []
        subject_stats[grade.subject].append(grade.percentage)
    
    subject_averages = {}
    for subject, scores in subject_stats.items():
        subject_averages[subject] = sum(scores) / len(scores) if scores else 0
    
    # Class-wise statistics
    class_stats = {}
    students = Student.get_all()
    for student in students:
        class_name = student.class_name
        if class_name not in class_stats:
            class_stats[class_name] = {'students': 0, 'total_performance': 0, 'attendance_rate': 0}
        
        class_stats[class_name]['students'] += 1
        
        # Calculate student's average performance
        student_grades = Grade.get_by_student(student.user_id)
        if student_grades:
            avg_grade = sum(g.percentage for g in student_grades) / len(student_grades)
            class_stats[class_name]['total_performance'] += avg_grade
        
        # Calculate student's attendance rate
        student_attendance = Attendance.get_by_student(student.user_id)
        if student_attendance:
            present = sum(1 for a in student_attendance if a.status == 'present')
            attendance_pct = (present / len(student_attendance)) * 100
            class_stats[class_name]['attendance_rate'] += attendance_pct
    
    # Calculate averages for each class
    for class_name in class_stats:
        student_count = class_stats[class_name]['students']
        if student_count > 0:
            class_stats[class_name]['avg_performance'] = class_stats[class_name]['total_performance'] / student_count
            class_stats[class_name]['avg_attendance'] = class_stats[class_name]['attendance_rate'] / student_count
        else:
            class_stats[class_name]['avg_performance'] = 0
            class_stats[class_name]['avg_attendance'] = 0
    
    return render_template('admin/reports.html', 
                         avg_performance=avg_performance,
                         attendance_rate=attendance_rate,
                         subject_averages=subject_averages,
                         class_stats=class_stats)

@admin_bp.route('/messages')
@login_required
@admin_required
def messages():
    """View received and sent messages for the current admin"""
    received_messages = sorted(Message.get_received(current_user.id), key=lambda x: x.created_at, reverse=True)
    sent_messages = sorted(Message.get_sent(current_user.id), key=lambda x: x.created_at, reverse=True)
    
    return render_template('admin/messages.html', received_messages=received_messages, sent_messages=sent_messages)


@admin_bp.route('/send_message', methods=['GET', 'POST'])
@login_required
@admin_required
def send_message():
    """Send a message to a user"""
    if request.method == 'POST':
        recipient_id = request.form.get('recipient_id', type=int)
        subject = request.form.get('subject')
        content = request.form.get('content')
        
        if not all([recipient_id, subject, content]):
            flash('All fields are required.', 'error')
            return redirect(url_for('admin.send_message'))
        
        recipient = User.get(recipient_id)
        if not recipient:
            flash('Recipient not found.', 'error')
            return redirect(url_for('admin.send_message'))
        
        # Create and send the message
        message = Message.create(
            sender_id=current_user.id,
            receiver_id=recipient_id,
            subject=subject,
            content=content
        )
        
        # Log the action
        ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        AuditLog.log_action(
            user_id=current_user.id,
            action='SEND_MESSAGE',
            table_name='messages',
            record_id=message.id,
            new_values={
                'sender_id': current_user.id,
                'receiver_id': recipient_id,
                'subject': subject
            },
            ip_address=ip_address
        )
        
        flash('Message sent successfully!', 'success')
        return redirect(url_for('admin.messages'))
    
    # For GET request, provide a list of all users (teachers and parents)
    recipients = User.query.filter(User.role.in_(['teacher', 'parent'])).all()
    return render_template('admin/send_message.html', recipients=recipients)


@admin_bp.route('/students')
@login_required
@admin_required
def manage_students():
    """Manage all students in the system"""
    students = Student.get_all()
    return render_template('admin/manage_students.html', students=students)


@admin_bp.route('/students/<int:student_id>')
@login_required
@admin_required
def view_student(student_id):
    """View a specific student's details"""
    student = Student.get(student_id)
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('admin.manage_students'))
    
    user = User.get(student.user_id)
    enrollments = Enrollment.get_by_student(student.user_id)
    
    return render_template('admin/view_student.html', student=student, user=user, enrollments=enrollments)


@admin_bp.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_student(student_id):
    """Edit a student's details"""
    student = Student.get(student_id)
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('admin.manage_students'))
    
    user = User.get(student.user_id)
    
    if request.method == 'POST':
        # Store old values for audit log
        old_user_values = {
            'full_name': user.full_name,
            'email': user.email
        }
        
        old_student_values = {
            'student_id': student.student_id,
            'class_name': student.class_name,
            'parent_contact': student.parent_contact,
            'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
            'address': student.address,
            'emergency_contact': student.emergency_contact
        }
        
        # Update user details
        full_name = request.form.get('full_name', user.full_name)
        email = request.form.get('email', user.email)
        
        # Update student details
        student_id = request.form.get('student_id', student.student_id)
        class_name = request.form.get('class_name', student.class_name)
        parent_contact = request.form.get('parent_contact', student.parent_contact)
        dob_str = request.form.get('date_of_birth')
        address = request.form.get('address', student.address)
        emergency_contact = request.form.get('emergency_contact', student.emergency_contact)
        
        # Prepare data for validation
        student_data = {
            'full_name': full_name,
            'email': email,
            'class_name': class_name,
            'date_of_birth': dob_str,
            'address': address,
            'parent_contact': parent_contact,
            'emergency_contact': emergency_contact
        }
        
        # Validate student data
        errors = validate_student_data(student_data, is_update=True)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('admin/edit_student.html', student=student, user=user)
        
        user.update(full_name=full_name, email=email)
        
        # Handle date of birth
        date_of_birth = None
        if dob_str:
            try:
                date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for date of birth.', 'error')
                return render_template('admin/edit_student.html', student=student, user=user)
        
        student.update(
            student_id=student_id,
            class_name=class_name,
            parent_contact=parent_contact,
            date_of_birth=date_of_birth,
            address=address,
            emergency_contact=emergency_contact
        )
        
        # Log the changes
        new_user_values = {
            'full_name': user.full_name,
            'email': user.email
        }
        
        new_student_values = {
            'student_id': student.student_id,
            'class_name': student.class_name,
            'parent_contact': student.parent_contact,
            'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
            'address': student.address,
            'emergency_contact': student.emergency_contact
        }
        
        # Get IP address
        ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        
        # Log user changes if any
        if old_user_values != new_user_values:
            AuditLog.log_action(
                user_id=current_user.id,
                action='UPDATE_USER',
                table_name='users',
                record_id=user.id,
                old_values=old_user_values,
                new_values=new_user_values,
                ip_address=ip_address
            )
        
        # Log student changes if any
        if old_student_values != new_student_values:
            AuditLog.log_action(
                user_id=current_user.id,
                action='UPDATE_STUDENT',
                table_name='students',
                record_id=student.id,
                old_values=old_student_values,
                new_values=new_student_values,
                ip_address=ip_address
            )
        
        flash('Student details updated successfully!', 'success')
        return redirect(url_for('admin.view_student', student_id=student_id))
    
    return render_template('admin/edit_student.html', student=student, user=user)


@admin_bp.route('/courses')
@login_required
@admin_required
def manage_courses():
    """Manage all courses in the system"""
    courses = Course.get_all()
    teachers = User.get_by_role('teacher')
    return render_template('admin/manage_courses.html', courses=courses, teachers=teachers)


@admin_bp.route('/courses/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_course():
    """Create a new course"""
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        description = request.form.get('description')
        credits = request.form.get('credits', 3, type=int)
        teacher_id = request.form.get('teacher_id', type=int)
        
        # Prepare data for validation
        course_data = {
            'name': name,
            'code': code,
            'description': description,
            'credits': credits
        }
        
        # Validation
        errors = validate_course_data(course_data)
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('admin.create_course'))
        
        # Create course
        try:
            course = Course.create(name, code, description, credits, teacher_id)
            
            # Log course creation
            # Get IP address
            ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            
            AuditLog.log_action(
                user_id=current_user.id,
                action='CREATE_COURSE',
                table_name='courses',
                record_id=course.id,
                new_values={
                    'name': name,
                    'code': code,
                    'description': description,
                    'credits': credits,
                    'teacher_id': teacher_id
                },
                ip_address=ip_address
            )
            
            flash(f'Course {name} created successfully!', 'success')
            return redirect(url_for('admin.manage_courses'))
        except Exception as e:
            flash(f'Error creating course: {str(e)}', 'error')
    
    teachers = User.get_by_role('teacher')
    return render_template('admin/create_course.html', teachers=teachers)


@admin_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    """Edit a course"""
    course = Course.get(course_id)
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('admin.manage_courses'))
    
    if request.method == 'POST':
        # Store old values for audit log
        old_values = {
            'name': course.name,
            'code': course.code,
            'description': course.description,
            'credits': course.credits,
            'teacher_id': course.teacher_id
        }
        
        name = request.form.get('name', course.name)
        code = request.form.get('code', course.code)
        description = request.form.get('description', course.description)
        credits = request.form.get('credits', course.credits, type=int)
        teacher_id = request.form.get('teacher_id', course.teacher_id, type=int)
        
        # Prepare data for validation
        course_data = {
            'name': name,
            'code': code,
            'description': description,
            'credits': credits
        }
        
        # Validation
        errors = validate_course_data(course_data, is_update=True)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('admin/edit_course.html', course=course, teachers=User.get_by_role('teacher'))
        
        # Check if code is unique (excluding current course)
        if code != course.code:
            existing_course = Course.get_by_code(code)
            if existing_course and existing_course.id != course.id:
                flash('Course code already exists.', 'error')
                return render_template('admin/edit_course.html', course=course, teachers=User.get_by_role('teacher'))
        
        # Update course
        course.name = name
        course.code = code
        course.description = description
        course.credits = credits
        course.teacher_id = teacher_id
        
        # Commit changes
        try:
            db.session.commit()
            
            # Log the changes
            new_values = {
                'name': course.name,
                'code': course.code,
                'description': course.description,
                'credits': course.credits,
                'teacher_id': course.teacher_id
            }
            
            # Get IP address
            ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            
            # Log course changes if any
            if old_values != new_values:
                AuditLog.log_action(
                    user_id=current_user.id,
                    action='UPDATE_COURSE',
                    table_name='courses',
                    record_id=course.id,
                    old_values=old_values,
                    new_values=new_values,
                    ip_address=ip_address
                )
            
            flash('Course updated successfully!', 'success')
            return redirect(url_for('admin.manage_courses'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating course: {str(e)}', 'error')
    
    teachers = User.get_by_role('teacher')
    return render_template('admin/edit_course.html', course=course, teachers=teachers)


@admin_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    """Delete a course"""
    course = Course.get(course_id)
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('admin.manage_courses'))
    
    # Check if there are enrollments for this course
    enrollments = Enrollment.get_by_course(course_id)
    if enrollments:
        flash('Cannot delete course with existing enrollments.', 'error')
        return redirect(url_for('admin.manage_courses'))
    
    # Store course details for audit log
    course_details = {
        'name': course.name,
        'code': course.code,
        'description': course.description,
        'credits': course.credits,
        'teacher_id': course.teacher_id
    }
    
    try:
        db.session.delete(course)
        db.session.commit()
        
        # Log course deletion
        # Get IP address
        ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        
        AuditLog.log_action(
            user_id=current_user.id,
            action='DELETE_COURSE',
            table_name='courses',
            record_id=course.id,
            old_values=course_details,
            ip_address=ip_address
        )
        
        flash(f'Course {course.name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting course: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_courses'))


@admin_bp.route('/programs')
@login_required
@admin_required
def manage_programs():
    """Manage all programs in the system"""
    programs = Program.get_all()
    return render_template('admin/manage_programs.html', programs=programs)


@admin_bp.route('/programs/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_program():
    """Create a new program"""
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        description = request.form.get('description')
        duration = request.form.get('duration', type=int)
        
        # Prepare data for validation
        program_data = {
            'name': name,
            'code': code,
            'description': description,
            'duration': duration
        }
        
        # Validation
        errors = validate_program_data(program_data)
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('admin.create_program'))
        
        # Create program
        try:
            program = Program.create(name, code, description, duration)
            
            # Log program creation
            # Get IP address
            ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            
            AuditLog.log_action(
                user_id=current_user.id,
                action='CREATE_PROGRAM',
                table_name='programs',
                record_id=program.id,
                new_values={
                    'name': name,
                    'code': code,
                    'description': description,
                    'duration': duration
                },
                ip_address=ip_address
            )
            
            flash(f'Program {name} created successfully!', 'success')
            return redirect(url_for('admin.manage_programs'))
        except Exception as e:
            flash(f'Error creating program: {str(e)}', 'error')
    
    return render_template('admin/create_program.html')


@admin_bp.route('/programs/<int:program_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_program(program_id):
    """Edit a program"""
    program = Program.get(program_id)
    if not program:
        flash('Program not found.', 'error')
        return redirect(url_for('admin.manage_programs'))
    
    if request.method == 'POST':
        # Store old values for audit log
        old_values = {
            'name': program.name,
            'code': program.code,
            'description': program.description,
            'duration': program.duration
        }
        
        name = request.form.get('name', program.name)
        code = request.form.get('code', program.code)
        description = request.form.get('description', program.description)
        duration = request.form.get('duration', program.duration, type=int)
        
        # Prepare data for validation
        program_data = {
            'name': name,
            'code': code,
            'description': description,
            'duration': duration
        }
        
        # Validation
        errors = validate_program_data(program_data, is_update=True)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('admin/edit_program.html', program=program)
        
        # Check if code is unique (excluding current program)
        if code != program.code:
            existing_program = Program.get_by_code(code)
            if existing_program and existing_program.id != program.id:
                flash('Program code already exists.', 'error')
                return render_template('admin/edit_program.html', program=program)
        
        # Update program
        program.name = name
        program.code = code
        program.description = description
        program.duration = duration
        
        # Commit changes
        try:
            db.session.commit()
            
            # Log the changes
            new_values = {
                'name': program.name,
                'code': program.code,
                'description': program.description,
                'duration': program.duration
            }
            
            # Get IP address
            ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            
            # Log program changes if any
            if old_values != new_values:
                AuditLog.log_action(
                    user_id=current_user.id,
                    action='UPDATE_PROGRAM',
                    table_name='programs',
                    record_id=program.id,
                    old_values=old_values,
                    new_values=new_values,
                    ip_address=ip_address
                )
            
            flash('Program updated successfully!', 'success')
            return redirect(url_for('admin.manage_programs'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating program: {str(e)}', 'error')
    
    return render_template('admin/edit_program.html', program=program)


@admin_bp.route('/programs/<int:program_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_program(program_id):
    """Delete a program"""
    program = Program.get(program_id)
    if not program:
        flash('Program not found.', 'error')
        return redirect(url_for('admin.manage_programs'))
    
    # Store program details for audit log
    program_details = {
        'name': program.name,
        'code': program.code,
        'description': program.description,
        'duration': program.duration
    }
    
    try:
        db.session.delete(program)
        db.session.commit()
        
        # Log program deletion
        # Get IP address
        ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        
        AuditLog.log_action(
            user_id=current_user.id,
            action='DELETE_PROGRAM',
            table_name='programs',
            record_id=program.id,
            old_values=program_details,
            ip_address=ip_address
        )
        
        flash(f'Program {program.name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting program: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_programs'))


@admin_bp.route('/enrollments')
@login_required
@admin_required
def manage_enrollments():
    """Manage all enrollments in the system"""
    enrollments = Enrollment.get_all()
    return render_template('admin/manage_enrollments.html', enrollments=enrollments)


@admin_bp.route('/enrollments/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_enrollment():
    """Create a new enrollment"""
    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        course_id = request.form.get('course_id', type=int)
        enrollment_date_str = request.form.get('enrollment_date')
        status = request.form.get('status', 'active')
        grade = request.form.get('grade')
        
        # Prepare data for validation
        enrollment_data = {
            'student_id': student_id,
            'course_id': course_id,
            'status': status,
            'grade': grade
        }
        
        # Validation
        errors = validate_enrollment_data(enrollment_data)
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('admin.create_enrollment'))
        
        # Parse enrollment date
        enrollment_date = date.today()
        if enrollment_date_str:
            try:
                enrollment_date = datetime.strptime(enrollment_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for enrollment date.', 'error')
                return redirect(url_for('admin.create_enrollment'))
        
        # Check if enrollment already exists
        existing_enrollment = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
        if existing_enrollment:
            flash('Student is already enrolled in this course.', 'error')
            return redirect(url_for('admin.create_enrollment'))
        
        # Create enrollment
        try:
            enrollment = Enrollment.create(student_id, course_id, enrollment_date, status, grade)
            
            # Log enrollment creation
            # Get IP address
            ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            
            AuditLog.log_action(
                user_id=current_user.id,
                action='CREATE_ENROLLMENT',
                table_name='enrollments',
                record_id=enrollment.id,
                new_values={
                    'student_id': student_id,
                    'course_id': course_id,
                    'enrollment_date': enrollment_date.isoformat(),
                    'status': status,
                    'grade': grade
                },
                ip_address=ip_address
            )
            
            flash('Enrollment created successfully!', 'success')
            return redirect(url_for('admin.manage_enrollments'))
        except Exception as e:
            flash(f'Error creating enrollment: {str(e)}', 'error')
    
    students = Student.get_all()
    courses = Course.get_all()
    return render_template('admin/create_enrollment.html', students=students, courses=courses)


@admin_bp.route('/enrollments/<int:enrollment_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_enrollment(enrollment_id):
    """Edit an enrollment"""
    enrollment = Enrollment.get(enrollment_id)
    if not enrollment:
        flash('Enrollment not found.', 'error')
        return redirect(url_for('admin.manage_enrollments'))
    
    if request.method == 'POST':
        # Store old values for audit log
        old_values = {
            'status': enrollment.status,
            'grade': enrollment.grade,
            'enrollment_date': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None
        }
        
        status = request.form.get('status', enrollment.status)
        grade = request.form.get('grade', enrollment.grade)
        
        # Prepare data for validation
        enrollment_data = {
            'status': status,
            'grade': grade
        }
        
        # Validation
        errors = validate_enrollment_data(enrollment_data, is_update=True)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('admin/edit_enrollment.html', enrollment=enrollment,
                                 students=Student.get_all(), courses=Course.get_all())
        
        enrollment.status = status
        enrollment.grade = grade
        
        # Parse enrollment date
        enrollment_date_str = request.form.get('enrollment_date')
        if enrollment_date_str:
            try:
                enrollment.enrollment_date = datetime.strptime(enrollment_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for enrollment date.', 'error')
                return render_template('admin/edit_enrollment.html', enrollment=enrollment,
                                     students=Student.get_all(), courses=Course.get_all())
        
        # Commit changes
        try:
            db.session.commit()
            
            # Log the changes
            new_values = {
                'status': enrollment.status,
                'grade': enrollment.grade,
                'enrollment_date': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None
            }
            
            # Get IP address
            ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            
            # Log enrollment changes if any
            if old_values != new_values:
                AuditLog.log_action(
                    user_id=current_user.id,
                    action='UPDATE_ENROLLMENT',
                    table_name='enrollments',
                    record_id=enrollment.id,
                    old_values=old_values,
                    new_values=new_values,
                    ip_address=ip_address
                )
            
            flash('Enrollment updated successfully!', 'success')
            return redirect(url_for('admin.manage_enrollments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating enrollment: {str(e)}', 'error')
    
    students = Student.get_all()
    courses = Course.get_all()
    return render_template('admin/edit_enrollment.html', enrollment=enrollment, students=students, courses=courses)


@admin_bp.route('/enrollments/<int:enrollment_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_enrollment(enrollment_id):
    """Delete an enrollment"""
    enrollment = Enrollment.get(enrollment_id)
    if not enrollment:
        flash('Enrollment not found.', 'error')
        return redirect(url_for('admin.manage_enrollments'))
    
    # Store enrollment details for audit log
    enrollment_details = {
        'student_id': enrollment.student_id,
        'course_id': enrollment.course_id,
        'enrollment_date': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None,
        'status': enrollment.status,
        'grade': enrollment.grade
    }
    
    try:
        db.session.delete(enrollment)
        db.session.commit()
        
        # Log enrollment deletion
        # Get IP address
        ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        
        AuditLog.log_action(
            user_id=current_user.id,
            action='DELETE_ENROLLMENT',
            table_name='enrollments',
            record_id=enrollment.id,
            old_values=enrollment_details,
            ip_address=ip_address
        )
        
        flash('Enrollment deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting enrollment: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_enrollments'))


@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    """View audit logs"""
    logs = AuditLog.get_all()
    return render_template('admin/audit_logs.html', logs=logs)
