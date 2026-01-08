from django.urls import include, path

from . import views
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet

router=DefaultRouter()
router.register(r'project',ProjectViewSet)

app_name = "tasks"


urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("signUp",views.signUp,name="signUp"),
    path("admin/manage_project", views.manage_project, name="manage_project"),
    path("admin/manage_user", views.manage_user, name="manage_user"),
    path("admin/add_user", views.add_user, name="add_user"),
    path("admin/add_project", views.add_project, name="add_project"),
    path('admin/api/',include(router.urls)),
    path("admin", views.admin_dashboard, name="admin"),
    path("user",views.user_dashboard,name="user"),
    path("register_user",views.register_user),
    path("admin/manage_role",views.manage_role,name="manage_role"),
    path("admin/role",views.role,name="role"),
    path("admin/edit_role",views.edit_role,name="edit_role"),
    path("admin/delete_role",views.delete_role,name="delete_role"),
    path("api/check-username/", views.check_username, name="check_username"),
    path("api/check-email/", views.check_email, name="check_email"),
    path("admin/assign_users", views.assign_users, name="assign_users"),
    path("api/project/<int:project_id>/users/",views.get_project_users),
    path("api/project/assign-user/",views.assign_user_to_project,name="assign_user_to_project"),
    path("api/project/unassign-user/",views.unassign_user_from_project,name="unassign_user_from_project"),
    path("user/project_details",views.project_details,name="project_details"),
    path("user/api/task/create/",views.create_task,name="create_task"),
    path("admin/manage_task",views.manage_task,name="manage_task"),
    path("admin/project/api/get_projects/",views.get_project_id_name,name="get_projects"),
    path("admin/project/api/get_project_detail/<int:project_id>/",views.get_project_detail,name="get_project_detail"),
    path("admin/project/api/get_project_userdetails/<int:project_id>/",views.get_project_users,name="get_project_users"),
    path("admin/task/api/create/",views.admin_save_task,name="admin_save_task"),
]