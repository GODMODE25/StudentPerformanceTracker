from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Student, Teacher

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember', False))
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')
        
        user = User.get_by_username(username)
        
        # Debug logging
        print(f"Login attempt - Username: {username}")
        print(f"User found: {user is not None}")
        if user:
            print(f"User role: {user.role}")
            print(f"Password check: {user.check_password(password)}")
        
        if user and user.check_password(password):
            if not user.is_active or user.role == 'student':
                flash('Student access has been disabled. Please contact support for more information.', 'error')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            # Redirect based on user role
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            elif user.role == 'parent':
                return redirect(url_for('student.dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        role = request.form.get('role', 'student')

        if role == 'student':
            flash('Student registration is currently disabled.', 'error')
            return render_template('register.html')
        
        # Validation
        if not all([username, email, password, confirm_password, full_name]):
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if password and len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if User.get_by_username(username):
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.get_by_email(email):
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        # Create user
        user = User.create(username, email, password, role, full_name)
        
        # Create role-specific profile
        if role == 'student':
            student_id = request.form.get('student_id', f'STU{user.id:04d}')
            class_name = request.form.get('class_name', 'Grade 10')
            parent_contact = request.form.get('parent_contact')
            Student.create(user.id, student_id, class_name, parent_contact)
        elif role == 'teacher':
            employee_id = request.form.get('employee_id', f'TCH{user.id:04d}')
            subjects = request.form.get('subjects', 'Mathematics').split(',')
            classes = request.form.get('classes', 'Grade 10').split(',')
            Teacher.create(user.id, employee_id, subjects, classes)
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))
