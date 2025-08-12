from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
from datetime import datetime, timedelta
import secrets
import re

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.Integer, nullable=False)
    setor_id = db.Column(db.Integer, nullable=False)

    def generate_reset_token(self):
        """Generate a password reset token"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        db.session.commit()
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verify if the reset token is valid and not expired"""
        if not self.reset_token or not self.reset_token_expiry:
            return False
        if datetime.utcnow() > self.reset_token_expiry:
            return False
        return self.reset_token == token
    
    def clear_reset_token(self):
        """Clear the reset token after use"""
        self.reset_token = None
        self.reset_token_expiry = None
        db.session.commit()

class Atividade(db.Model):
    __tablename__ = 'atividade'
    
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('Pendente', 'Em andamento', 'Concluída', 'Cancelada', name='status_enum'), default='Pendente')
    prioridade = db.Column(db.Enum('Baixa', 'Média', 'Alta', 'Crítica', name='prioridade_enum'), default='Média')
    data_criada = db.Column(db.DateTime, default=datetime.utcnow)
    prazo = db.Column(db.DateTime, nullable=True)
    local = db.Column(db.String(255), nullable=False)
    setor = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    solicitante = db.Column(db.String(100), nullable=True)
    atendente = db.Column(db.String(100), nullable=True)
    
    # Relationships
    criado_por = db.relationship('User', foreign_keys=[user_id], backref='atividade_criadas')

def create_user(username, email, password, setor_id, tipo):
    hashed_password = generate_password_hash(password)
    user = User(username=username, email=email, password=hashed_password, setor_id=setor_id, tipo=tipo)
    db.session.add(user)
    db.session.commit()
    return user

def create_atividade(descricao, status, prioridade, user_id, prazo=None, local=None, setor=None, solicitante=None):
    """Create a new atividade"""
    # Parse prazo if it's a string
    if prazo and isinstance(prazo, str):
        try:
            prazo = datetime.fromisoformat(prazo.replace('T', ' '))
        except ValueError:
            prazo = None
    
    atividade = Atividade(
        descricao=descricao,
        status=status,
        prioridade=prioridade,
        user_id=user_id,
        prazo=prazo,
        local=local,
        setor=setor if setor else None,
        solicitante=solicitante if solicitante else None
    )
    db.session.add(atividade)
    db.session.commit()
    return atividade

def get_all_atividades(page=1, per_page=10):
    """Get all atividades with creator info, with pagination and custom ordering"""
    from sqlalchemy.orm import aliased
    from sqlalchemy import case
    
    # Create alias for the User table (only for creator now)
    CriadorUser = aliased(User)
    
    # Define status priority order: 'em andamento' > 'pendente' > others, 'concluído' last
    status_order = case(
        (Atividade.status == 'Concluída', 3),  # Concluído always last
        (Atividade.status == 'Em andamento', 1),  # Em andamento first
        (Atividade.status == 'Pendente', 2),  # Pendente second
        else_=2  # Other statuses with pendente
    )
    
    query = db.session.query(
        Atividade.id,
        Atividade.descricao,
        Atividade.status,
        Atividade.prioridade,
        Atividade.data_criada,
        Atividade.prazo,
        Atividade.local,
        Atividade.setor,
        CriadorUser.username.label('criado_por_nome'),
        Atividade.solicitante,
        Atividade.atendente
    ).join(
        CriadorUser, Atividade.user_id == CriadorUser.id
    ).order_by(
        db.func.isnull(Atividade.prazo),  # NULL prazo last
        Atividade.prazo.asc(),  # Order by prazo first
        status_order  # Then by status priority
    )
    
    return query.paginate(page=page, per_page=per_page, error_out=False)

def get_atividades_by_setor(setor_nome, page=1, per_page=10):
    """Get all atividades filtered by setor name, with pagination and custom ordering"""
    from sqlalchemy.orm import aliased
    from sqlalchemy import case
    
    # Create alias for the User table (only for creator now)
    CriadorUser = aliased(User)
    
    # Define status priority order: 'em andamento' > 'pendente' > others, 'concluído' last
    status_order = case(
        (Atividade.status == 'Concluída', 3),  # Concluído always last
        (Atividade.status == 'Em andamento', 1),  # Em andamento first
        (Atividade.status == 'Pendente', 2),  # Pendente second
        else_=2  # Other statuses with pendente
    )
    
    query = db.session.query(
        Atividade.id,
        Atividade.descricao,
        Atividade.status,
        Atividade.prioridade,
        Atividade.data_criada,
        Atividade.prazo,
        Atividade.local,
        Atividade.setor,
        CriadorUser.username.label('criado_por_nome'),
        Atividade.solicitante,
        Atividade.atendente
    ).join(
        CriadorUser, Atividade.user_id == CriadorUser.id
    ).filter(
        Atividade.setor == setor_nome
    ).order_by(
        db.func.isnull(Atividade.prazo),  # NULL prazo last
        Atividade.prazo.asc(),  # Order by prazo first
        status_order  # Then by status priority
    )
    
    return query.paginate(page=page, per_page=per_page, error_out=False)

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

def get_user_by_reset_token(token):
    return User.query.filter_by(reset_token=token).first()

def update_user_password(user, new_password):
    user.password = generate_password_hash(new_password)
    user.clear_reset_token()
    db.session.commit()

def init_db(app):
    with app.app_context():
        db.create_all()

# Input validation functions
def validate_username(username):
    """Validate username format and length"""
    if not username or len(username) < 3 or len(username) > 50:
        return False
    return re.match(r'^[a-zA-Z0-9_]+$', username) is not None

def validate_email(email):
    """Validate email format"""
    if not email or len(email) > 150:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if not password or len(password) < 6:
        return False
    return True

def sanitize_input(text):
    """Sanitize text input"""
    if text:
        return escape(text.strip())
    return None

class Setor(db.Model):
    __tablename__ = 'setor'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150))