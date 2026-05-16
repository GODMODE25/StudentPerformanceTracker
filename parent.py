from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import User, Message
from app import db

parent_bp = Blueprint('parent', __name__, url_prefix='/parent')

@parent_bp.route('/messages')
@login_required
def messages():
    # Assuming current_user is a parent
    received_messages = Message.query.filter_by(recipient_id=current_user.id).all()
    sent_messages = Message.query.filter_by(sender_id=current_user.id).all()
    return render_template('parent/messages.html', received_messages=received_messages, sent_messages=sent_messages)

@parent_bp.route('/send_message', methods=['GET', 'POST'])
@login_required
def send_message():
    if request.method == 'POST':
        recipient_id = request.form.get('recipient_id')
        subject = request.form.get('subject')
        body = request.form.get('body')

        if not recipient_id or not subject or not body:
            flash('All fields are required.')
            return redirect(url_for('parent.send_message'))

        recipient = User.query.get(recipient_id)
        if not recipient:
            flash('Recipient not found.')
            return redirect(url_for('parent.send_message'))

        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient.id,
            subject=subject,
            body=body
        )
        db.session.add(message)
        db.session.commit()
        flash('Message sent successfully.')
        return redirect(url_for('parent.messages'))

    # GET request
    recipients = User.query.filter(User.role.in_(['admin', 'teacher'])).all()
    return render_template('parent/send_message.html', recipients=recipients)