import pymysql
from datetime import datetime

def migrate_database():
    """Add missing columns to the existing user table and create atividades table"""
    print("Starting database migration...")
    
    try:
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='lucasbm92',
            password='lbm291292',
            database='auth_system_db',
            connect_timeout=5
        )
        
        print("✅ Connected to database")
        
        cursor = connection.cursor()
        
        # Check current table structure
        cursor.execute("DESCRIBE user;")
        columns = cursor.fetchall()
        existing_columns = [col[0] for col in columns]
        
        print(f"Current columns: {existing_columns}")
        
        # Add missing columns to user table
        migrations = []
        
        if 'email' not in existing_columns:
            migrations.append("ALTER TABLE user ADD COLUMN email VARCHAR(150) UNIQUE")
            print("- Will add email column")
        
        if 'reset_token' not in existing_columns:
            migrations.append("ALTER TABLE user ADD COLUMN reset_token VARCHAR(100) NULL")
            print("- Will add reset_token column")
        
        if 'reset_token_expiry' not in existing_columns:
            migrations.append("ALTER TABLE user ADD COLUMN reset_token_expiry DATETIME NULL")
            print("- Will add reset_token_expiry column")
        
        if 'created_at' not in existing_columns:
            migrations.append("ALTER TABLE user ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            print("- Will add created_at column")
        
        if not migrations:
            print("✅ No migrations needed for user table - table is up to date")
        else:
            # Execute user table migrations
            for migration in migrations:
                try:
                    cursor.execute(migration)
                    print(f"✅ Executed: {migration}")
                except Exception as e:
                    print(f"❌ Error executing {migration}: {e}")
        
        # Check if atividades table exists
        cursor.execute("SHOW TABLES LIKE 'atividades';")
        atividades_exists = cursor.fetchone()
        
        if not atividades_exists:
            print("Creating atividades table...")
            create_atividades_table = """
            CREATE TABLE atividades (
                id INT AUTO_INCREMENT PRIMARY KEY,
                descricao TEXT NOT NULL,
                status ENUM('Pendente', 'Em andamento', 'Concluída', 'Cancelada') DEFAULT 'Pendente',
                prioridade ENUM('Baixa', 'Média', 'Alta', 'Crítica') DEFAULT 'Média',
                data_criada DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_prevista DATETIME NULL,
                localizacao VARCHAR(255) NULL,
                criado_por_id INT NOT NULL,
                responsavel_id INT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (criado_por_id) REFERENCES user(id) ON DELETE CASCADE,
                FOREIGN KEY (responsavel_id) REFERENCES user(id) ON DELETE SET NULL
            )
            """
            try:
                cursor.execute(create_atividades_table)
                print("✅ Created atividades table successfully!")
            except Exception as e:
                print(f"❌ Error creating atividades table: {e}")
        else:
            print("✅ Atividades table already exists")
        
        connection.commit()
        print("✅ Database migration completed successfully!")
        
        # Show final table structures
        cursor.execute("DESCRIBE user;")
        columns = cursor.fetchall()
        print("\nUser table structure:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")
        
        cursor.execute("DESCRIBE atividades;")
        columns = cursor.fetchall()
        print("\nAtividades table structure:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_database()
