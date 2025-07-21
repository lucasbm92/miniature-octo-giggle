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
            database='miniature_octo_giggle',
            connect_timeout=5
        )
        
        print("✅ Connected to database")
        
        cursor = connection.cursor()
        
        # Check if user table exists, create if it doesn't
        cursor.execute("SHOW TABLES LIKE 'user';")
        user_table_exists = cursor.fetchone()
        
        if not user_table_exists:
            print("Creating user table...")
            create_user_table = """
            CREATE TABLE user (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(150) UNIQUE NOT NULL,
                email VARCHAR(150) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                reset_token VARCHAR(100) NULL,
                reset_token_expiry DATETIME NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            try:
                cursor.execute(create_user_table)
                print("✅ Created user table successfully!")
            except Exception as e:
                print(f"❌ Error creating user table: {e}")
                return
        else:
            print("✅ User table already exists")
        
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
                responsavel_nome VARCHAR(100) NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (criado_por_id) REFERENCES user(id) ON DELETE CASCADE
            )
            """
            try:
                cursor.execute(create_atividades_table)
                print("✅ Created atividades table successfully!")
            except Exception as e:
                print(f"❌ Error creating atividades table: {e}")
        else:
            print("✅ Atividades table already exists")
            # Check if we need to update the responsavel field
            cursor.execute("SHOW COLUMNS FROM atividades LIKE 'responsavel_id';")
            responsavel_id_exists = cursor.fetchone()
            cursor.execute("SHOW COLUMNS FROM atividades LIKE 'responsavel_nome';")
            responsavel_nome_exists = cursor.fetchone()
            
            if responsavel_id_exists and not responsavel_nome_exists:
                print("Updating atividades table structure - changing responsavel from ID to nome...")
                try:
                    # Add the new column
                    cursor.execute("ALTER TABLE atividades ADD COLUMN responsavel_nome VARCHAR(100) NULL;")
                    print("✅ Added responsavel_nome column")
                    
                    # Migrate existing data (copy usernames from responsavel relationship)
                    migrate_responsavel_data = """
                    UPDATE atividades a 
                    LEFT JOIN user u ON a.responsavel_id = u.id 
                    SET a.responsavel_nome = u.username 
                    WHERE a.responsavel_id IS NOT NULL;
                    """
                    cursor.execute(migrate_responsavel_data)
                    print("✅ Migrated existing responsavel data")
                    
                    # Drop the foreign key constraint first
                    cursor.execute("ALTER TABLE atividades DROP FOREIGN KEY atividades_ibfk_2;")
                    print("✅ Dropped foreign key constraint")
                    
                    # Drop the old column
                    cursor.execute("ALTER TABLE atividades DROP COLUMN responsavel_id;")
                    print("✅ Dropped responsavel_id column")
                    
                except Exception as e:
                    print(f"❌ Error updating atividades table: {e}")
            elif responsavel_nome_exists:
                print("✅ Atividades table already has responsavel_nome field")
        
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
