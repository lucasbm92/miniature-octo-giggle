#!/usr/bin/env python3
"""
Gestor de Tarefas - Task Management System
Developed by Lucas Brito Marinho
Copyright (c) 2025

A web-based task management system built with Flask
Features: User authentication, task management, real-time notifications, role-based access
"""

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
from auth import auth_blueprint, mail
from models import db, init_db
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

# Production configuration
app.config['DEBUG'] = False
app.config['TESTING'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # Must be secure!
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Store socketio in app extensions for access from blueprints
app.extensions['socketio'] = socketio

# Security headers
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))

# Add timeout settings for better error handling
app.config['MAIL_TIMEOUT'] = 30
app.config['MAIL_DEBUG'] = True

# Initialize extensions
db.init_app(app)
mail.init_app(app)
init_db(app)

app.register_blueprint(auth_blueprint)

# WebSocket events
@socketio.on('connect')
def on_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def on_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('join_admin_room')
def on_join_admin_room():
    """Join room for admin users (tipo==1) to receive notifications"""
    join_room('admin_room')
    emit('status', {'msg': 'Joined admin notification room'})

@socketio.on('join_setor_room')
def on_join_setor_room(data):
    """Join room for tipo==2 users to receive sector-specific notifications"""
    setor = data.get('setor')
    if setor:
        setor_room = f"setor_{setor}"
        join_room(setor_room)
        emit('status', {'msg': f'Joined sector room: {setor_room}'})

# Favicon route
@app.route('/favicon.ico')
def favicon():
    from flask import send_from_directory
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'), 
                              'brasao.svg', mimetype='image/svg+xml')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Logging setup
if not app.debug and not os.path.exists('logs'):
    os.mkdir('logs')
    
if not app.debug:
    file_handler = RotatingFileHandler('logs/gestor_tarefas.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Gestor de Tarefas startup')

# if __name__ == '__main__':
#     app.run(debug=True)
if __name__ == '__main__':
    # Check environment
    if os.getenv('FLASK_ENV') != 'production':
        print("Warning: Not running in production mode!")
    
    print("Starting Gestor de Tarefas")
    print("Access at: http://localhost:5000 or http://YOUR_IP:5000")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)