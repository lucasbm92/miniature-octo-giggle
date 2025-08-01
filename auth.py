from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from models import (get_user_by_username, get_user_by_email, create_user, 
                   get_user_by_reset_token, update_user_password, create_atividade, 
                   get_all_atividades, Atividade, db)

auth_blueprint = Blueprint('auth', __name__)

# Initialize Mail (will be configured in app.py)
mail = Mail()

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect logged-in users to dashboard
    if 'user_id' in session:
        return redirect(url_for('auth.index'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
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
        
        create_user(username, email, password)
        flash('Cadastro realizado com sucesso! Faça o login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

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
    
    # Get all atividades from database
    atividades = get_all_atividades()
    
    return render_template('index.html', username=session.get('username'), atividades=atividades)

@auth_blueprint.route('/new-task', methods=['GET', 'POST'])
def new_task():
    if 'user_id' not in session:
        flash('Por favor, faça login para acessar esta página', 'warning')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Get form data
        descricao = request.form['descricao']
        prioridade = request.form['prioridade']
        prazo = request.form.get('prazo')
        local = request.form.get('local')
        setor = request.form.get('setor')
        responsavel_nome = request.form.get('responsavel_nome')
        
        # Basic validation
        if not descricao or not prioridade or not local:
            flash('Descrição, Prioridade e Local são obrigatórios', 'warning')
            return redirect(url_for('auth.new_task'))
        
        try:
            from datetime import datetime, timedelta
            if prioridade == 'Baixa':
                prazo_value = datetime.now() + timedelta(days=15)
            elif prioridade == 'Média':
                prazo_value = datetime.now() + timedelta(days=10)
            elif prioridade == 'Alta':
                prazo_value = datetime.now() + timedelta(days=5)
            else:
                prazo_value = datetime.now() + timedelta(days=2)

            create_atividade(
                descricao=descricao,
                status='Pendente',
                prioridade=prioridade,
                prazo=prazo_value,
                criado_por_id=session['user_id'],
                local=local.strip() if local else None,
                setor=setor.strip() if setor else None,
                responsavel_nome=responsavel_nome.strip() if responsavel_nome else None
            )
            flash('Atividade criada com sucesso!', 'success')
            return redirect(url_for('auth.index'))
        except Exception as e:
            flash(f'Erro ao criar atividade: {str(e)}', 'error')
            return redirect(url_for('auth.new_task'))
    
    return render_template('newtask.html', username=session.get('username'))

@auth_blueprint.route('/update-status/<int:atividade_id>/<new_status>')
def update_status(atividade_id, new_status):
    if 'user_id' not in session:
        flash('Por favor, faça login para acessar esta página', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        # Get the atividade from database
        atividade = Atividade.query.get_or_404(atividade_id)
        
        # Update the status
        atividade.status = new_status
        db.session.commit()
        
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
        # Get the atividade from database
        atividade = Atividade.query.get_or_404(atividade_id)
        
        # Check if the current user is the creator (optional security check)
        if atividade.criado_por_id != session['user_id']:
            flash('Você só pode excluir atividades que você criou', 'warning')
            return redirect(url_for('auth.index'))
        
        # Delete the atividade
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
    try:
        print(f"Attempting to send email to: {email}")
        print(f"SMTP Server: {current_app.config['MAIL_SERVER']}")
        print(f"SMTP Port: {current_app.config['MAIL_PORT']}")
        print(f"SMTP TLS: {current_app.config.get('MAIL_USE_TLS')}")
        print(f"SMTP SSL: {current_app.config.get('MAIL_USE_SSL')}")
        print(f"SMTP Username: {current_app.config['MAIL_USERNAME']}")

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
        
        print("Testing SMTP connection...")
        with mail.connect() as conn:
            print("SMTP connection successful, sending email...")
            conn.send(msg)
        print(f"✅ Password reset email sent successfully to {email}")
        print(f"Reset URL: {reset_url}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        print(f"Error type: {type(e).__name__}")
        # For development/fallback, always print the reset URL to console
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        print(f"\n{'='*60}")
        print(f"PASSWORD RESET URL (copy this link):")
        print(f"{reset_url}")
        print(f"{'='*60}\n")
        return False
