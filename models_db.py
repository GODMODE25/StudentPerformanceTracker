from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import json

# This will be set by the app
db = None

def init_db(database):
    global db
    db = database

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'teacher', 'student', 'parent'
    full_name = db.Column(db.String(100), nullable=False)
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
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'

class Student(db.Model):
    __tablename__ = 'students'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    parent_contact = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='student_profile')
    
    @staticmethod
    def create(user_id, student_id, class_name, parent_contact=None):
        student = Student(
            user_id=user_id,
            student_id=student_id,
            class_name=class_name,
            parent_contact=parent_contact
        )
        db.session.add(student)
        db.session.commit()
        return student
    
    @staticmethod
    def get(user_id):
        return Student.query.get(user_id)
    
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
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    subjects = db.Column(db.Text)  # JSON string
    classes = db.Column(db.Text)   # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='teacher_profile')
    
    @staticmethod
    def create(user_id, employee_id, subjects, classes):
        teacher = Teacher(
            user_id=user_id,
            employee_id=employee_id,
            subjects=json.dumps(subjects if isinstance(subjects, list) else [subjects]),
            classes=json.dumps(classes if isinstance(classes, list) else [classes])
        )
        db.session.add(teacher)
        db.session.commit()
        return teacher
    
    @staticmethod
    def get(user_id):
        return Teacher.query.get(user_id)
    
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
    exam_type = db.Column(db.String(50), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('User', foreign_keys=[student_id], backref='grades_received')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='grades_given')
    
    @property
    def student_name(self):
        return self.student.full_name if self.student else 'Unknown Student'
    
    @property
    def teacher_name(self):
        return self.teacher.full_name if self.teacher else 'Unknown Teacher'
    
    @property
    def percentage(self):
        return (self.marks / self.max_marks * 100) if self.max_marks > 0 else 0
    
    @staticmethod
    def create(student_id, teacher_id, subject, exam_type, marks, max_marks, date=None):
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        elif date is None:
            date = datetime.now().date()
        
        grade = Grade(
            student_id=student_id,
            teacher_id=teacher_id,
            subject=subject,
            exam_type=exam_type,
            marks=marks,
            max_marks=max_marks,
            date=date
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
        return round((self.marks / self.max_marks) * 100, 2) if self.max_marks > 0 else 0
    
    def __repr__(self):
        return f'<Grade {self.subject}: {self.percentage}%>'

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
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        elif date is None:
            date = datetime.now().date()
        
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
    read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    
    @staticmethod
    def create(sender_id, receiver_id, subject, content):
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            subject=subject,
            content=content
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
    def get_sent(user_id):
        return Message.query.filter_by(sender_id=user_id).all()
    
    @staticmethod
    def get_all():
        return Message.query.all()
    
    def mark_as_read(self):
        self.read = True
        db.session.commit()
    
    def __repr__(self):
        return f'<Message {self.subject}>'

class DisciplineRecord(db.Model):
    __tablename__ = 'discipline_records'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    incident_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    action_taken = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('User', foreign_keys=[student_id], backref='discipline_records')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='discipline_reports')
    
    @staticmethod
    def create(student_id, teacher_id, incident_type, description, date=None, action_taken=None):
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        elif date is None:
            date = datetime.now().date()
        
        record = DisciplineRecord(
            student_id=student_id,
            teacher_id=teacher_id,
            incident_type=incident_type,
            description=description,
            date=date,
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
        return f'<DisciplineRecord {self.incident_type}: {self.date}>'

def get_sample_data():
    """Create sample data for testing and development"""
    # Check if sample data already exists
    if User.query.filter_by(username='admin').first():
        return
    
    try:
        # Create admin user
        admin = User.create('admin', 'admin@school.com', 'admin123', 'admin', 'System Administrator')
        
        # Create teacher
        teacher_user = User.create('teacher1', 'teacher1@school.com', 'teacher123', 'teacher', 'John Smith')
        Teacher.create(teacher_user.id, 'T001', ['Mathematics', 'Physics'], ['Class A', 'Class B'])
        
        # Create student
        student_user = User.create('student1', 'student1@school.com', 'student123', 'student', 'Alice Johnson')
        Student.create(student_user.id, 'S001', 'Class A', 'parent1@email.com')
        
        # Create parent
        parent_user = User.create('parent1', 'parent1@school.com', 'parent123', 'parent', 'Bob Johnson')
        
        # Add sample grades
        Grade.create(student_user.id, teacher_user.id, 'Mathematics', 'quiz', 85, 100, '2024-01-15')
        Grade.create(student_user.id, teacher_user.id, 'Physics', 'assignment', 92, 100, '2024-01-20')
        
        # Add sample attendance
        Attendance.create(student_user.id, teacher_user.id, '2024-01-15', 'present')
        Attendance.create(student_user.id, teacher_user.id, '2024-01-16', 'late', 'Arrived 10 minutes late')
        
        # Add sample message
        Message.create(teacher_user.id, parent_user.id, 'Student Progress Update', 
                      'Alice is doing excellent work in mathematics. Keep up the good work!')
        
        print("Sample data created successfully!")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.session.rollback()