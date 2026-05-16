from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date
from models import User, Student, Teacher, Grade, Attendance, Message, DisciplineRecord
from utils import teacher_required

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    """Teacher dashboard"""
    teacher = Teacher.get(current_user.id)
    if not teacher:
        flash('Teacher profile not found.', 'error')
        return redirect(url_for('index'))

    # Get teacher's classes and subjects
    my_grades = Grade.get_by_teacher(current_user.id)
    my_attendance = Attendance.get_by_teacher(current_user.id)
    my_messages = Message.get_received(current_user.id)

    # Calculate statistics
    stats = {
        'total_grades_entered': len(my_grades),
        'total_attendance_records': len(my_attendance),
        'unread_messages': len([m for m in my_messages if not m.read]),
        'classes_taught': len(teacher.classes),
        'subjects_taught': len(teacher.subjects)
    }

    # Recent activities
    recent_grades = sorted(my_grades, key=lambda x: x.created_at, reverse=True)[:5]
    recent_messages = sorted(my_messages, key=lambda x: x.timestamp, reverse=True)[:3]

    return render_template('teacher/dashboard.html', teacher=teacher, stats=stats,
                         recent_grades=recent_grades, recent_messages=recent_messages)

@teacher_bp.route('/grades')
@login_required
@teacher_required
def manage_grades():
    """Manage student grades"""
    teacher = Teacher.get(current_user.id)
    if not teacher:
        flash('Teacher profile not found.', 'error')
        return redirect(url_for('index'))

    # Get students from teacher's classes
    students = []
    for class_name in teacher.get_classes():
        students.extend(Student.get_by_class(class_name))

    # Get grades entered by this teacher
    grades = Grade.get_by_teacher(current_user.id)

    return render_template('teacher/manage_grades.html', teacher=teacher, 
                         students=students, grades=grades)

@teacher_bp.route('/grades/add', methods=['GET', 'POST'])
@login_required
@teacher_required
def add_grade():
    """Add a new grade"""
    teacher = Teacher.get(current_user.id)
    if not teacher:
        flash('Teacher profile not found.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        student_id = int(request.form.get('student_id'))
        subject = request.form.get('subject')
        exam_type = request.form.get('exam_type')
        marks = float(request.form.get('marks'))
        max_marks = float(request.form.get('max_marks'))
        exam_date = request.form.get('exam_date')

        # Validation
        if not all([student_id, subject, exam_type, marks, max_marks, exam_date]):
            flash('All fields are required.', 'error')
            return redirect(url_for('teacher.add_grade'))

        if marks > max_marks:
            flash('Marks cannot exceed maximum marks.', 'error')
            return redirect(url_for('teacher.add_grade'))

        # Convert date string to date object
        try:
            exam_date = datetime.strptime(exam_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'error')
            return redirect(url_for('teacher.add_grade'))

        # Create grade
        Grade.create(student_id, current_user.id, subject, exam_type, marks, max_marks, exam_date)
        flash('Grade added successfully!', 'success')
        return redirect(url_for('teacher.manage_grades'))

    # Get students from teacher's classes
    students = []
    for class_name in teacher.get_classes():
        students.extend(Student.get_by_class(class_name))

    return render_template('teacher/add_grade.html', teacher=teacher, students=students)

@teacher_bp.route('/attendance')
@login_required
@teacher_required
def manage_attendance():
    """Manage student attendance"""
    teacher = Teacher.get(current_user.id)
    if not teacher:
        flash('Teacher profile not found.', 'error')
        return redirect(url_for('index'))

    # Get students from teacher's classes
    students = []
    for class_name in teacher.get_classes():
        students.extend(Student.get_by_class(class_name))

    # Get attendance records entered by this teacher
    attendance_records = Attendance.get_by_teacher(current_user.id)

    # Group by date for easier display
    attendance_by_date = {}
    for record in attendance_records:
        date_str = record.date.strftime('%Y-%m-%d')
        if date_str not in attendance_by_date:
            attendance_by_date[date_str] = []
        attendance_by_date[date_str].append(record)

    return render_template('teacher/manage_attendance.html', teacher=teacher, 
                         students=students, attendance_by_date=attendance_by_date)

@teacher_bp.route('/attendance/mark', methods=['GET', 'POST'])
@login_required
@teacher_required
def mark_attendance():
    """Mark attendance for students"""
    teacher = Teacher.get(current_user.id)
    if not teacher:
        flash('Teacher profile not found.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        attendance_date = request.form.get('attendance_date')

        # Convert date string to date object
        try:
            attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'error')
            return redirect(url_for('teacher.mark_attendance'))

        # Get students from teacher's classes
        students = []
        for class_name in teacher.get_classes():
            students.extend(Student.get_by_class(class_name))

        # Process attendance for each student
        for student in students:
            status = request.form.get(f'status_{student.user_id}')
            remarks = request.form.get(f'remarks_{student.user_id}', '')

            if status:
                # Check if attendance already exists for this date
                existing = [a for a in Attendance.get_by_student(student.user_id) 
                          if a.date == attendance_date and a.teacher_id == current_user.id]

                if not existing:
                    Attendance.create(student.user_id, current_user.id, attendance_date, status, remarks)

        flash('Attendance marked successfully!', 'success')
        return redirect(url_for('teacher.manage_attendance'))

    # Get students from teacher's classes
    students = []
    for class_name in teacher.get_classes():
        students.extend(Student.get_by_class(class_name))

    return render_template('teacher/mark_attendance.html', teacher=teacher, students=students, today=date.today())

@teacher_bp.route('/messages')
@login_required
@teacher_required
def messages():
    """View and send messages"""
    received_messages = Message.get_received(current_user.id)
    sent_messages = Message.get_sent(current_user.id)

    return render_template('teacher/messages.html',
                         received_messages=received_messages,
                         sent_messages=sent_messages)

@teacher_bp.route('/messages/mark_as_read/<int:message_id>')
@login_required
@teacher_required
def mark_as_read(message_id):
    """Mark a message as read"""
    message = Message.get(message_id)
    if message and message.receiver_id == current_user.id:
        message.read = True
        message.save()
        flash('Message marked as read.', 'success')
    else:
        flash('Message not found or you do not have permission to mark it as read.', 'error')
    return redirect(url_for('teacher.messages'))

@teacher_bp.route('/messages/send', methods=['GET', 'POST'])
@login_required
@teacher_required
def send_message():
    """Send a message to parents/students"""
    if request.method == 'POST':
        receiver_id = int(request.form.get('receiver_id'))
        subject = request.form.get('subject')
        content = request.form.get('content')

        if not all([receiver_id, subject, content]):
            flash('All fields are required.', 'error')
            return redirect(url_for('teacher.send_message'))

        Message.create(current_user.id, receiver_id, subject, content)
        flash('Message sent successfully!', 'success')
        return redirect(url_for('teacher.messages'))

    # Get all users for message recipients
    users = User.get_all()
    
    # Exclude the current user from the list of recipients
    recipients = [user for user in users if user.id != current_user.id]

    return render_template('teacher/send_message.html', recipients=recipients)

@teacher_bp.route('/discipline')
@login_required
@teacher_required
def discipline_records():
    """View and manage discipline records"""
    records = DisciplineRecord.get_by_teacher(current_user.id)
    return render_template('teacher/discipline_records.html', records=records)

@teacher_bp.route('/discipline/add', methods=['GET', 'POST'])
@login_required
@teacher_required
def add_discipline_record():
    """Add a discipline record"""
    teacher = Teacher.get(current_user.id)
    if not teacher:
        flash('Teacher profile not found.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        student_id = int(request.form.get('student_id'))
        incident_type = request.form.get('incident_type')
        description = request.form.get('description')
        incident_date = request.form.get('incident_date')
        action_taken = request.form.get('action_taken', '')

        if not all([student_id, incident_type, description, incident_date]):
            flash('All required fields must be filled.', 'error')
            return redirect(url_for('teacher.add_discipline_record'))

        # Convert date string to date object
        try:
            incident_date = datetime.strptime(incident_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'error')
            return redirect(url_for('teacher.add_discipline_record'))

        DisciplineRecord.create(student_id, current_user.id, incident_type, description, incident_date, action_taken)
        flash('Discipline record added successfully!', 'success')
        return redirect(url_for('teacher.discipline_records'))

    # Get students from teacher's classes
    students = []
    for class_name in teacher.get_classes():
        students.extend(Student.get_by_class(class_name))

    return render_template('teacher/add_discipline_record.html', teacher=teacher, students=students)