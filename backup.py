import os
import subprocess
from datetime import datetime

def backup_database():
    """Create a backup of the production database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create backups directory if it doesn't exist
    if not os.path.exists('backups'):
        os.makedirs('backups')
    
    backup_file = f"backups/backup_gestor_tarefas_{timestamp}.sql"
    
    # Get database credentials from environment
    from dotenv import load_dotenv
    load_dotenv()
    
    db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
    if not db_uri:
        print("Error: Database URI not found in environment variables")
        return
    
    # Parse database URI (mysql+pymysql://user:password@host:port/database)
    try:
        # Extract components from URI
        import re
        pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
        match = re.match(pattern, db_uri)
        
        if match:
            user, password, host, port, database = match.groups()
            
            # Create mysqldump command
            cmd = [
                'mysqldump',
                f'-h{host}',
                f'-P{port}',
                f'-u{user}',
                f'-p{password}',
                database
            ]
            
            # Execute backup
            with open(backup_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                print(f"✅ Database backup created successfully: {backup_file}")
                
                # Get file size
                size = os.path.getsize(backup_file)
                print(f"   Backup size: {size:,} bytes")
            else:
                print(f"❌ Backup failed: {result.stderr}")
                # Remove empty backup file
                if os.path.exists(backup_file):
                    os.remove(backup_file)
        else:
            print("Error: Could not parse database URI")
            
    except Exception as e:
        print(f"❌ Backup failed with error: {e}")

def cleanup_old_backups(days_to_keep=7):
    """Remove backup files older than specified days"""
    if not os.path.exists('backups'):
        return
    
    import time
    current_time = time.time()
    cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
    
    removed_count = 0
    for filename in os.listdir('backups'):
        if filename.startswith('backup_') and filename.endswith('.sql'):
            filepath = os.path.join('backups', filename)
            if os.path.getmtime(filepath) < cutoff_time:
                os.remove(filepath)
                removed_count += 1
    
    if removed_count > 0:
        print(f"🗑️  Removed {removed_count} old backup(s)")

if __name__ == '__main__':
    print("Gestor de Tarefas - Database Backup")
    print("=" * 40)
    
    backup_database()
    cleanup_old_backups()
    
    print("\nBackup process completed!")
