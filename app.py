from flask import Flask
from auth import auth_blueprint, mail
from models import db, init_db
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Flask configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

if __name__ == '__main__':
    app.run(debug=True)
