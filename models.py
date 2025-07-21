from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    __tablename__ = 'atividades'
    
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('Pendente', 'Em andamento', 'Concluída', 'Cancelada', name='status_enum'), default='Pendente')
    prioridade = db.Column(db.Enum('Baixa', 'Média', 'Alta', 'Crítica', name='prioridade_enum'), default='Média')
    data_criada = db.Column(db.DateTime, default=datetime.utcnow)
    data_prevista = db.Column(db.DateTime, nullable=True)
    localizacao = db.Column(db.String(255), nullable=True)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    responsavel_nome = db.Column(db.String(100), nullable=True)
    
    # Relationships
    criado_por = db.relationship('User', foreign_keys=[criado_por_id], backref='atividades_criadas')

def create_user(username, email, password):
    hashed_password = generate_password_hash(password)
    user = User(username=username, email=email, password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return user

def create_atividade(descricao, status, prioridade, criado_por_id, data_prevista=None, localizacao=None, responsavel_nome=None):
    """Create a new atividade"""
    # Parse data_prevista if it's a string
    if data_prevista and isinstance(data_prevista, str):
        try:
            data_prevista = datetime.fromisoformat(data_prevista.replace('T', ' '))
        except ValueError:
            data_prevista = None
    
    atividade = Atividade(
        descricao=descricao,
        status=status,
        prioridade=prioridade,
        criado_por_id=criado_por_id,
        data_prevista=data_prevista,
        localizacao=localizacao,
        responsavel_nome=responsavel_nome if responsavel_nome else None
    )
    db.session.add(atividade)
    db.session.commit()
    return atividade

def get_all_atividades():
    """Get all atividades with creator info"""
    from sqlalchemy.orm import aliased
    
    # Create alias for the User table (only for creator now)
    CriadorUser = aliased(User)
    
    return db.session.query(
        Atividade.id,
        Atividade.descricao,
        Atividade.status,
        Atividade.prioridade,
        Atividade.data_criada,
        Atividade.data_prevista,
        Atividade.localizacao,
        CriadorUser.username.label('criado_por_nome'),
        Atividade.responsavel_nome
    ).join(
        CriadorUser, Atividade.criado_por_id == CriadorUser.id
    ).all()

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
        print('Database initialized.')
