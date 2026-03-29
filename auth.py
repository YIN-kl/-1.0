import json
import os
from typing import List


class RBAC:
    """基于角色的访问控制模型。"""

    def __init__(self, data_file: str = "./auth_data.json"):
        self.data_file = data_file
        self.load_data()

    def load_data(self):
        """从文件加载用户、角色和权限数据。"""
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as file:
                data = json.load(file)
            self.users = data.get("users", {})
            self.roles = data.get("roles", {})
            self.permissions = data.get("permissions", {})
            self.role_permissions = data.get("role_permissions", {})
            self.user_roles = data.get("user_roles", {})
            return

        self.users = {
            "admin": {"password": "admin123", "name": "管理员"},
            "hr": {"password": "hr123", "name": "人力资源"},
            "employee": {"password": "employee123", "name": "普通员工"},
        }
        self.roles = {
            "admin": "管理员",
            "hr": "人力资源",
            "employee": "普通员工",
        }
        self.permissions = {
            "read_all": "查看所有文档",
            "read_employee": "查看员工相关文档",
            "read_hr": "查看人力资源相关文档",
            "write_logs": "查看和写入审计日志",
        }
        self.role_permissions = {
            "admin": ["read_all", "write_logs"],
            "hr": ["read_all", "write_logs"],
            "employee": ["read_employee"],
        }
        self.user_roles = {
            "admin": ["admin"],
            "hr": ["hr"],
            "employee": ["employee"],
        }
        self.save_data()

    def save_data(self):
        """保存权限模型数据到文件。"""
        data = {
            "users": self.users,
            "roles": self.roles,
            "permissions": self.permissions,
            "role_permissions": self.role_permissions,
            "user_roles": self.user_roles,
        }
        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def authenticate(self, username: str, password: str) -> bool:
        """校验用户名和密码。"""
        return username in self.users and self.users[username]["password"] == password

    def get_user_roles(self, username: str) -> List[str]:
        """获取用户角色列表。"""
        return self.user_roles.get(username, [])

    def get_role_permissions(self, role: str) -> List[str]:
        """获取角色拥有的权限。"""
        return self.role_permissions.get(role, [])

    def get_user_permissions(self, username: str) -> List[str]:
        """汇总用户拥有的所有权限。"""
        permissions: List[str] = []
        for role in self.get_user_roles(username):
            permissions.extend(self.get_role_permissions(role))
        return list(set(permissions))

    def has_permission(self, username: str, permission: str) -> bool:
        """判断用户是否具备指定权限。"""
        return permission in self.get_user_permissions(username)

    def add_user(self, username: str, password: str, name: str):
        """新增用户，默认角色为普通员工。"""
        self.users[username] = {"password": password, "name": name}
        self.user_roles[username] = ["employee"]
        self.save_data()

    def add_role(self, role: str, description: str):
        """新增角色。"""
        self.roles[role] = description
        self.role_permissions[role] = []
        self.save_data()

    def add_permission(self, permission: str, description: str):
        """新增权限。"""
        self.permissions[permission] = description
        self.save_data()

    def assign_role(self, username: str, role: str):
        """给用户分配角色。"""
        if username not in self.user_roles:
            self.user_roles[username] = []
        if role not in self.user_roles[username]:
            self.user_roles[username].append(role)
        self.save_data()

    def assign_permission(self, role: str, permission: str):
        """给角色分配权限。"""
        if role not in self.role_permissions:
            self.role_permissions[role] = []
        if permission not in self.role_permissions[role]:
            self.role_permissions[role].append(permission)
        self.save_data()


rbac = RBAC()
