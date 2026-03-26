from enum import Enum

class StaffRole(str, Enum):
    ADMIN = 'admin'
    MANAGER = 'manager'

class UsersRole(str, Enum):
    USER = 'user'
    STAFF = 'staff'
