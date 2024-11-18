# app/initial_data.py
from sqlalchemy.orm import Session
from app.models.auth import User, Role, Permission
from app.models.department import Department
from app.core.security import get_password_hash
from app.models.opinion import (
    WorkflowStatus, 
    CommunicationType,
    Category,
    SubCategory
)

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
    

def init_workflow_statuses(db: Session) -> dict:
    """Initialize default workflow statuses"""
    statuses = {
        "unassigned": "New request pending assignment",
        "assigned_to_department": "Assigned to department",
        "assigned_to_expert": "Assigned to expert",
        "in_review": "Under review",
        "additional_info_requested": "Additional information requested",
        "pending_other_department": "Waiting for other department input",
        "expert_opinion_submitted": "Expert has submitted opinion",
        "head_review_pending": "Pending department head review",
        "head_approved": "Approved by department head",
        "completed": "Request completed",
        "rejected": "Request rejected"
    }
    
    status_objects = {}
    for name, description in statuses.items():
        db_status = db.query(WorkflowStatus).filter(
            WorkflowStatus.name == name
        ).first()
        if not db_status:
            db_status = WorkflowStatus(
                name=name,
                description=description
            )
            db.add(db_status)
        status_objects[name] = db_status
    
    db.commit()
    return status_objects

def init_communication_types(db: Session) -> dict:
    """Initialize default communication types"""
    types = {
        "opinion_request": {
            "name": "Opinion Request",
            "description": "Request for department opinion",
            "requires_response": True,
            "default_deadline_hours": 72
        },
        "information_request": {
            "name": "Information Request",
            "description": "Request for additional information",
            "requires_response": True,
            "default_deadline_hours": 48
        },
        "notification": {
            "name": "Notification",
            "description": "General notification",
            "requires_response": False,
            "default_deadline_hours": None
        },
        "escalation": {
            "name": "Escalation",
            "description": "Escalation of request",
            "requires_response": True,
            "default_deadline_hours": 24
        },
        "interdepartmental_consult": {
            "name": "Interdepartmental Consultation",
            "description": "Consultation between departments",
            "requires_response": True,
            "default_deadline_hours": 96
        },
        "status_update": {
            "name": "Status Update",
            "description": "Update on request status",
            "requires_response": False,
            "default_deadline_hours": None
        }
    }
    
    type_objects = {}
    for code, data in types.items():
        db_type = db.query(CommunicationType).filter(
            CommunicationType.name == data["name"]
        ).first()
        if not db_type:
            db_type = CommunicationType(**data)
            db.add(db_type)
        type_objects[code] = db_type
    
    db.commit()
    return type_objects

# Add new permissions for opinion system
def add_opinion_permissions(db: Session, permissions: dict):
    """Add opinion system specific permissions"""
    opinion_permissions = {
        # Workflow Management
        "manage_workflow": "Can manage workflow statuses and transitions",
        "view_workflow_history": "Can view workflow history",
        
        # Opinion Specific
        "submit_opinion": "Can submit opinions",
        "review_opinions": "Can review submitted opinions",
        "approve_opinions": "Can approve opinions",
        
        # Communication
        "send_communications": "Can send interdepartmental communications",
        "respond_communications": "Can respond to communications",
        "escalate_requests": "Can escalate requests",
        
        # Statistics and Reports
        "view_opinion_statistics": "Can view opinion statistics",
        "export_opinion_reports": "Can export opinion reports"
    }
    
    for name, description in opinion_permissions.items():
        if name not in permissions:
            db_permission = Permission(name=name, description=description)
            db.add(db_permission)
            permissions[name] = db_permission
    
    db.commit()
    return permissions
def init_categories_and_subcategories(db: Session) -> dict:
    """Initialize categories and subcategories"""
    categories_data = {
        "Projects and Initiatives": [
            "Project or Initiative",
            "Hosting/Holding an Event",
            "Cancelling a Project"
        ],
        "Policies and Strategies": [
            "General Policy",
            "Strategy/Executive Plan for an Entity",
            "Change in the Approved Executive Plan",
            "Strategy for a Pillar/Sector"
        ],
        "Governance and Legislation": [
            "Local Legislation",
            "Federal Legislation",
            "Governance Mechanisms",
            "Committees/Councils and Powers",
            "Complex/Responsive Memoranda",
            "Legislative Permission",
            "Agreements",
            "Memoranda of Understanding"
        ],
        "Infrastructure, Land and Assets": [
            "Leasing a Headquarter",
            "Land and Assets"
        ],
        "Human Capital": [
            "Organizational Structures",
            "Talent Management and Manpower for the Administration",
            "Manpower Exceptions"
        ],
        "Financial Requests": [
            "Contracts",
            "Purchases",
            "Fees, Tariffs and Taxes",
            "Financial Transfers",
            "Additional Budget for Projects",
            "Additional Budget Or financial transfer on the first door",
            "Additional budget (jobs, employment contracts)",
            "Acceptance of a sponsorship request"
        ],
        "Reports and Studies": []
    }
    
    category_objects = {}
    
    for category_name, subcategories in categories_data.items():
        # Create or get category
        db_category = db.query(Category).filter(
            Category.name == category_name
        ).first()
        
        if not db_category:
            db_category = Category(name=category_name)
            db.add(db_category)
            db.flush()  # Get ID for subcategories
            
        category_objects[category_name] = {
            "category": db_category,
            "subcategories": []
        }
        
        # Create subcategories
        for subcategory_name in subcategories:
            db_subcategory = db.query(SubCategory).filter(
                SubCategory.category_id == db_category.id,
                SubCategory.name == subcategory_name
            ).first()
            
            if not db_subcategory:
                db_subcategory = SubCategory(
                    category_id=db_category.id,
                    name=subcategory_name
                )
                db.add(db_subcategory)
            
            category_objects[category_name]["subcategories"].append(db_subcategory)
    
    db.commit()
    return category_objects

# Update init_db function to include categories and subcategories
def init_db(db: Session) -> None:
    """Initialize database with default data"""
    try:
        # Check if database is already initialized
        existing_users = db.query(User).first()
        if existing_users:
            print("Database already contains data. Skipping initialization.")
            return

        print("Starting database initialization...")
        
        print("Initializing permissions...")
        permissions = init_permissions(db)
        
        print("Adding opinion system permissions...")
        permissions = add_opinion_permissions(db, permissions)
        
        print("Initializing roles...")
        roles = init_roles(db, permissions)
        
        print("Initializing departments...")
        departments = init_departments(db)
        
        print("Initializing categories and subcategories...")  # Add this line
        categories = init_categories_and_subcategories(db)     # Add this line
        
        print("Initializing workflow statuses...")
        workflow_statuses = init_workflow_statuses(db)
        
        print("Initializing communication types...")
        communication_types = init_communication_types(db)
        
        print("Initializing default users...")
        init_default_users(db, roles, departments)
        
        print("Database initialization completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error during database initialization: {e}")
        raise
    finally:
        db.close()

# Update check_init_status function to include categories
def check_init_status(db: Session) -> dict:
    """Check the initialization status of the database"""
    try:
        status = {
            "permissions": db.query(Permission).count(),
            "roles": db.query(Role).count(),
            "departments": db.query(Department).count(),
            "users": db.query(User).count(),
            "superusers": db.query(User).filter(User.is_superuser == True).count(),
            "workflow_statuses": db.query(WorkflowStatus).count(),
            "communication_types": db.query(CommunicationType).count(),
            "categories": db.query(Category).count(),           # Add this line
            "subcategories": db.query(SubCategory).count()     # Add this line
        }
        return status
    except Exception as e:
        print(f"Error checking initialization status: {e}")
        raise