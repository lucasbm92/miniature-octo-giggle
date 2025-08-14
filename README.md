# Gestor de Tarefas

A Flask-based task management web application that provides user authentication and activity tracking capabilities. The application features a complete user management system with registration, login, password reset functionality, and a comprehensive task management interface.

## ✨ Features

### User Management
- **User Registration** - Create new accounts with email verification
- **Secure Login/Logout** - Session-based authentication
- **Password Reset** - Email-based password recovery system
- **Profile Management** - Change password functionality

### Task Management
- **Task Creation** - Create tasks with description, priority, and deadlines
- **Priority System** - Four levels: Baixa, Média, Alta, Crítica with color coding
- **Status Workflow** - Pendente → Em andamento → Concluída → Cancelada
- **Automatic Deadlines** - Based on priority levels (15, 10, 5, 2 days)
- **Task Assignment** - Assign tasks to responsible persons
- **Location Tracking** - Specify task locations

### Interface
- **Responsive Design** - Bootstrap 5 interface works on all devices
- **Real-time Updates** - Dynamic status changes and task management
- **Intuitive Navigation** - Clean, user-friendly interface
- **Network Access** - Multi-user support on local network

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Database**: MySQL with SQLAlchemy ORM
- **Frontend**: HTML5, Bootstrap 5, Jinja2 templates
- **Email**: Flask-Mail for notifications
- **Security**: Werkzeug password hashing, session management
- **Deployment**: Gunicorn WSGI server ready

## 📋 Requirements

- Python 3.7+
- MySQL 5.7+
- pip (Python package manager)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/lucasbm92/miniature-octo-giggle.git
cd miniature-octo-giggle
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy the example environment file
copy .env.example .env

# Edit .env with your settings:
# - Generate SECRET_KEY: python -c "import secrets; print(secrets.token_hex(32))"
# - Update database credentials
# - Configure email settings
```

### 4. Setup Database
```bash
# Run the database migration
python migrate_db.py
```

### 5. Start the Application
```bash
# Development mode
python app.py

# Production mode
python start_production.py
```

### 6. Access the Application
- **Local**: http://localhost:5000
- **Network**: http://YOUR_IP:5000

## 🌐 Network Deployment

For multi-user access on your local network:

1. **Find your IP address**:
   ```cmd
   ipconfig
   ```

2. **Configure firewall** to allow Python/port 5000

3. **Access from other devices**: `http://YOUR_SERVER_IP:5000`

4. **Users can register and login** from any device on the network

## ⚙️ Configuration

### Environment Variables (.env)
```env
SECRET_KEY=your-64-character-secret-key
SQLALCHEMY_DATABASE_URI=mysql+pymysql://user:password@localhost:3306/database
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-email-password
FLASK_ENV=production
```

### Database Setup
```sql
CREATE DATABASE gestor_tarefas;
-- Update .env with your database credentials
```

## 📝 Usage

### Getting Started
1. **Register** a new account with username, email, and password
2. **Login** with your credentials
3. **Create tasks** using the "+" button
4. **Manage tasks** with priority levels and deadlines
5. **Track progress** through status updates

### Task Workflow
1. **Create** → Task starts as "Pendente"
2. **Start** → Change to "Em andamento"  
3. **Complete** → Mark as "Concluída"
4. **Delete** → Remove completed or unwanted tasks

### Priority Levels
- **Baixa** (Low) - 15 days deadline
- **Média** (Medium) - 10 days deadline
- **Alta** (High) - 5 days deadline
- **Crítica** (Critical) - 2 days deadline

## 🔧 Development

### Project Structure
```
miniature-octo-giggle/
├── app.py              # Flask application entry point
├── auth.py             # Authentication routes and logic
├── models.py           # Database models and functions
├── migrate_db.py       # Database migration script
├── backup.py           # Database backup utility
├── start_production.py # Production startup script
├── templates/          # HTML templates
├── static/            # Static files (CSS, JS, images)
├── logs/              # Application logs
└── backups/           # Database backups
```

### Adding Features
1. **Models**: Add new database models in `models.py`
2. **Routes**: Add new routes in `auth.py` or create new blueprints
3. **Templates**: Create HTML templates in `templates/`
4. **Migrations**: Run `migrate_db.py` for database changes

## 🔒 Security Features

- **Password Hashing** - Werkzeug secure password storage
- **Session Management** - Flask session handling
- **Input Validation** - Form validation and sanitization
- **Error Handling** - Graceful error pages and logging
- **Security Headers** - XSS protection, content type sniffing prevention

## 📊 Backup & Maintenance

### Database Backup
```bash
# Create backup
python backup.py

# Backups are stored in backups/ directory
```

### Log Monitoring
```bash
# View application logs
tail -f logs/gestor_tarefas.log
```

## 🐛 Troubleshooting

### Common Issues

**Can't access from other computers:**
- Check firewall settings
- Verify app is running with `host='0.0.0.0'`
- Confirm IP address is correct

**Database connection errors:**
- Verify credentials in `.env`
- Check MySQL service is running
- Test database connectivity

**Email not working:**
- Verify email settings in `.env`
- Check email provider security settings
- Test SMTP connectivity

## 📈 Future Enhancements

- [ ] Task categories and tags
- [ ] Due date notifications
- [ ] File attachments
- [ ] Task comments and history
- [ ] Export functionality (PDF, Excel)
- [ ] Mobile app
- [ ] REST API
- [ ] Advanced reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Lucas Brito Marinho** - [lucasbm92](https://github.com/lucasbm92)

## 🙏 Acknowledgments

- Flask framework and community
- Bootstrap for responsive UI components
- MySQL for reliable data storage
- Contributors and testers

---

**Ready for production use!** 🚀

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)