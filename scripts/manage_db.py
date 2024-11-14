# scripts/manage_db.py
import sys
import click
from pathlib import Path
from alembic import command
from alembic.config import Config

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.initial_data import init_db, init_permissions, init_roles, init_departments, init_default_users
from sqlalchemy import text

def run_migrations():
    """Run database migrations"""
    try:
        # Create Alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        # Run the migrations
        command.upgrade(alembic_cfg, "head")
        return True
    except Exception as e:
        click.echo(f"Error running migrations: {e}", err=True)
        return False

@click.group()
def cli():
    """Database management commands for ADEO application"""
    pass

@cli.command()
@click.option('--force', is_flag=True, help='Force initialization even if data exists')
def init(force):
    """Initialize database with default data"""
    db = SessionLocal()
    try:
        # First, run migrations to create tables
        click.echo("Running database migrations...")
        if not run_migrations():
            click.echo("Failed to run migrations. Aborting initialization.")
            return
        
        if force:
            # Clean existing data
            click.echo("Forcing reinitialization... Cleaning existing data...")
            try:
                db.execute(text("""
                    TRUNCATE TABLE users, roles, permissions, departments, 
                    user_roles, role_permissions RESTART IDENTITY CASCADE;
                """))
                db.commit()
            except Exception as e:
                click.echo(f"Error cleaning data (this is normal for first run): {e}")
                db.rollback()
        
        click.echo("Initializing database...")
        init_db(db)
        click.echo("Database initialization completed successfully!")
        
    except Exception as e:
        click.echo(f"Error initializing database: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()

@cli.command()
def verify():
    """Verify database initialization status"""
    db = SessionLocal()
    try:
        # Check each table
        tables = ['users', 'roles', 'permissions', 'departments']
        status = {}
        
        for table in tables:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            status[table] = result
        
        click.echo("\nDatabase Status:")
        click.echo("================")
        for table, count in status.items():
            click.echo(f"{table.capitalize()}: {count} records")
            
        # Check specific entities
        click.echo("\nKey Entities Check:")
        click.echo("==================")
        
        # Check Super Admin
        super_admin = db.execute(text("SELECT COUNT(*) FROM users WHERE is_superuser = true")).scalar()
        click.echo(f"Super Admin users: {super_admin}")
        
        # Check departments
        dept_list = db.execute(text("SELECT code, name FROM departments")).fetchall()
        click.echo("\nDepartments:")
        for dept in dept_list:
            click.echo(f"- {dept.code}: {dept.name}")
        
        # Check roles
        role_list = db.execute(text("SELECT name FROM roles")).fetchall()
        click.echo("\nRoles:")
        for role in role_list:
            click.echo(f"- {role.name}")
            
    except Exception as e:
        click.echo(f"Error verifying database: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()

@cli.command()
@click.option('--type', 'entity_type', type=click.Choice(['users', 'roles', 'departments', 'permissions']), 
              help='Type of entity to list')
def list(entity_type):
    """List entities in the database"""
    db = SessionLocal()
    try:
        if entity_type == 'users':
            result = db.execute(text("""
                SELECT u.username, u.email, d.code as department, r.name as role, u.is_superuser
                FROM users u
                LEFT JOIN departments d ON u.department_id = d.id
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                ORDER BY u.username
            """)).fetchall()
            
            click.echo("\nUsers:")
            click.echo("=======")
            for user in result:
                click.echo(f"Username: {user.username}")
                click.echo(f"Email: {user.email}")
                click.echo(f"Department: {user.department}")
                click.echo(f"Role: {user.role}")
                click.echo(f"Is Superuser: {user.is_superuser}")
                click.echo("---")
                
        elif entity_type == 'roles':
            result = db.execute(text("""
                SELECT r.name, r.description, 
                       STRING_AGG(p.name, ', ') as permissions
                FROM roles r
                LEFT JOIN role_permissions rp ON r.id = rp.role_id
                LEFT JOIN permissions p ON rp.permission_id = p.id
                GROUP BY r.id, r.name, r.description
                ORDER BY r.name
            """)).fetchall()
            
            click.echo("\nRoles:")
            click.echo("=======")
            for role in result:
                click.echo(f"Name: {role.name}")
                click.echo(f"Description: {role.description}")
                click.echo(f"Permissions: {role.permissions}")
                click.echo("---")
                
        elif entity_type == 'departments':
            result = db.execute(text("""
                SELECT d.code, d.name, d.description,
                       COUNT(u.id) as user_count
                FROM departments d
                LEFT JOIN users u ON d.id = u.department_id
                GROUP BY d.id, d.code, d.name, d.description
                ORDER BY d.code
            """)).fetchall()
            
            click.echo("\nDepartments:")
            click.echo("============")
            for dept in result:
                click.echo(f"Code: {dept.code}")
                click.echo(f"Name: {dept.name}")
                click.echo(f"Description: {dept.description}")
                click.echo(f"Users: {dept.user_count}")
                click.echo("---")
                
        elif entity_type == 'permissions':
            result = db.execute(text("""
                SELECT p.name, p.description,
                       COUNT(DISTINCT r.id) as role_count
                FROM permissions p
                LEFT JOIN role_permissions rp ON p.id = rp.permission_id
                LEFT JOIN roles r ON rp.role_id = r.id
                GROUP BY p.id, p.name, p.description
                ORDER BY p.name
            """)).fetchall()
            
            click.echo("\nPermissions:")
            click.echo("============")
            for perm in result:
                click.echo(f"Name: {perm.name}")
                click.echo(f"Description: {perm.description}")
                click.echo(f"Used in roles: {perm.role_count}")
                click.echo("---")
    
    except Exception as e:
        click.echo(f"Error listing entities: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    cli()