from django.utils import timezone
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from tasks.models import Project_User, Task
from tasks.models.Project import Project
from tasks.models.Role import Role
from tasks.models.Users import Users
from tasks.serailizers import ProjectSerializer
from django.core import serializers

class ProjectViewSet(viewsets.ModelViewSet):
    queryset=Project.objects.all()
    serializer_class=ProjectSerializer


def index(request):
    # return HttpResponse("Hello, world. You're at the polls index.")
    res=check_session(request)
    if res is not None:
        return res
    return render(request,"tasks/index.html")



def check_session(request):
    if request.session.session_key:
        #print(f"Session key: {request.session.session_key}")
        if request.session.get("role")=="admin":
            return redirect("tasks:admin")
        else:
            return redirect("tasks:user")
    

@csrf_exempt
def login(request):
    res=check_session(request)
    if res is not None:
        return res
    error=None
    if request.method=="POST":
        form=request.POST
        username=form.get("username")
        password=form.get("password")
        try:
            user=Users.objects.get(
                username=username,
                password=password
            )
            request.session["user_id"]=user.id
            request.session["username"]=user.username
            request.session["role"]=user.role.name
            request.session["email"]=user.email
            if user.role.name == "admin":
                response = redirect("tasks:admin")
                response.set_cookie(
                    key="user_id",
                    value=user.id
                )
                return response
            else:
                return redirect("tasks:user")
        except Users.DoesNotExist:
            error="username or password is incorrect"
        except Exception as err:
            error=err
    return render(request,"tasks/index.html",{"error":error})

def logout(request):
    request.session.flush()
    return render(request,"tasks/index.html")

def manage_project(request):
    return render(request,"tasks/admin/manage_project.html")

def add_project(request):
    if request.method=="GET":
        return render(request,"tasks/admin/add_project.html")
    return render(request,"tasks/admin/manage_project.html")

def admin_dashboard(request):
    if request.session.get("role") == "admin":
        return render(request,"tasks/admin/dashboard.html")
    return render(request,"tasks/index.html")

def signUp(request):
    return render(request,"tasks/signUp.html")

def register_user(request):
    msg=None
    username=None
    password=None
    if request.method=="POST":
        form=request.POST
        username=form.get("username")
        password=form.get("password")
        email=form.get("email")
        fullname=form.get("fullname")
        if Users.objects.filter(username=username).exists():
            return render(request,"tasks/signUp.html", {"msg":"username already exist"})
        try:
            role=Role.objects.get(name="user")
            user=Users(
                username=username,
                email=email,
                password=password,
                full_name=fullname,
                role=role
            )
            user.save()
            user.set_creator_and_note(user)
            user.save()
            msg="user registered successfully"
        except Exception as err:
            print(err)
            return render(request,"tasks/signUp.html",{ "msg":str(err)})
    return render(request,"tasks/index.html",{"msg":msg,"username":username,"password":password})

def user_dashboard(request):
    if request.session.get("role") == "user":
        user_id=request.session.get("user_id")
        project=Project.objects.filter(project_user__user_id=user_id).distinct()
        return render(request,"tasks/user/dashboard.html",{"projects":project})
    return render(request,"tasks/index.html")

def manage_user(request):
    users = Users.objects.all()
    return render(request,"tasks/admin/manage_user.html",{"users":users})

def add_user(request):
    if request.method=="GET":
        return render(request,"tasks/admin/add_user.html")
    elif request.method=="POST":
        msg=None
        username=None
        password=None
        if request.session.get("role")=="admin":
            form=request.POST
            username=form.get("username")
            password=form.get("password")
            email=form.get("email")
            note=form.get("note")
            fullname=form.get("fullname")
            if Users.objects.filter(username=username).exists():
                return render(request,"tasks/admin/add_user.html", {"msg":"username already exist"})
            try:
                admin=Users.objects.get(username=request.session.get("username"))
                role=Role.objects.get(name="user")
                user=Users(
                    username=username,
                    email=email,
                    password=password,
                    full_name=fullname,
                    role=role,
                    created_by=admin,
                    note=note or "by admin"
                )
                user.save()
                msg="user registered successfully"
            except Exception as err:
                print(err)
                return render(request,"tasks/admin/add_user.html",{ "msg":str(err)})
    return redirect("tasks:manage_user")

def manage_role(request):
    roles=Role.objects.all()
    return render(request,"tasks/admin/manage_role.html",{"roles":roles})

def role(request):
    if request.method=="POST":
        form=request.POST
        role_name=form.get("role_name")
        role=Role(name=role_name)
        role.save()
        return redirect("tasks:manage_role")
    else:
        return redirect("tasks:admin")

def edit_role(request):
    if request.method=="POST":
        form=request.POST
        role_id=form.get("role_id")
        role_name=form.get("role_name")
        try:
            role=Role.objects.get(id=role_id)
            role.name=role_name
            role.save()
        except Exception as err:
            print(err)
    return redirect("tasks:manage_role")

def delete_role(request):
    if request.method=="POST":
        form=request.POST
        role_id=form.get("role_id")
        try:
            role=Role.objects.get(id=role_id)
            role.delete()
        except Exception as err:
            print(err)
    return redirect("tasks:manage_role")

def check_username(request):
    username = request.GET.get("username", "").strip()

    if not username:
        return JsonResponse({"exists": False})

    exists = Users.objects.filter(username=username).exists()
    return JsonResponse({"exists": exists})

def check_email(request):
    email = request.GET.get("email", "").strip()

    if not email:
        return JsonResponse({"exists": False})

    exists = Users.objects.filter(email=email).exists()
    return JsonResponse({"exists": exists})

def assign_users_to_project(request):
    if request.method=="POST":
        try:
            project_id = request.POST.get("project_id")
            user_ids = request.POST.getlist("user_ids[]")

            admin_id = request.POST.get("admin_id")
            admin = Users.objects.get(id=admin_id)

            if admin.role.name != "admin":
                return JsonResponse({"error": "Only admin can assign users"}, status=403)

            project = Project.objects.get(id=project_id)
            
            existing_user_ids = set(
            Project_User.objects.filter(project=project)
            .values_list("user_id", flat=True)
            )
            
            assignments = []
            for uid in user_ids:
                if int(uid) not in existing_user_ids:
                    assignments.append(
                        Project_User(
                            project=project,
                            user_id=uid,
                            assigned_by=admin
                        )
                    )


            if not assignments:
                return JsonResponse({"message": "All users already assigned"})

            Project_User.objects.bulk_create(assignments)

            return JsonResponse({
                "message": "Users assigned successfully",
                "assigned_count": len(assignments)
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"message": "call appropriate method"}, status=403)

def unassign_user_from_project(request):
    if request.method=="POST":
        project_id = request.POST.get("project_id")
        user_ids = request.POST.getlist("user_ids[]")

        admin = Users.objects.get(id=request.session.get("user_id"))

        if admin.role.name != "admin":
            return JsonResponse({"error": "Unauthorized"}, status=403)

        deleted, _ = Project_User.objects.filter(
            project_id=project_id,
            user_id__in=user_ids
        ).delete()

        return JsonResponse({
            "message": "Users unassigned successfully",
            "count": deleted
        })
    return JsonResponse({"message": "call appropriate method"}, status=403)

def get_project_users_admin(request, project_id):
    try:
        assigned_user_ids = Project_User.objects.filter(
            project_id=project_id
        ).values_list("user_id", flat=True)

        assigned_users = Users.objects.filter(
            id__in=assigned_user_ids
        ).values("id", "username", "email")

        unassigned_users = Users.objects.exclude(
            id__in=assigned_user_ids
        ).exclude(role__name="admin") \
         .values("id", "username", "email")

        return JsonResponse({
            "assigned_users": list(assigned_users),
            "unassigned_users": list(unassigned_users)
        })

    except Exception as e:
        print(e)
        return JsonResponse({"error": str(e)}, status=400)


def assign_users(request):
    project_id = request.GET.get("project_id")
    project=None
    try:
        project=Project.objects.get(id=project_id)
    except Exception as err:
        print(err)
    return render(request,"tasks/admin/assign_user_project.html",{"project":project})

def assign_user_to_project(request):
    print(request.method)
    admin_id = request.session.get("user_id")
    if not admin_id:
        return JsonResponse({"error": "Not logged in"}, status=401)

    admin = Users.objects.get(id=admin_id)
    if admin.role.name != "admin":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    project_id = request.POST.get("project_id")
    user_id = request.POST.get("user_id")

    project = get_object_or_404(Project, id=project_id)
    user = get_object_or_404(Users, id=user_id)

    Project_User.objects.get_or_create(
        project=project,
        user=user,
        defaults={"assigned_by": admin}
    )

    return JsonResponse({"message": "User assigned"})

def unassign_user_from_project(request):
    try:
        admin_id = request.session.get("user_id")
        if not admin_id:
            return JsonResponse({"error": "Not logged in"}, status=401)

        admin = Users.objects.get(id=admin_id)

        if admin.role.name != "admin":
            return JsonResponse({"error": "Only admin can unassign users"}, status=403)

        project_id = request.POST.get("project_id")
        user_id = request.POST.get("user_id")

        if not project_id or not user_id:
            return JsonResponse(
                {"error": "project_id and user_id are required"},
                status=400
            )

        deleted, _ = Project_User.objects.filter(
            project_id=project_id,
            user_id=user_id
        ).delete()

        if deleted == 0:
            return JsonResponse({"message": "User was not assigned"})

        return JsonResponse({"message": "User unassigned successfully"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    
def project_users(project):
    users = Users.objects.filter(
            project_user__project_id=project.id
        ).distinct()
    return users

def project_details(request):
    project_id=request.GET.get("project_id")
    try:
        project=Project.objects.get(id=project_id)
        users=project_users(project)
        tasks = Task.objects.filter(
            project_id=project
        ).select_related("assigned_to")
        return render(request,"tasks/user/project_details.html",{"project":project,"users":users,"tasks": tasks})
    except Exception as err:
        print(err)
    return redirect("tasks:user")

def create_task(request):
    try:
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Login required"}, status=401)

        session_user = Users.objects.get(id=user_id)

        title = request.POST.get("title")
        description = request.POST.get("description")
        priority = request.POST.get("priority")
        due_date = request.POST.get("due_date")
        assigned_to_id = request.POST.get("assigned_to")
        project_id = request.POST.get("project_id")

        if not all([title, description, priority, due_date, project_id]):
            return JsonResponse({"error": "All fields are required"}, status=400)

        assigned_to = None
        if assigned_to_id:
            assigned_to = get_object_or_404(Users, id=assigned_to_id)

        project = get_object_or_404(Project, id=project_id)

        task = Task.objects.create(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            status="Todo",              
            assigned_to=assigned_to,    
            created_by=session_user,    
            updated_by=session_user,    
            project_id=project          
        )

        return JsonResponse({
            "message": "Task created successfully",
            "task_id": task.task_id
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    
def update_task(request):
    try:
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Login required"}, status=401)

        session_user = Users.objects.get(id=user_id)
        data = json.loads(request.body)

        task_id = data.get("task_id")
        title = data.get("title")
        description = data.get("description")
        priority = data.get("priority")
        due_date = data.get("due_date")
        assigned_to_id = data.get("assigned_to")

        if not all([title, description, priority, due_date]):
            return JsonResponse({"error": "All fields are required"}, status=400)

        assigned_to = None
        if assigned_to_id:
            assigned_to = get_object_or_404(Users, id=assigned_to_id)
            
        task=Task.objects.get(task_id=task_id)
        task.title=title
        task.description=description
        task.priority=priority
        task.assigned_to=assigned_to
        task.updated_by=session_user
        task.updated_at=timezone.now()
        task.save()

        return JsonResponse({
            "message": "Task updated    successfully",
            "task_id": task.task_id
        })

    except Exception as e:
        print(e)
        return JsonResponse({"error": str(e)}, status=400)
    
def manage_task(request):
    return render(request,"tasks/admin/manage_task.html")

def get_project_id_name(request):
    admin_id = request.session.get("user_id")
    if not admin_id:
        return JsonResponse({"error": "Not logged in"}, status=401)

    admin = Users.objects.get(id=admin_id)
    if admin.role.name != "admin":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    project=Project.objects.only('id', 'title')

    res=serializers.serialize("json", project)
    return JsonResponse({"projects": res})


def get_project_detail(request, project_id):
    admin_id = request.session.get("user_id")

    if not admin_id:
        return JsonResponse({"error": "Not logged in"}, status=401)

    admin = Users.objects.get(id=admin_id)

    if admin.role.name != "admin":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        project = Project.objects.get(id=project_id)
        users=project_users(project)
        tasks = Task.objects.filter(project_id=project)

        return JsonResponse({
            "id": project.id,
            "title": project.title,
            "detail": project.detail,
            "created_by": project.created_by.username if project.created_by else None,
            "created_at": project.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "users": [
                {
                    "id": user.id,
                    "full_name": user.full_name
                }
                for user in users
            ],
            "tasks": [
                {
                    "id": t.task_id,
                    "title": t.title,
                    "priority": t.priority,
                    "status": t.status,
                    "assigned_to": t.assigned_to.full_name if t.assigned_to else None,
                    "due_date": t.due_date.strftime("%Y-%m-%d")
                }
                for t in tasks
            ]
        })

    except Project.DoesNotExist:
        return JsonResponse({"error": "Project not found"}, status=404)
    
def get_project_users(request,project_id):
    try:
        project = Project.objects.get(id=project_id)
        users=project_users(project)

        return JsonResponse({
            "users": [
                {
                    "id": user.id,
                    "full_name": user.full_name
                }
                for user in users
            ]
        })
    except Project.DoesNotExist:
        return JsonResponse({"error": "user not found"}, status=404)
    
def admin_save_task(request):
    if request.method=="POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            user_id = request.session.get("user_id")
            session_user = Users.objects.get(id=user_id)

            title = data.get("title")
            description = data.get("description")
            priority = data.get("priority")
            due_date = data.get("due_date")
            assigned_to_id = data.get("assigned_to")
            project_id = data.get("project_id")


            if not all([title, description, priority, due_date, project_id]):
                return JsonResponse({"error": "All fields are required"}, status=400)

            assigned_to = None
            if assigned_to_id:
                assigned_to = get_object_or_404(Users, id=assigned_to_id)

            project = get_object_or_404(Project, id=project_id)

            task = Task.objects.create(
                title=title,
                description=description,
                priority=priority,
                due_date=due_date,
                status="Todo",              
                assigned_to=assigned_to,    
                created_by=session_user,    
                updated_by=session_user,    
                project_id=project          
            )

            return JsonResponse({
                "message": "Task created successfully",
                "task_id": task.task_id
            })

        except Exception as err:
            print(err)
            return JsonResponse({"error": str(err)}, status=404)
    return JsonResponse({"error": "method not allowed"}, status=404)


def get_task_detail(request, task_id):
    try:
        task = Task.objects.get(task_id=task_id)

        return JsonResponse({
            "id": task.task_id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "status": task.status,
            "due_date": task.due_date.strftime("%Y-%m-%d"),
            "assigned_to": task.assigned_to.id if task.assigned_to else None,
            "assigned_to_name": task.assigned_to.full_name if task.assigned_to else None,
            "project_id": task.project_id.id if task.project_id else None
        }, status=200)

    except Task.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)

def task_next_state(request,task_id):
    try:
        status=('Todo','In Progress','Under Review','Done')
        task=Task.objects.get(task_id=task_id)
        current_task=task.status
        status_index=status.index(current_task)
        if status_index<len(status)-1:
            task.status=status[status_index+1]
            task.save()
            return JsonResponse({"msg": "Task status updated"}, status=200)
        return JsonResponse({"error": "Task cannot be updated"}, status=404)
    except Exception as e:
        print(e)
        return  JsonResponse({"msg": "Task not found"}, status=200)

def get_current_state(request,task_id):
    try:
        task=Task.objects.get(task_id=task_id)
        return JsonResponse({"task status": task.status}, status=200)
    except Task.DoesNotExist:
        return JsonResponse({"msg": "Task not found"}, status=400)