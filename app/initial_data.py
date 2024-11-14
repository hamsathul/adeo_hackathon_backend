# app/initial_data.py
from sqlalchemy.orm import Session
from app.models.auth import User, Role, Permission
from app.models.department import Department
from app.core.security import get_password_hash

def init_permissions(db: Session) -> dict:
    """Initialize default permissions"""
    permissions = {
        # Opinion Request Management
        "create_opinion_request": "Can create opinion requests",
        "view_opinion_requests": "Can view opinion requests",
        "review_opinion_requests": "Can review and provide opinions",
        "manage_opinion_requests": "Can manage all opinion requests",
        "approve_opinion_requests": "Can approve opinion requests",
        "reject_opinion_requests": "Can reject opinion requests",
        
        # User Management
        "manage_users": "Can manage all user operations",
        "view_users": "Can view user details",
        
        # Department Management
        "manage_departments": "Can manage department operations",
        "view_departments": "Can view department details",
        
        # Expert Management
        "assign_experts": "Can assign experts to requests",
        "manage_experts": "Can manage expert assignments",
        
        # System Management
        "system_admin": "Full system administration access",
        "view_analytics": "Can view analytics and reports",
        
        # Document Management
        "upload_documents": "Can upload documents",
        "view_documents": "Can view documents",
        "manage_documents": "Can manage all documents",
        
        # Comment Management
        "add_comments": "Can add comments to requests",
        "view_comments": "Can view comments",
        "manage_comments": "Can manage all comments"
    }
    
    permission_objects = {}
    for name, description in permissions.items():
        db_permission = db.query(Permission).filter(Permission.name == name).first()
        if not db_permission:
            db_permission = Permission(name=name, description=description)
            db.add(db_permission)
        permission_objects[name] = db_permission
    
    db.commit()
    return permission_objects

def init_roles(db: Session, permissions: dict) -> dict:
    """Initialize expanded roles for ADEO"""
    roles = {
        "Super Admin": {
            "description": "Has full system access",
            "permissions": list(permissions.values())
        },
        "System Admin": {
            "description": "System administrator with limited access",
            "permissions": [
                permissions["manage_users"],
                permissions["manage_departments"],
                permissions["view_analytics"],
                permissions["system_admin"],
                permissions["manage_documents"]
            ]
        },
        "Department Head": {
            "description": "Head of department with approval authority",
            "permissions": [
                permissions["view_users"],
                permissions["manage_opinion_requests"],
                permissions["review_opinion_requests"],
                permissions["approve_opinion_requests"],
                permissions["reject_opinion_requests"],
                permissions["view_analytics"],
                permissions["assign_experts"],
                permissions["manage_documents"],
                permissions["manage_comments"]
            ]
        },
        "Senior Expert": {
            "description": "Senior department expert with additional privileges",
            "permissions": [
                permissions["view_users"],
                permissions["review_opinion_requests"],
                permissions["approve_opinion_requests"],
                permissions["view_opinion_requests"],
                permissions["manage_documents"],
                permissions["add_comments"],
                permissions["view_comments"]
            ]
        },
        "Expert": {
            "description": "Department expert who reviews requests",
            "permissions": [
                permissions["view_users"],
                permissions["review_opinion_requests"],
                permissions["view_opinion_requests"],
                permissions["upload_documents"],
                permissions["view_documents"],
                permissions["add_comments"],
                permissions["view_comments"]
            ]
        },
        "Regular User": {
            "description": "Regular department user",
            "permissions": [
                permissions["create_opinion_request"],
                permissions["view_opinion_requests"],
                permissions["view_documents"],
                permissions["upload_documents"],
                permissions["add_comments"],
                permissions["view_comments"]
            ]
        },
        "Viewer": {
            "description": "Can only view requests and comments",
            "permissions": [
                permissions["view_opinion_requests"],
                permissions["view_documents"],
                permissions["view_comments"]
            ]
        }
    }
    
    role_objects = {}
    for name, data in roles.items():
        db_role = db.query(Role).filter(Role.name == name).first()
        if not db_role:
            db_role = Role(
                name=name,
                description=data["description"]
            )
            db_role.permissions = data["permissions"]
            db.add(db_role)
        role_objects[name] = db_role
    
    db.commit()
    return role_objects

def init_departments(db: Session) -> dict:
    """Initialize expanded ADEO departments"""
    departments = {
        # Executive & Administration
        "EXE": {
            "name": "Executive Office",
            "code": "EXE",
            "description": "Executive oversight and decision making"
        },
        "ADM": {
            "name": "Administration Department",
            "code": "ADM",
            "description": "Administrative affairs and support"
        },
        
        # Core Business Departments
        "PLD": {
            "name": "Policy & Legislation Department",
            "code": "PLD",
            "description": "Policy development and legislative affairs"
        },
        "GSD": {
            "name": "Government Services Department",
            "code": "GSD",
            "description": "Government service delivery and improvement"
        },
        "DID": {
            "name": "Digital Innovation Department",
            "code": "DID",
            "description": "Digital transformation and innovation"
        },
        "STD": {
            "name": "Strategy & Planning Department",
            "code": "STD",
            "description": "Strategic planning and development"
        },
        
        # Support Departments
        "LEG": {
            "name": "Legal Affairs Department",
            "code": "LEG",
            "description": "Legal consultation and compliance"
        },
        "FIN": {
            "name": "Finance Department",
            "code": "FIN",
            "description": "Financial planning and management"
        },
        "HRD": {
            "name": "Human Resources Department",
            "code": "HRD",
            "description": "HR management and development"
        },
        "ITD": {
            "name": "Information Technology Department",
            "code": "ITD",
            "description": "IT infrastructure and support"
        },
        
        # Specialized Departments
        "PMO": {
            "name": "Project Management Office",
            "code": "PMO",
            "description": "Project management and coordination"
        },
        "QCD": {
            "name": "Quality Control Department",
            "code": "QCD",
            "description": "Quality assurance and control"
        },
        "CCD": {
            "name": "Corporate Communications Department",
            "code": "CCD",
            "description": "Communications and media relations"
        },
        "IRD": {
            "name": "International Relations Department",
            "code": "IRD",
            "description": "International cooperation and relations"
        }
    }
    
    department_objects = {}
    for code, data in departments.items():
        db_dept = db.query(Department).filter(Department.code == code).first()
        if not db_dept:
            db_dept = Department(**data)
            db.add(db_dept)
        department_objects[code] = db_dept
    
    db.commit()
    return department_objects

def init_default_users(db: Session, roles: dict, departments: dict):
    """Initialize expanded set of default users"""
    users = [
        # Executive Management
        {
            "email": "superadmin@adeo.gov.ae",
            "username": "superadmin",
            "password": "superadmin123",
            "is_superuser": True,
            "role": roles["Super Admin"],
            "department": departments["EXE"]
        },
        {
            "email": "sysadmin@adeo.gov.ae",
            "username": "sysadmin",
            "password": "sysadmin123",
            "is_superuser": False,
            "role": roles["System Admin"],
            "department": departments["ITD"]
        },
        
        # Department Heads
        {
            "email": "pld.head@adeo.gov.ae",
            "username": "pldhead",
            "password": "pldhead123",
            "role": roles["Department Head"],
            "department": departments["PLD"]
        },
        {
            "email": "gsd.head@adeo.gov.ae",
            "username": "gsdhead",
            "password": "gsdhead123",
            "role": roles["Department Head"],
            "department": departments["GSD"]
        },
        {
            "email": "legal.head@adeo.gov.ae",
            "username": "legalhead",
            "password": "legalhead123",
            "role": roles["Department Head"],
            "department": departments["LEG"]
        },
        
        # Senior Experts
        {
            "email": "legal.senior@adeo.gov.ae",
            "username": "legalsenior",
            "password": "legal123",
            "role": roles["Senior Expert"],
            "department": departments["LEG"]
        },
        {
            "email": "policy.senior@adeo.gov.ae",
            "username": "policysenior",
            "password": "policy123",
            "role": roles["Senior Expert"],
            "department": departments["PLD"]
        },
        
        # Experts by Department
        {
            "email": "legal.expert@adeo.gov.ae",
            "username": "legalexpert",
            "password": "legal123",
            "role": roles["Expert"],
            "department": departments["LEG"]
        },
        {
            "email": "policy.expert@adeo.gov.ae",
            "username": "policyexpert",
            "password": "policy123",
            "role": roles["Expert"],
            "department": departments["PLD"]
        },
        {
            "email": "digital.expert@adeo.gov.ae",
            "username": "digitalexpert",
            "password": "digital123",
            "role": roles["Expert"],
            "department": departments["DID"]
        },
        
        # Regular Users
        {
            "email": "pld.user@adeo.gov.ae",
            "username": "plduser",
            "password": "plduser123",
            "role": roles["Regular User"],
            "department": departments["PLD"]
        },
        {
            "email": "gsd.user@adeo.gov.ae",
            "username": "gsduser",
            "password": "gsduser123",
            "role": roles["Regular User"],
            "department": departments["GSD"]
        },
        {
            "email": "legal.user@adeo.gov.ae",
            "username": "legaluser",
            "password": "legaluser123",
            "role": roles["Regular User"],
            "department": departments["LEG"]
        },
        
        # Viewers
        {
            "email": "exe.viewer@adeo.gov.ae",
            "username": "exeviewer",
            "password": "viewer123",
            "role": roles["Viewer"],
            "department": departments["EXE"]
        }
    ]
    
    for user_data in users:
        db_user = db.query(User).filter(User.email == user_data["email"]).first()
        if not db_user:
            is_superuser = user_data.get("is_superuser", False)
            db_user = User(
                email=user_data["email"],
                username=user_data["username"],
                hashed_password=get_password_hash(user_data["password"]),
                is_superuser=is_superuser,
                department_id=user_data["department"].id
            )
            db_user.roles = [user_data["role"]]
            db.add(db_user)
    
    db.commit()
    
def init_db(db: Session) -> None:
    """Initialize database with default data"""
    try:
        # Check if database is already initialized
        existing_users = db.query(User).first()
        if existing_users:
            print("Database already contains data. Skipping initialization.")
            return

        print("Starting database initialization...")
        
        # Initialize in correct order to maintain relationships
        print("Initializing permissions...")
        permissions = init_permissions(db)
        
        print("Initializing roles...")
        roles = init_roles(db, permissions)
        
        print("Initializing departments...")
        departments = init_departments(db)
        
        print("Initializing default users...")
        init_default_users(db, roles, departments)
        
        print("Database initialization completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error during database initialization: {e}")
        raise
    finally:
        db.close()

# Optional: Add a function to check initialization status
def check_init_status(db: Session) -> dict:
    """Check the initialization status of the database"""
    try:
        status = {
            "permissions": db.query(Permission).count(),
            "roles": db.query(Role).count(),
            "departments": db.query(Department).count(),
            "users": db.query(User).count(),
            "superusers": db.query(User).filter(User.is_superuser == True).count()
        }
        return status
    except Exception as e:
        print(f"Error checking initialization status: {e}")
        raise