from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase
import json
from database import db

class Base(DeclarativeBase):
    pass

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'teacher', 'student', 'parent'
    full_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def create(username, email, password, role, full_name=None):
        user = User(
            username=username,
            email=email,
            role=role,
            full_name=full_name or username
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    
    def update(self, username=None, email=None, role=None, full_name=None, is_active=None):
        """Update user information"""
        if username is not None:
            self.username = username
        if email is not None:
            self.email = email
        if role is not None:
            self.role = role
        if full_name is not None:
            self.full_name = full_name
        if is_active is not None:
            self.is_active = is_active
        
        db.session.commit()

    @staticmethod
    def get(user_id):
        return User.query.get(user_id)

    @staticmethod
    def get_by_username(username):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def get_all():
        return User.query.all()

    @staticmethod
    def get_by_role(role):
        return User.query.filter_by(role=role).all()

    def update_password(self, new_password):
        self.set_password(new_password)
        db.session.commit()

    def update(self, full_name=None, email=None):
        """Update user details"""
        if full_name is not None:
            self.full_name = full_name
        if email is not None:
            self.email = email
        
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f'<User {self.username}>'


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    parent_contact = db.Column(db.String(120))
    date_of_birth = db.Column(db.Date)
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))

    @staticmethod
    def create(user_id, student_id, class_name, parent_contact=None, date_of_birth=None, address=None, emergency_contact=None):
        student = Student(
            user_id=user_id,
            student_id=student_id,
            class_name=class_name,
            parent_contact=parent_contact,
            date_of_birth=date_of_birth,
            address=address,
            emergency_contact=emergency_contact
        )
        db.session.add(student)
        db.session.commit()
        return student
    
    def update(self, student_id=None, class_name=None, parent_contact=None, date_of_birth=None, address=None, emergency_contact=None):
        """Update student information"""
        if student_id is not None:
            self.student_id = student_id
        if class_name is not None:
            self.class_name = class_name
        if parent_contact is not None:
            self.parent_contact = parent_contact
        if date_of_birth is not None:
            self.date_of_birth = date_of_birth
        if address is not None:
            self.address = address
        if emergency_contact is not None:
            self.emergency_contact = emergency_contact
        
        db.session.commit()

    @staticmethod
    def get(user_id):
        return Student.query.filter_by(user_id=user_id).first()

    @staticmethod
    def get_all():
        return Student.query.all()

    @staticmethod
    def get_by_class(class_name):
        return Student.query.filter_by(class_name=class_name).all()

    def __repr__(self):
        return f'<Student {self.student_id}>'


class Teacher(db.Model):
    __tablename__ = 'teachers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    subjects = db.Column(db.Text)  # JSON string of subjects
    classes = db.Column(db.Text)   # JSON string of classes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('teacher_profile', uselist=False))

    @staticmethod
    def create(user_id, employee_id, subjects, classes):
        teacher = Teacher(
            user_id=user_id,
            employee_id=employee_id,
            subjects=json.dumps(subjects) if isinstance(subjects, list) else subjects,
            classes=json.dumps(classes) if isinstance(classes, list) else classes
        )
        db.session.add(teacher)
        db.session.commit()
        return teacher

    @staticmethod
    def get(user_id):
        return Teacher.query.filter_by(user_id=user_id).first()

    @staticmethod
    def get_all():
        return Teacher.query.all()

    def get_subjects(self):
        return json.loads(self.subjects) if self.subjects else []

    def get_classes(self):
        return json.loads(self.classes) if self.classes else []

    def __repr__(self):
        return f'<Teacher {self.employee_id}>'


class Grade(db.Model):
    __tablename__ = 'grades'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)  # 'assignment', 'quiz', 'midterm', 'final'
    marks = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('User', foreign_keys=[student_id], backref='grades_received')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='grades_given')

    @staticmethod
    def create(student_id, teacher_id, subject, exam_type, marks, max_marks, date=None):
        grade = Grade(
            student_id=student_id,
            teacher_id=teacher_id,
            subject=subject,
            exam_type=exam_type,
            marks=marks,
            max_marks=max_marks,
            date=date or datetime.utcnow().date()
        )
        db.session.add(grade)
        db.session.commit()
        return grade

    @staticmethod
    def get(grade_id):
        return Grade.query.get(grade_id)

    @staticmethod
    def get_by_student(student_id):
        return Grade.query.filter_by(student_id=student_id).all()

    @staticmethod
    def get_by_teacher(teacher_id):
        return Grade.query.filter_by(teacher_id=teacher_id).all()

    @staticmethod
    def get_by_subject(subject):
        return Grade.query.filter_by(subject=subject).all()

    @staticmethod
    def get_all():
        return Grade.query.all()

    @property
    def percentage(self):
        """Calculate percentage score"""
        if self.max_marks == 0:
            return 0
        return (self.marks / self.max_marks) * 100

    def __repr__(self):
        return f'<Grade {self.subject}: {self.marks}/{self.max_marks}>'


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'present', 'absent', 'late'
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('User', foreign_keys=[student_id], backref='attendance_records')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='attendance_marked')

    __table_args__ = (db.UniqueConstraint('student_id', 'date', name='unique_student_date'),)

    @staticmethod
    def create(student_id, teacher_id, date, status, remarks=None):
        attendance = Attendance(
            student_id=student_id,
            teacher_id=teacher_id,
            date=date,
            status=status,
            remarks=remarks
        )
        db.session.add(attendance)
        db.session.commit()
        return attendance

    @staticmethod
    def get(attendance_id):
        return Attendance.query.get(attendance_id)

    @staticmethod
    def get_by_student(student_id):
        return Attendance.query.filter_by(student_id=student_id).all()

    @staticmethod
    def get_by_teacher(teacher_id):
        return Attendance.query.filter_by(teacher_id=teacher_id).all()

    @staticmethod
    def get_by_date(date):
        return Attendance.query.filter_by(date=date).all()

    @staticmethod
    def get_all():
        return Attendance.query.all()

    def __repr__(self):
        return f'<Attendance {self.date}: {self.status}>'


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

    @staticmethod
    def create(sender_id, receiver_id, subject, content):
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            subject=subject,
            content=content,
            timestamp=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()
        return message

    @staticmethod
    def get(message_id):
        return Message.query.get(message_id)

    @staticmethod
    def get_by_user(user_id):
        return Message.query.filter(
            (Message.sender_id == user_id) | (Message.receiver_id == user_id)
        ).all()

    @staticmethod
    def get_received(user_id):
        return Message.query.filter_by(receiver_id=user_id).all()

    @staticmethod
    def get_sent(sender_id):
        return Message.query.filter_by(sender_id=sender_id).all()

    @staticmethod
    def get_all():
        return Message.query.all()

    def mark_as_read(self):
        self.is_read = True
        db.session.commit()

    def __repr__(self):
        return f'<Message {self.subject}>'


class DisciplineRecord(db.Model):
    __tablename__ = 'discipline_records'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    incident_type = db.Column(db.String(50), nullable=False)  # 'minor', 'major', 'severe'
    description = db.Column(db.Text, nullable=False)
    action_taken = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('User', foreign_keys=[student_id], backref='discipline_records')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='discipline_reports')

    @staticmethod
    def create(student_id, teacher_id, incident_type, description, date=None, action_taken=None):
        record = DisciplineRecord(
            student_id=student_id,
            teacher_id=teacher_id,
            incident_type=incident_type,
            description=description,
            date=date or datetime.utcnow().date(),
            action_taken=action_taken
        )
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def get(record_id):
        return DisciplineRecord.query.get(record_id)

    @staticmethod
    def get_by_student(student_id):
        return DisciplineRecord.query.filter_by(student_id=student_id).all()

    @staticmethod
    def get_by_teacher(teacher_id):
        return DisciplineRecord.query.filter_by(teacher_id=teacher_id).all()

    @staticmethod
    def get_all():
        return DisciplineRecord.query.all()

    def __repr__(self):
        return f'<DisciplineRecord {self.incident_type}>'


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    credits = db.Column(db.Integer, default=3)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship('User', backref='courses_taught')

    @staticmethod
    def create(name, code, description=None, credits=3, teacher_id=None):
        course = Course(
            name=name,
            code=code,
            description=description,
            credits=credits,
            teacher_id=teacher_id
        )
        db.session.add(course)
        db.session.commit()
        return course

    @staticmethod
    def get(course_id):
        return Course.query.get(course_id)

    @staticmethod
    def get_by_code(code):
        return Course.query.filter_by(code=code).first()

    @staticmethod
    def get_all():
        return Course.query.all()

    def __repr__(self):
        return f'<Course {self.code}: {self.name}>'


class Program(db.Model):
    __tablename__ = 'programs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer)  # in years
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def create(name, code, description=None, duration=None):
        program = Program(
            name=name,
            code=code,
            description=description,
            duration=duration
        )
        db.session.add(program)
        db.session.commit()
        return program

    @staticmethod
    def get(program_id):
        return Program.query.get(program_id)

    @staticmethod
    def get_by_code(code):
        return Program.query.filter_by(code=code).first()

    @staticmethod
    def get_all():
        return Program.query.all()

    def __repr__(self):
        return f'<Program {self.code}: {self.name}>'


class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrollment_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(20), default='active')  # 'active', 'completed', 'dropped'
    grade = db.Column(db.String(2))  # A+, A, B, C, D, F
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('User', backref='enrollments')
    course = db.relationship('Course', backref='enrollments')

    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='unique_student_course'),)

    @staticmethod
    def create(student_id, course_id, enrollment_date=None, status='active', grade=None):
        enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id,
            enrollment_date=enrollment_date or date.today(),
            status=status,
            grade=grade
        )
        db.session.add(enrollment)
        db.session.commit()
        return enrollment

    @staticmethod
    def get(enrollment_id):
        return Enrollment.query.get(enrollment_id)

    @staticmethod
    def get_by_student(student_id):
        return Enrollment.query.filter_by(student_id=student_id).all()

    @staticmethod
    def get_by_course(course_id):
        return Enrollment.query.filter_by(course_id=course_id).all()

    @staticmethod
    def get_all():
        return Enrollment.query.all()

    def __repr__(self):
        return f'<Enrollment {self.student_id} -> {self.course_id}>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(50))
    record_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)  # JSON string of old values
    new_values = db.Column(db.Text)  # JSON string of new values
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

    user = db.relationship('User', backref='audit_logs')

    @staticmethod
    def create(user_id, action, table_name=None, record_id=None, old_values=None, new_values=None, ip_address=None):
        log = AuditLog(
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def log_action(user_id, action, table_name=None, record_id=None, old_values=None, new_values=None, ip_address=None):
        """Log an action with automatic timestamp"""
        return AuditLog.create(user_id, action, table_name, record_id, old_values, new_values, ip_address)
    
    @staticmethod
    def log_action(user_id, action, table_name=None, record_id=None, old_values=None, new_values=None, ip_address=None):
        """Convenience method for logging actions"""
        return AuditLog.create(user_id, action, table_name, record_id, old_values, new_values, ip_address)

    @staticmethod
    def get(log_id):
        return AuditLog.query.get(log_id)

    @staticmethod
    def get_by_user(user_id):
        return AuditLog.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_all():
        return AuditLog.query.all()

    def __repr__(self):
        return f'<AuditLog {self.action}>'


def get_sample_data():
    """Create sample data for testing and development"""

    # Check if we already have data
    if User.query.first():
        return

    try:
        # Create sample users
        admin = User.create(
            username='admin',
            email='admin@school.com',
            password='admin123',
            role='admin',
            full_name='System Administrator'
        )

        teacher1 = User.create(
            username='teacher1',
            email='teacher1@school.com',
            password='teacher123',
            role='teacher',
            full_name='John Smith'
        )

        teacher2 = User.create(
            username='teacher2',
            email='teacher2@school.com',
            password='teacher123',
            role='teacher',
            full_name='Jane Doe'
        )

        student1 = User.create(
            username='student1',
            email='student1@school.com',
            password='student123',
            role='student',
            full_name='Alice Johnson'
        )

        student2 = User.create(
            username='student2',
            email='student2@school.com',
            password='student123',
            role='student',
            full_name='Bob Wilson'
        )

        parent1 = User.create(
            username='parent1',
            email='parent1@school.com',
            password='parent123',
            role='parent',
            full_name='Bob Johnson'
        )

        # Create teacher profiles
        Teacher.create(
            user_id=teacher1.id,
            employee_id='T001',
            subjects=['Mathematics', 'Physics'],
            classes=['Class A', 'Class B']
        )
        
        Teacher.create(
            user_id=teacher2.id,
            employee_id='T002',
            subjects=['English', 'Literature'],
            classes=['Class A', 'Class C']
        )

        # Create student profiles
        Student.create(
            user_id=student1.id,
            student_id='S001',
            class_name='Class A',
            parent_contact='parent1@school.com',
            date_of_birth=date(2005, 5, 15),
            address='123 Main St, City, State',
            emergency_contact='Emergency Contact: 555-1234'
        )
        
        Student.create(
            user_id=student2.id,
            student_id='S002',
            class_name='Class A',
            parent_contact='parent2@school.com',
            date_of_birth=date(2006, 8, 22),
            address='456 Oak Ave, City, State',
            emergency_contact='Emergency Contact: 555-5678'
        )

        # Create sample programs
        program1 = Program.create(
            name='Computer Science',
            code='CS',
            description='Computer Science Program',
            duration=4
        )
        
        program2 = Program.create(
            name='Business Administration',
            code='BA',
            description='Business Administration Program',
            duration=4
        )

        # Create sample courses
        course1 = Course.create(
            name='Introduction to Programming',
            code='CS101',
            description='Basic programming concepts',
            credits=3,
            teacher_id=teacher1.id
        )
        
        course2 = Course.create(
            name='English Literature',
            code='ENG201',
            description='Survey of English Literature',
            credits=3,
            teacher_id=teacher2.id
        )

        # Create sample enrollments
        Enrollment.create(
            student_id=student1.id,
            course_id=course1.id,
            enrollment_date=date.today(),
            status='active',
            grade=None
        )
        
        Enrollment.create(
            student_id=student1.id,
            course_id=course2.id,
            enrollment_date=date.today(),
            status='active',
            grade=None
        )
        
        Enrollment.create(
            student_id=student2.id,
            course_id=course1.id,
            enrollment_date=date.today(),
            status='active',
            grade=None
        )

        # Create sample grades
        Grade.create(
            student_id=student1.id,
            teacher_id=teacher1.id,
            subject='Mathematics',
            exam_type='quiz',
            marks=85,
            max_marks=100
        )

        # Create sample attendance
        Attendance.create(
            student_id=student1.id,
            teacher_id=teacher1.id,
            date=datetime.utcnow().date(),
            status='present'
        )

        print("Sample data created successfully!")

    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.session.rollback()