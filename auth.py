#!/usr/bin/env python3
"""
Módulo de Autenticação - Gestor de Tarefas
Desenvolvido por Lucas Brito Marinho
Copyright (c) 2025

Gerencia autenticação de usuários, registro, gerenciamento de senhas,
gestão de tarefas com controle de acesso baseado em papéis e notificações em tempo real
"""

from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from flask_mail import Mail, Message
from flask_socketio import emit
from werkzeug.security import generate_password_hash, check_password_hash
from models import (get_user_by_username, get_user_by_email, create_user, 
                   get_user_by_reset_token, update_user_password, create_atividade, 
                   get_all_atividades, get_atividades_by_setor, Atividade, db)
import logging

auth_blueprint = Blueprint('auth', __name__)

# Initialize Mail (will be configured in app.py)
mail = Mail()

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect logged-in users to dashboard
    if 'user_id' in session:
        return redirect(url_for('auth.index'))
    from models import Setor
    setores = Setor.query.all()
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        setor_id = request.form['setor_id']
        tipo = 2
        
        # Validation
        if password != confirm_password:
            flash('As senhas não coincidem', 'error')
            return redirect(url_for('auth.register'))
        
        if get_user_by_username(username):
            flash('Nome de usuário já existe', 'error')
            return redirect(url_for('auth.register'))
        
        if get_user_by_email(email):
            flash('Email já está cadastrado', 'error')
            return redirect(url_for('auth.register'))
        
        create_user(username, email, password, setor_id, tipo)
        flash('Cadastro realizado com sucesso! Faça o login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', setores=setores)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect logged-in users to dashboard
    if 'user_id' in session:
        return redirect(url_for('auth.index'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_user_by_email(email)
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['email'] = user.email
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('auth.index'))
        flash('Credenciais inválidas', 'error')
        return redirect(url_for('auth.login'))
    return render_template('login.html')

@auth_blueprint.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('email', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('auth.login'))

@auth_blueprint.route('/')
def index():
    if 'user_id' not in session:
        flash('Por favor, faça login para acessar esta página', 'warning')
        return redirect(url_for('auth.login'))
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 10 tasks per page
    
    # Get the current user object
    from models import User, Setor
    user = User.query.get(session['user_id'])
    
    # Filter atividades based on user type
    user_setor_nome = None
    if user and getattr(user, 'tipo', None) == 2:
        # For tipo 2 users, only show tasks from their setor
        user_setor = Setor.query.get(user.setor_id)
        if user_setor:
            user_setor_nome = user_setor.nome
            # Get paginated tasks that match the user's setor name
            pagination = get_atividades_by_setor(user_setor.nome, page=page, per_page=per_page)
        else:
            # Create empty pagination object
            from sqlalchemy import text
            empty_query = db.session.query(text('1')).filter(text('1=0'))
            pagination = empty_query.paginate(page=page, per_page=per_page, error_out=False)
    else:
        # For tipo 1 users, show all tasks with pagination
        pagination = get_all_atividades(page=page, per_page=per_page)
    
    atividades = pagination.items
    
    return render_template('index.html', 
                         atividades=atividades, 
                         pagination=pagination,
                         user=user, 
                         user_setor=user_setor_nome)

@auth_blueprint.route('/new-task', methods=['GET', 'POST'])
def new_task():
    if 'user_id' not in session:
        flash('Por favor, faça login para acessar esta página', 'warning')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Get form data
        descricao = request.form['descricao']
        prioridade = request.form['prioridade']
        local = request.form.get('local')
        setor = request.form.get('setor')
        solicitante = request.form.get('solicitante')
        
        # Get current user to check tipo and setor_id
        from models import User, Setor
        current_user = User.query.get(session['user_id'])
        
        # If user tipo is 2, force setor to be the user's setor name
        if current_user and getattr(current_user, 'tipo', None) == 2:
            user_setor = Setor.query.get(current_user.setor_id)
            expected_setor = user_setor.nome if user_setor else None
            
            # Validate that tipo 2 users can only create tasks in their own sector
            if setor and setor.strip() != expected_setor:
                flash('Você só pode criar atividades no seu próprio setor.', 'error')
                return redirect(url_for('auth.new_task'))
            
            # Force correct values for tipo 2 users
            setor = expected_setor
            local = "CAM 2"
            solicitante = current_user.username
        
        # Basic validation
        if not descricao or not prioridade or not local:
            flash('Descrição, Prioridade e Local são obrigatórios', 'warning')
            return redirect(url_for('auth.new_task'))
        
        try:
            new_atividade = create_atividade(
                descricao=descricao,
                status='Pendente',
                prioridade=prioridade,
                user_id=session['user_id'],
                local=local.strip() if local else None,
                setor=setor.strip() if setor else None,
                solicitante=solicitante.strip() if solicitante else None
            )
            
            # Emit notification to admin users (tipo==1) if task was created by tipo==2 user
            if current_user and getattr(current_user, 'tipo', None) == 2:
                try:
                    # Import here to avoid circular imports
                    from flask import current_app
                    socketio = current_app.extensions.get('socketio')
                    if socketio:
                        # Send complete data including the new activity ID
                        from datetime import datetime
                        socketio.emit('new_task_notification', {
                            'atividade_id': new_atividade.id,
                            'descricao': descricao,
                            'local': local.strip() if local else 'Não especificado',
                            'setor': setor.strip() if setor else '-',
                            'criado_por_nome': current_user.username,
                            'solicitante': solicitante.strip() if solicitante else 'Não atribuído',
                            'atendente': '-',
                            'prioridade': prioridade,
                            'data_criada': datetime.now().strftime('%d/%m/%Y'),
                            'prazo': 'Não definido',
                            'status': 'Pendente',
                            'message': f'Nova tarefa criada por {solicitante} no setor {setor}'
                        }, room='admin_room')
                except Exception as socket_error:
                    from flask import current_app
                    current_app.logger.warning(f"Error sending WebSocket notification: {socket_error}")
            
            flash('Atividade criada com sucesso!', 'success')
            return redirect(url_for('auth.index'))
        except Exception as e:
            flash(f'Erro ao criar atividade: {str(e)}', 'error')
            return redirect(url_for('auth.new_task'))
    
    # Get current user to pass to template
    from models import User
    current_user = User.query.get(session['user_id'])
    
    return render_template('newtask.html', username=session.get('username'), user=current_user)

@auth_blueprint.route('/update-status/<int:atividade_id>/<new_status>')
def update_status(atividade_id, new_status):
    if 'user_id' not in session:
        flash('Por favor, faça login para acessar esta página', 'warning')
        return redirect(url_for('auth.login'))
    try:
        atividade = Atividade.query.get_or_404(atividade_id)
        from models import User
        user = User.query.get(session['user_id'])
        if user and getattr(user, 'tipo', None) == 2:
            flash('Você não tem permissão para atualizar atividades.', 'warning')
            return redirect(url_for('auth.index'))
        # Set prazo when moving from Pendente to Em andamento
        if atividade.status == 'Pendente' and new_status == 'Em andamento':
            from datetime import datetime, timedelta
            # Set prazo based on prioridade
            if atividade.prioridade == 'Baixa':
                atividade.prazo = datetime.now() + timedelta(days=15)
            elif atividade.prioridade == 'Média':
                atividade.prazo = datetime.now() + timedelta(days=10)
            elif atividade.prioridade == 'Alta':
                atividade.prazo = datetime.now() + timedelta(days=5)
            elif atividade.prioridade == 'Crítica':
                atividade.prazo = datetime.now() + timedelta(days=2)
            # Set atendente to current user's username
            current_user = User.query.get(session['user_id'])
            if current_user:
                atividade.atendente = current_user.username
        atividade.status = new_status
        db.session.commit()
        
        # Emit notification to tipo==2 users when their activities are updated
        try:
            # Import here to avoid circular imports
            from flask import current_app
            socketio = current_app.extensions.get('socketio')
            if socketio:
                # Get the setor of the updated activity
                setor_room = f"setor_{atividade.setor}" if atividade.setor else None
                
                if setor_room:
                    socketio.emit('activity_update_notification', {
                        'atividade_id': atividade.id,
                        'descricao': atividade.descricao,
                        'status': new_status,
                        'prioridade': atividade.prioridade,
                        'setor': atividade.setor,
                        'atendente': atividade.atendente,
                        'prazo': atividade.prazo.strftime('%d/%m/%Y') if atividade.prazo else 'Não definido',
                        'message': f'Atividade "{atividade.descricao[:50]}..." foi atualizada para "{new_status}"'
                    }, room=setor_room)
        except Exception as socket_error:
            from flask import current_app
            current_app.logger.warning(f"Error sending WebSocket notification: {socket_error}")
        
        flash(f'Status da atividade atualizado para "{new_status}" com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar status: {str(e)}', 'error')
    return redirect(url_for('auth.index'))

@auth_blueprint.route('/delete-atividade/<int:atividade_id>')
def delete_atividade(atividade_id):
    if 'user_id' not in session:
        flash('Por favor, faça login para acessar esta página', 'warning')
        return redirect(url_for('auth.login'))
    try:
        atividade = Atividade.query.get_or_404(atividade_id)
        from models import User
        user = User.query.get(session['user_id'])
        if user and getattr(user, 'tipo', None) == 2:
            flash('Você não tem permissão para excluir atividades.', 'warning')
            return redirect(url_for('auth.index'))
        # Only restrict tipo==2 users, tipo==1 can delete any task
        # Remove creator check for tipo==1
        db.session.delete(atividade)
        db.session.commit()
        flash('Atividade excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir atividade: {str(e)}', 'error')
    return redirect(url_for('auth.index'))

@auth_blueprint.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        flash('Por favor, faça login para acessar esta página', 'warning')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        user = get_user_by_email(session.get('email', ''))
        
        if not user:
            flash('Sessão expirada. Faça login novamente.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not check_password_hash(user.password, current_password):
            flash('Senha atual incorreta', 'error')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('As novas senhas não coincidem', 'error')
            return redirect(url_for('auth.change_password'))
        
        if len(new_password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres', 'error')
            return redirect(url_for('auth.change_password'))
        
        update_user_password(user, new_password)
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('auth.index'))
    
    return render_template('change_password.html')

@auth_blueprint.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    # Redirect logged-in users to change password instead
    if 'user_id' in session:
        return redirect(url_for('auth.change_password'))
    
    if request.method == 'POST':
        email = request.form['email']
        user = get_user_by_email(email)
        
        if user:
            token = user.generate_reset_token()
            send_reset_email(user.email, token)
            flash('Instruções para redefinir a senha foram enviadas para seu email.', 'info')
        else:
            flash('Email não encontrado.', 'error')
        
        return redirect(url_for('auth.login'))
    
    return render_template('forgot_password.html')

@auth_blueprint.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = get_user_by_reset_token(token)
    
    if not user or not user.verify_reset_token(token):
        flash('Token de redefinição inválido ou expirado.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('As senhas não coincidem', 'error')
            return redirect(url_for('auth.reset_password', token=token))
        
        if len(new_password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres', 'error')
            return redirect(url_for('auth.reset_password', token=token))
        
        update_user_password(user, new_password)
        flash('Senha redefinida com sucesso! Faça o login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', token=token)

def send_reset_email(email, token):
    """Send password reset email"""
    from flask import current_app
    
    # Get logger
    logger = current_app.logger
    
    try:
        logger.info(f"Attempting to send password reset email to: {email}")
        logger.debug(f"SMTP Server: {current_app.config['MAIL_SERVER']}")
        logger.debug(f"SMTP Port: {current_app.config['MAIL_PORT']}")
        logger.debug("SMTP configuration loaded successfully")

        msg = Message(
            subject='Password Reset Request',
            recipients=[email]
        )
        
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        
        msg.body = f"""
        You have requested a password reset for your account.
        
        Click the following link to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you did not make this request, please ignore this email.
        """
        
        msg.html = f"""
        <h3>Password Reset Request</h3>
        <p>You have requested a password reset for your account.</p>
        <p><a href=\"{reset_url}\">Click here to reset your password</a></p>
        <p>This link will expire in 1 hour.</p>
        <p>If you did not make this request, please ignore this email.</p>
        """
        
        logger.debug("Testing SMTP connection...")
        with mail.connect() as conn:
            logger.debug("SMTP connection successful, sending email...")
            conn.send(msg)
        logger.info(f"Password reset email sent successfully to: {email}")
        # Password reset URL logging removed for security
        return True
    except Exception as e:
        logger.error(f"Error sending password reset email to {email}: {e}")
        logger.debug(f"Error type: {type(e).__name__}")
        # For security reasons, password reset URLs are not logged to console in production
        # If email fails, users should use the forgot password form again
        return False
