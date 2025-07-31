#!/usr/bin/env python3
"""
Production startup script for Gestor de Tarefas
Run this file to start the application in production mode
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Check if all required environment variables are set"""
    load_dotenv()
    
    required_vars = [
        'SECRET_KEY',
        'SQLALCHEMY_DATABASE_URI',
        'MAIL_USERNAME',
        'MAIL_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease update your .env file with the required variables.")
        print("See .env.example for reference.")
        return False
    
    return True

def start_production():
    """Start the production server"""
    print("🚀 Starting Gestor de Tarefas - Production Mode")
    print("=" * 50)
    
    # Check environment variables
    if not check_environment():
        sys.exit(1)
    
    # Get server configuration
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    
    print(f"📡 Server will start on: http://{host}:{port}")
    print("🔒 Running in production mode (DEBUG=False)")
    print("📁 Logs will be saved to: logs/gestor_tarefas.log")
    print("\n⚠️  Security Notes:")
    print("   - Make sure your firewall is properly configured")
    print("   - Ensure strong passwords are used")
    print("   - Regular backups are recommended")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        from app import app
        app.run(
            host=host,
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    start_production()
