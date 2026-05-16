from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import User, Student, Grade, Attendance, Message, DisciplineRecord
from utils import student_or_parent_required, calculate_performance_stats

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
@student_or_parent_required
def dashboard():
    """Student/Parent dashboard"""
    # Determine which student to show data for
    if current_user.role == 'student':
        student = Student.get(current_user.id)
        student_id = current_user.id
    else:  # parent role
        # For parents, find their child's student profile
        # In a real system, this would be a proper parent-child relationship
        # For now, we'll get the first student as a demo
        all_students = Student.get_all()
        if all_students:
            student = all_students[0]  # Get first student for demo
            student_id = student.user_id
        else:
            student = None
            student_id = None
    
    if not student:
        flash('No student data available. Please contact administrator.', 'error')
        return render_template('student/dashboard.html', 
                             student=None, 
                             stats={},
                             recent_grades=[],
                             recent_attendance=[],
                             unread_messages=[],
                             discipline_count=0)
    
    # Get student's academic data
    grades = Grade.get_by_student(student_id)
    attendance_records = Attendance.get_by_student(student_id)
    discipline_records = DisciplineRecord.get_by_student(student_id)
    messages = Message.get_received(current_user.id)
    
    # Calculate statistics
    stats = calculate_performance_stats(student_id)
    
    # Recent activities
    recent_grades = sorted(grades, key=lambda x: x.created_at, reverse=True)[:5]
    recent_attendance = sorted(attendance_records, key=lambda x: x.created_at, reverse=True)[:5]
    unread_messages = [m for m in messages if not m.read]
    
    return render_template('student/dashboard.html', 
                         student=student, 
                         stats=stats,
                         recent_grades=recent_grades,
                         recent_attendance=recent_attendance,
                         unread_messages=unread_messages,
                         discipline_count=len(discipline_records))

@student_bp.route('/grades')
@login_required
@student_or_parent_required
def view_grades():
    """View student grades"""
    if current_user.role == 'student':
        student_id = current_user.id
    else:  # parent
        student_id = current_user.id  # Simplified for demo
    
    student = Student.get(student_id)
    if not student:
        flash('Student profile not found.', 'error')
        return redirect(url_for('index'))
    
    grades = Grade.get_by_student(student_id)
    
    # Group grades by subject
    grades_by_subject = {}
    for grade in grades:
        if grade.subject not in grades_by_subject:
            grades_by_subject[grade.subject] = []
        grades_by_subject[grade.subject].append(grade)
    
    # Calculate subject averages
    subject_averages = {}
    for subject, subject_grades in grades_by_subject.items():
        if subject_grades:
            avg = sum(g.percentage for g in subject_grades) / len(subject_grades)
            subject_averages[subject] = round(avg, 2)
        else:
            subject_averages[subject] = 0
    
    return render_template('student/view_grades.html', 
                         student=student,
                         grades_by_subject=grades_by_subject,
                         subject_averages=subject_averages)

@student_bp.route('/attendance')
@login_required
@student_or_parent_required
def view_attendance():
    """View student attendance"""
    if current_user.role == 'student':
        student_id = current_user.id
    else:  # parent
        student_id = current_user.id  # Simplified for demo
    
    student = Student.get(student_id)
    if not student:
        flash('Student profile not found.', 'error')
        return redirect(url_for('index'))
    
    attendance_records = Attendance.get_by_student(student_id)
    
    # Calculate attendance statistics
    total_days = len(attendance_records)
    present_days = len([r for r in attendance_records if r.status == 'present'])
    absent_days = len([r for r in attendance_records if r.status == 'absent'])
    late_days = len([r for r in attendance_records if r.status == 'late'])
    
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    # Group by month for chart display
    monthly_attendance = {}
    for record in attendance_records:
        month_key = record.date.strftime('%Y-%m')
        if month_key not in monthly_attendance:
            monthly_attendance[month_key] = {'total': 0, 'present': 0}
        
        monthly_attendance[month_key]['total'] += 1
        if record.status == 'present':
            monthly_attendance[month_key]['present'] += 1
    
    stats = {
        'total_days': total_days,
        'present_days': present_days,
        'absent_days': absent_days,
        'late_days': late_days,
        'attendance_percentage': round(attendance_percentage, 2)
    }
    
    return render_template('student/view_attendance.html', 
                         student=student,
                         attendance_records=attendance_records,
                         stats=stats,
                         monthly_attendance=monthly_attendance)

@student_bp.route('/discipline')
@login_required
@student_or_parent_required
def view_discipline():
    """View discipline records"""
    if current_user.role == 'student':
        student_id = current_user.id
    else:  # parent
        student_id = current_user.id  # Simplified for demo
    
    student = Student.get(student_id)
    if not student:
        flash('Student profile not found.', 'error')
        return redirect(url_for('index'))
    
    discipline_records = DisciplineRecord.get_by_student(student_id)
    
    return render_template('student/view_discipline.html', 
                         student=student,
                         discipline_records=discipline_records)

@student_bp.route('/messages')
@login_required
@student_or_parent_required
def messages():
    """View messages"""
    received_messages = Message.get_received(current_user.id)
    sent_messages = Message.get_sent(current_user.id)
    
    # Mark messages as read when viewed
    for message in received_messages:
        message.mark_as_read()
    
    return render_template('student/messages.html', 
                         received_messages=received_messages,
                         sent_messages=sent_messages)

@student_bp.route('/messages/send', methods=['GET', 'POST'])
@login_required
@student_or_parent_required
def send_message():
    """Send a message to teachers"""
    if request.method == 'POST':
        receiver_id = int(request.form.get('receiver_id'))
        subject = request.form.get('subject')
        content = request.form.get('content')
        
        if not all([receiver_id, subject, content]):
            flash('All fields are required.', 'error')
            return redirect(url_for('student.send_message'))
        
        Message.create(current_user.id, receiver_id, subject, content)
        flash('Message sent successfully!', 'success')
        return redirect(url_for('student.messages'))
    
    # Get all users for message recipients
    users = User.get_all()
    
    # Exclude the current user from the list of recipients
    recipients = [user for user in users if user.id != current_user.id]
    
    return render_template('student/send_message.html', recipients=recipients)

@student_bp.route('/reports')
@login_required
@student_or_parent_required
def reports():
    """Generate student performance reports"""
    if current_user.role == 'student':
        student_id = current_user.id
    else:  # parent
        student_id = current_user.id  # Simplified for demo
    
    student = Student.get(student_id)
    if not student:
        flash('Student profile not found.', 'error')
        return redirect(url_for('index'))
    
    # Get comprehensive data
    grades = Grade.get_by_student(student_id)
    attendance_records = Attendance.get_by_student(student_id)
    discipline_records = DisciplineRecord.get_by_student(student_id)
    
    # Calculate detailed statistics
    stats = calculate_performance_stats(student_id)
    
    # Subject-wise detailed analysis
    subject_analysis = {}
    for grade in grades:
        if grade.subject not in subject_analysis:
            subject_analysis[grade.subject] = {
                'grades': [],
                'exam_types': {},
                'improvement_trend': []
            }
        
        subject_analysis[grade.subject]['grades'].append(grade)
        
        if grade.exam_type not in subject_analysis[grade.subject]['exam_types']:
            subject_analysis[grade.subject]['exam_types'][grade.exam_type] = []
        subject_analysis[grade.subject]['exam_types'][grade.exam_type].append(grade.percentage)
    
    # Calculate averages and trends
    for subject in subject_analysis:
        grades_list = subject_analysis[subject]['grades']
        grades_list.sort(key=lambda x: x.date)
        
        # Calculate improvement trend (simple: compare first half vs second half)
        if len(grades_list) >= 4:
            first_half = grades_list[:len(grades_list)//2]
            second_half = grades_list[len(grades_list)//2:]
            
            first_avg = sum(g.percentage for g in first_half) / len(first_half)
            second_avg = sum(g.percentage for g in second_half) / len(second_half)
            
            trend = second_avg - first_avg
            subject_analysis[subject]['trend'] = round(trend, 2)
        else:
            subject_analysis[subject]['trend'] = 0
    
    return render_template('student/reports.html', 
                         student=student,
                         stats=stats,
                         subject_analysis=subject_analysis,
                         discipline_count=len(discipline_records))
