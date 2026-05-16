from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Import db from app to avoid circular imports
def get_db():
    from app import db
    return db

db = get_db()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    def __init__(self, id, username, email, password_hash, role, full_name=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role  # 'admin', 'teacher', 'student', 'parent'
        self.full_name = full_name or username
        self.created_at = datetime.now()
    
    @staticmethod
    def create(username, email, password, role, full_name=None):
        global _user_id_counter
        password_hash = generate_password_hash(password)
        user = User(_user_id_counter, username, email, password_hash, role, full_name)
        _users[_user_id_counter] = user
        _user_id_counter += 1
        return user
    
    @staticmethod
    def get(user_id):
        return _users.get(user_id)
    
    @staticmethod
    def get_by_username(username):
        for user in _users.values():
            if user.username == username:
                return user
        return None
    
    @staticmethod
    def get_by_email(email):
        for user in _users.values():
            if user.email == email:
                return user
        return None
    
    @staticmethod
    def get_all():
        return list(_users.values())
    
    @staticmethod
    def get_by_role(role):
        return [user for user in _users.values() if user.role == role]
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_password(self, new_password):
        self.password_hash = generate_password_hash(new_password)
    
    def delete(self):
        if self.id in _users:
            del _users[self.id]

class Student:
    def __init__(self, user_id, student_id, class_name, parent_contact=None):
        self.user_id = user_id
        self.student_id = student_id
        self.class_name = class_name
        self.parent_contact = parent_contact
        self.created_at = datetime.now()
    
    @staticmethod
    def create(user_id, student_id, class_name, parent_contact=None):
        student = Student(user_id, student_id, class_name, parent_contact)
        _students[user_id] = student
        return student
    
    @staticmethod
    def get(user_id):
        return _students.get(user_id)
    
    @staticmethod
    def get_all():
        return list(_students.values())
    
    @staticmethod
    def get_by_class(class_name):
        return [student for student in _students.values() if student.class_name == class_name]
    
    @property
    def user(self):
        return User.get(self.user_id)

class Teacher:
    def __init__(self, user_id, employee_id, subjects, classes):
        self.user_id = user_id
        self.employee_id = employee_id
        self.subjects = subjects if isinstance(subjects, list) else [subjects]
        self.classes = classes if isinstance(classes, list) else [classes]
        self.created_at = datetime.now()
    
    @staticmethod
    def create(user_id, employee_id, subjects, classes):
        teacher = Teacher(user_id, employee_id, subjects, classes)
        _teachers[user_id] = teacher
        return teacher
    
    @staticmethod
    def get(user_id):
        return _teachers.get(user_id)
    
    @staticmethod
    def get_all():
        return list(_teachers.values())
    
    @property
    def user(self):
        return User.get(self.user_id)

class Grade:
    def __init__(self, id, student_id, teacher_id, subject, exam_type, marks, max_marks, date):
        self.id = id
        self.student_id = student_id
        self.teacher_id = teacher_id
        self.subject = subject
        self.exam_type = exam_type  # 'assignment', 'quiz', 'midterm', 'final'
        self.marks = marks
        self.max_marks = max_marks
        self.date = date
        self.created_at = datetime.now()
    
    @staticmethod
    def create(student_id, teacher_id, subject, exam_type, marks, max_marks, date=None):
        global _grade_id_counter
        if date is None:
            date = datetime.now().date()
        grade = Grade(_grade_id_counter, student_id, teacher_id, subject, exam_type, marks, max_marks, date)
        _grades[_grade_id_counter] = grade
        _grade_id_counter += 1
        return grade
    
    @staticmethod
    def get(grade_id):
        return _grades.get(grade_id)
    
    @staticmethod
    def get_by_student(student_id):
        return [grade for grade in _grades.values() if grade.student_id == student_id]
    
    @staticmethod
    def get_by_teacher(teacher_id):
        return [grade for grade in _grades.values() if grade.teacher_id == teacher_id]
    
    @staticmethod
    def get_by_subject(subject):
        return [grade for grade in _grades.values() if grade.subject == subject]
    
    @staticmethod
    def get_all():
        return list(_grades.values())
    
    @property
    def percentage(self):
        return (self.marks / self.max_marks) * 100 if self.max_marks > 0 else 0
    
    @property
    def student(self):
        return Student.get(self.student_id)
    
    @property
    def teacher(self):
        return Teacher.get(self.teacher_id)

class Attendance:
    def __init__(self, id, student_id, teacher_id, date, status, remarks=None):
        self.id = id
        self.student_id = student_id
        self.teacher_id = teacher_id
        self.date = date
        self.status = status  # 'present', 'absent', 'late'
        self.remarks = remarks
        self.created_at = datetime.now()
    
    @staticmethod
    def create(student_id, teacher_id, date, status, remarks=None):
        global _attendance_id_counter
        attendance = Attendance(_attendance_id_counter, student_id, teacher_id, date, status, remarks)
        _attendance[_attendance_id_counter] = attendance
        _attendance_id_counter += 1
        return attendance
    
    @staticmethod
    def get(attendance_id):
        return _attendance.get(attendance_id)
    
    @staticmethod
    def get_by_student(student_id):
        return [record for record in _attendance.values() if record.student_id == student_id]
    
    @staticmethod
    def get_by_teacher(teacher_id):
        return [record for record in _attendance.values() if record.teacher_id == teacher_id]
    
    @staticmethod
    def get_by_date(date):
        return [record for record in _attendance.values() if record.date == date]
    
    @staticmethod
    def get_all():
        return list(_attendance.values())
    
    @property
    def student(self):
        return Student.get(self.student_id)
    
    @property
    def teacher(self):
        return Teacher.get(self.teacher_id)

class Message:
    def __init__(self, id, sender_id, receiver_id, subject, content, timestamp):
        self.id = id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.subject = subject
        self.content = content
        self.timestamp = timestamp
        self.read = False
    
    @staticmethod
    def create(sender_id, receiver_id, subject, content):
        global _message_id_counter
        message = Message(_message_id_counter, sender_id, receiver_id, subject, content, datetime.now())
        _messages[_message_id_counter] = message
        _message_id_counter += 1
        return message
    
    @staticmethod
    def get(message_id):
        return _messages.get(message_id)
    
    @staticmethod
    def get_by_user(user_id):
        return [msg for msg in _messages.values() if msg.sender_id == user_id or msg.receiver_id == user_id]
    
    @staticmethod
    def get_received(user_id):
        return [msg for msg in _messages.values() if msg.receiver_id == user_id]
    
    @staticmethod
    def get_sent(user_id):
        return [msg for msg in _messages.values() if msg.sender_id == user_id]
    
    @staticmethod
    def get_all():
        return list(_messages.values())
    
    @property
    def sender(self):
        return User.get(self.sender_id)
    
    @property
    def receiver(self):
        return User.get(self.receiver_id)
    
    def mark_as_read(self):
        self.read = True

class DisciplineRecord:
    def __init__(self, id, student_id, teacher_id, incident_type, description, date, action_taken=None):
        self.id = id
        self.student_id = student_id
        self.teacher_id = teacher_id
        self.incident_type = incident_type  # 'minor', 'major', 'severe'
        self.description = description
        self.date = date
        self.action_taken = action_taken
        self.created_at = datetime.now()
    
    @staticmethod
    def create(student_id, teacher_id, incident_type, description, date=None, action_taken=None):
        global _discipline_id_counter
        if date is None:
            date = datetime.now().date()
        record = DisciplineRecord(_discipline_id_counter, student_id, teacher_id, incident_type, description, date, action_taken)
        _discipline_records[_discipline_id_counter] = record
        _discipline_id_counter += 1
        return record
    
    @staticmethod
    def get(record_id):
        return _discipline_records.get(record_id)
    
    @staticmethod
    def get_by_student(student_id):
        return [record for record in _discipline_records.values() if record.student_id == student_id]
    
    @staticmethod
    def get_by_teacher(teacher_id):
        return [record for record in _discipline_records.values() if record.teacher_id == teacher_id]
    
    @staticmethod
    def get_all():
        return list(_discipline_records.values())
    
    @property
    def student(self):
        return Student.get(self.student_id)
    
    @property
    def teacher(self):
        return Teacher.get(self.teacher_id)
