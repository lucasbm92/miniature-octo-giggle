import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment variables"""
    return os.getenv('SQLALCHEMY_DATABASE_URI')

def migrate_database():
    """Migrate database from localizacao to local and setor fields"""
    
    db_url = get_database_url()
    if not db_url:
        print("❌ Error: SQLALCHEMY_DATABASE_URI not found in .env file")
        return False
    
    try:
        # Create engine using the same connection string as Flask app
        engine = create_engine(db_url)
        
        print("🔄 Starting database migration...")
        print(f"📊 Database URL: {db_url.split('@')[1] if '@' in db_url else 'hidden'}")
        
        with engine.connect() as connection:
            # Start transaction
            trans = connection.begin()
            
            try:
                # Check if the migration has already been done
                result = connection.execute(text("SHOW COLUMNS FROM atividades LIKE 'local'"))
                if result.fetchone():
                    print("✅ Migration already completed - 'local' field already exists")
                    return True
                
                print("📋 Step 1: Adding new 'local' and 'setor' columns...")
                
                # Add the new columns
                connection.execute(text("""
                    ALTER TABLE atividades 
                    ADD COLUMN local VARCHAR(255) NOT NULL DEFAULT '',
                    ADD COLUMN setor VARCHAR(100) NULL
                """))
                
                print("📋 Step 2: Migrating data from 'localizacao' to 'local'...")
                
                # Migrate existing data (copy localizacao to local)
                connection.execute(text("""
                    UPDATE atividades 
                    SET local = COALESCE(localizacao, 'Não especificado')
                    WHERE localizacao IS NOT NULL
                """))
                
                # For any remaining NULL or empty localizacao values
                connection.execute(text("""
                    UPDATE atividades 
                    SET local = 'Local não especificado'
                    WHERE local = '' OR local IS NULL
                """))
                
                print("📋 Step 3: Removing default constraint from 'local' column...")
                
                # Remove the default value constraint
                connection.execute(text("""
                    ALTER TABLE atividades 
                    ALTER COLUMN local DROP DEFAULT
                """))
                
                print("📋 Step 4: Dropping old 'localizacao' column...")
                
                # Drop the old column
                connection.execute(text("ALTER TABLE atividades DROP COLUMN localizacao"))
                
                # Commit the transaction
                trans.commit()
                
                print("✅ Database migration completed successfully!")
                print("📊 Changes made:")
                print("   - Added 'local' column (VARCHAR(255), NOT NULL)")
                print("   - Added 'setor' column (VARCHAR(100), NULL)")
                print("   - Migrated data from 'localizacao' to 'local'")
                print("   - Removed 'localizacao' column")
                
                return True
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Error during migration: {e}")
                return False
                
    except SQLAlchemyError as e:
        print(f"❌ Database connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_migration():
    """Verify that the migration was successful"""
    
    db_url = get_database_url()
    if not db_url:
        return False
    
    try:
        engine = create_engine(db_url)
        
        with engine.connect() as connection:
            # Check table structure
            result = connection.execute(text("DESCRIBE atividades"))
            columns = result.fetchall()
            
            print("\n📊 Current table structure:")
            for column in columns:
                print(f"   {column[0]} | {column[1]} | {'NULL' if column[2] == 'YES' else 'NOT NULL'}")
            
            # Check if we have local and setor columns
            column_names = [col[0] for col in columns]
            
            if 'local' in column_names and 'setor' in column_names:
                if 'localizacao' not in column_names:
                    print("✅ Migration verification successful!")
                    return True
                else:
                    print("⚠️  Warning: Old 'localizacao' column still exists")
                    return False
            else:
                print("❌ Migration verification failed - missing required columns")
                return False
                
    except Exception as e:
        print(f"❌ Error verifying migration: {e}")
        return False

def main():
    """Main migration function"""
    print("🗃️  Database Field Migration Tool")
    print("=" * 50)
    
    # Perform migration
    if migrate_database():
        # Verify migration
        if verify_migration():
            print("\n🎉 Migration completed successfully!")
            print("\n📋 Next steps:")
            print("   1. Test your application: python app.py")
            print("   2. Create a new task to test the new fields")
            print("   3. Verify existing tasks display correctly")
        else:
            print("\n⚠️  Migration completed but verification failed")
    else:
        print("\n❌ Migration failed")
        print("\n🔧 Troubleshooting:")
        print("   1. Check your .env file has SQLALCHEMY_DATABASE_URI")
        print("   2. Ensure your database is running")
        print("   3. Verify database credentials are correct")

if __name__ == "__main__":
    main()