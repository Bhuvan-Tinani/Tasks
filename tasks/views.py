from django.utils import timezone
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from tasks.models import Project_User, Task
from tasks.models.Activity_Log import Activity_Log
from tasks.models.Comments import Comments
from tasks.models.Project import Project
from tasks.models.Role import Role
from tasks.models.Users import Users
from tasks.serailizers import ProjectSerializer
from django.core import serializers
from django.core.paginator import Paginator
from django.db.models import Case, When, IntegerField,Count
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password



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
    res = check_session(request)
    if res:
        return res

    error = None
    username = ""
    password=""

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            user = Users.objects.get(username=username)

            # Compare hashed password
            if not check_password(password, user.password):
                error = "Invalid username or password"
            else:
                # Login success
                request.session["user_id"] = user.id
                request.session["username"] = user.username
                request.session["role"] = user.role.name
                request.session["email"] = user.email

                if user.role.name == "admin":
                    response = redirect("tasks:admin")
                    response.set_cookie("user_id", user.id)
                    return response
                else:
                    return redirect("tasks:user")

        except Users.DoesNotExist:
            error = "Invalid username or password"
        except Exception as err:
            error = str(err)


    return render(request, "tasks/index.html", {"error": error, "username": username, "active_tab": "login"})

def logout(request):
    request.session.flush()
    return redirect("tasks:index")
    # return render(request,"tasks/index.html")

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
    status=None
    active_tab="signup"
    context = {"active_tab": active_tab}

    if request.method=="POST":
        form=request.POST
        username=form.get("username")
        password=form.get("password")
        email=form.get("email")
        fullname=form.get("fullname")
        
        context.update({
            "signup_username": username,
            "signup_email": email,
            "signup_fullname": fullname
        })

        if Users.objects.filter(username=username).exists():
            context.update({"msg": "Username already exists", "status": "error"})
            return render(request, "tasks/index.html", context)
        try:
            role=Role.objects.get(name="user")
            user = Users(
                username=username,
                email=email,
                password=make_password(password),
                full_name=fullname,
                role=role
            )
            user.save()

            user.save()
            user.set_creator_and_note(user)
            user.save()
            
            # On success, switch to login tab and pre-fill username
            return render(request, "tasks/index.html", {
                "msg": "User registered successfully",
                "status": "success",
                "active_tab": "login",
                "username": username
            })
        except Exception as err:
            print(err)
            context.update({"msg": str(err), "status": "error"})
            return render(request, "tasks/index.html", context)
    return render(request, "tasks/index.html", context)

def user_dashboard(request):
    if request.session.get("role") == "user":
        user_id=request.session.get("user_id")
        project=Project.objects.filter(project_user__user_id=user_id).distinct()
        return render(request,"tasks/user/dashboard.html",{"projects":project})
    return render(request,"tasks/index.html")

def manage_user(request):
    users = Users.objects.all().order_by("-id")  # Optional ordering

    # ⬇ Pagination params
    page = int(request.GET.get("page", 1))
    limit = int(request.GET.get("limit", 10))

    paginator = Paginator(users, limit)
    page_obj = paginator.get_page(page)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        users_data = []
        for user in page_obj:
            users_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.name if user.role else "",
                "created_by": user.created_by.username if user.created_by else "",
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "",
                "note": user.note,
            })

        return JsonResponse({
            "users": users_data,
            "page": page_obj.number,
            "limit": limit,
            "total_users": paginator.count,
            "total_pages": paginator.num_pages,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
            "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
            "previous_page": page_obj.previous_page_number() if page_obj.has_previous() else None,
        })

    # For normal page load
    return render(request, "tasks/admin/manage_user.html")

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
                    password=make_password(password),
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
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        roles_data = [{"id": role.id, "name": role.name} for role in roles]
        return JsonResponse({"roles": roles_data})
    return render(request,"tasks/admin/manage_role.html",{"roles":roles})

def role(request):
    if request.method=="POST":
        form=request.POST
        role_name=form.get("role_name")
        role=Role(name=role_name)
        role.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"message": "Role added successfully"})
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
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"message": "Role updated successfully"})
        except Exception as err:
            print(err)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"error": str(err)}, status=400)
    return redirect("tasks:manage_role")

def delete_role(request):
    if request.method=="POST":
        form=request.POST
        role_id=form.get("role_id")
        try:
            role=Role.objects.get(id=role_id)
            role.delete()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"message": "Role deleted successfully"})
        except Exception as err:
            print(err)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"error": str(err)}, status=400)
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
    if request.method == "POST":
        project_id = request.POST.get("project_id")
        user_ids = request.POST.getlist("user_ids[]")

        admin = Users.objects.get(id=request.session.get("user_id"))

        if admin.role.name != "admin":
            return JsonResponse({"error": "Unauthorized"}, status=403)

        # STEP 1 — Unassign from PROJECT
        deleted, _ = Project_User.objects.filter(
            project_id=project_id,
            user_id__in=user_ids
        ).delete()

        # STEP 2 — Unassign from TASKS of that project
        tasks = Task.objects.filter(
            project_id=project_id,
            assigned_to_id__in=user_ids
        )

        for task in tasks:
            old_user = task.assigned_to
            task.assigned_to = None
            task.updated_by = admin
            task.save()

            # STEP 3 — Log activity
            Activity_Log.objects.create(
                task=task,
                action="User Unassigned",
                old_value=old_user.full_name if old_user else None,
                new_value="None",
                user=admin
            )

        return JsonResponse({
            "message": "Users unassigned successfully",
            "project_unassigned_count": deleted,
            "task_unassigned_count": tasks.count()
        })

    return JsonResponse({"message": "call appropriate method"}, status=405)
    
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
        
        user_id = request.session.get("user_id")
        all_projects = Project.objects.filter(project_user__user_id=user_id).distinct()
        return render(request,"tasks/user/project_details.html",{"project":project,"users":users,"tasks": tasks, "projects": all_projects})
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
        
        Activity_Log.objects.create(
            task=task,
            action="Task Created",
            old_value=None,
            new_value=f"Task '{title}' created",
            user=session_user
        )

        if assigned_to:
            Activity_Log.objects.create(
                task=task,
                action="Assigned",
                old_value=None,
                new_value=f"Assigned to {assigned_to.full_name}",
                user=session_user
            )

        return JsonResponse({
            "message": "Task created successfully",
            "task_id": task.task_id
        })

    except Exception as e:
        print(e)
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

        task = Task.objects.get(task_id=task_id)

        old_title = task.title
        old_description = task.description
        old_priority = task.priority
        old_due_date = task.due_date
        old_assigned_to = task.assigned_to.full_name if task.assigned_to else None

        task.title = title
        task.description = description
        task.priority = priority
        task.due_date = due_date
        task.assigned_to = assigned_to
        task.updated_by = session_user
        task.updated_at = timezone.now()
        task.save()

        changes = []

        if old_title != title:
            changes.append(("title", old_title, title))

        if old_description != description:
            changes.append(("description", old_description, description))

        if old_priority != priority:
            changes.append(("priority", old_priority, priority))

        if old_due_date.strftime("%Y-%m-%d") != due_date:
            changes.append(("due_date", old_due_date.strftime("%Y-%m-%d"), due_date))

        new_assigned = assigned_to.full_name if assigned_to else None
        if old_assigned_to != new_assigned:
            changes.append(("assigned_to", old_assigned_to, new_assigned))

        # ---- STEP 4: Save each change to activity log ----
        for field, old, new in changes:
            Activity_Log.objects.create(
                task=task,
                user=session_user,
                action=f"Updated {field}",
                old_value=old,
                new_value=new,
            )

        return JsonResponse({
            "message": "Task updated successfully",
            "task_id": task.task_id,
            "changes_logged": len(changes)
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
                    "full_name": user.full_name,
                    "username":user.username
                }
                for user in users
            ]
        })
    except Project.DoesNotExist:
        return JsonResponse({"error": "user not found"}, status=404)
    
from tasks.models.Activity_Log import Activity_Log

def admin_save_task(request):
    if request.method == "POST":
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

            # 🔻 Log activity
            Activity_Log.objects.create(
                task=task,
                user=session_user,
                action="Task Created",
                old_value=None,
                new_value=f"Task '{title}' created"
            )

            # 🔻 If assigned to someone else, log assignment too
            if assigned_to and assigned_to != session_user:
                Activity_Log.objects.create(
                    task=task,
                    user=session_user,
                    action="Assigned",
                    old_value=None,
                    new_value=f"Assigned to {assigned_to.full_name}"
                )

            return JsonResponse({
                "message": "Task created successfully",
                "task_id": task.task_id
            })

        except Exception as err:
            print(err)
            return JsonResponse({"error": str(err)}, status=400)

    return JsonResponse({"error": "method not allowed"}, status=405)



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

def task_next_state(request, task_id):
    try:
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Login required"}, status=401)

        user = Users.objects.get(id=user_id)

        STATUS_FLOW = ('Todo', 'In Progress', 'Under Review', 'Done')

        task = Task.objects.get(task_id=task_id)
        old_state = task.status

        if old_state not in STATUS_FLOW:
            return JsonResponse({"error": "Invalid task status"}, status=400)

        current_index = STATUS_FLOW.index(old_state)

        if current_index == len(STATUS_FLOW) - 1:
            return JsonResponse({
                "message": "Task is already completed",
                "status": old_state,
                "completed": True
            })

        new_state = STATUS_FLOW[current_index + 1]

        task.status = new_state
        task.updated_by = user
        task.updated_at = timezone.now()
        task.save()

        Activity_Log.objects.create(
            task=task,
            user=user,
            action="Status Changed",
            old_value=old_state,
            new_value=new_state,
        )

        return JsonResponse({
            "message": "Task status updated",
            "old": old_state,
            "new": new_state,
            "completed": False
        })
 
    except Task.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def get_task_current_state(request,task_id):
    try:
        task=Task.objects.get(task_id=task_id)
        return JsonResponse({"task_status": task.status}, status=200)
    except Task.DoesNotExist:
        return JsonResponse({"msg": "Task not found"}, status=400)

def get_project_tasks(request, project_id):
    try:
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))

        title = request.GET.get("title", "").strip()
        priority = request.GET.get("priority", "").lower().strip()
        status = request.GET.get("status", "").strip()
        assigned_to = request.GET.get("assigned_to", "").strip()
        print(status)

        # ---- PROJECT INFO ----
        project = Project.objects.get(id=project_id)

        assigned_users = Project_User.objects.filter(project=project).select_related("user")

        users_data = [{
            "id": pu.user.id,
            "username": pu.user.username,
            "full_name": pu.user.full_name,
            "role": pu.user.role.name if pu.user.role else None,
        } for pu in assigned_users]

        tasks = Task.objects.filter(project_id=project_id).select_related(
            "assigned_to", "created_by", "updated_by", "project_id"
        ).annotate(
            comment_count=Count("comments__id")
        )

        # === FILTERS ===
        if title:
            tasks = tasks.filter(title__icontains=title)

        if priority and priority in ["high", "medium", "low"]:
            tasks = tasks.filter(priority=priority)

        if status and status in ["Todo", "In Progress", "Under Review", "Done"]:
            tasks = tasks.filter(status=status)

        if assigned_to:
            tasks = tasks.filter(assigned_to_id=assigned_to)

        today = timezone.localdate()

        tasks = tasks.annotate(
            status_order=Case(
                When(status="Todo", then=1),
                When(status="In Progress", then=2),
                When(status="Under Review", then=3),
                When(status="Done", then=4),
                default=99,
                output_field=IntegerField()
            ),
            priority_order=Case(
                When(priority="high", then=1),
                When(priority="medium", then=2),
                When(priority="low", then=3),
                default=99,
                output_field=IntegerField()
            )
        ).order_by("priority_order", "due_date")

        paginator = Paginator(tasks, limit)
        page_obj = paginator.get_page(page)

        tasks_data = []
        for task in page_obj:
            due = task.due_date.date()
            overdue_days = (today - due).days if due < today and task.status != "Done" else 0

            tasks_data.append({
                "task_id": task.task_id,
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "due_date": task.due_date.strftime("%Y-%m-%d"),
                "assigned_to": task.assigned_to.full_name if task.assigned_to else None,
                "assigned_to_id": task.assigned_to.id if task.assigned_to else None,
                "created_by": task.created_by.full_name if task.created_by else None,
                "updated_by": task.updated_by.full_name if task.updated_by else None,
                "project": task.project_id.title,
                "created_at": task.created_at.strftime("%Y-%m-%d %H:%M"),
                "overdue_days": overdue_days,
                "is_overdue": overdue_days > 0,
                "comment_count": task.comment_count
            })

        return JsonResponse({
            "project": {
                "id": project.id,
                "title": project.title,
                "detail": project.detail,
                "status": project.status if hasattr(project, "status") else None,
                "created_by": project.created_by.full_name if hasattr(project, "created_by") else None,
            },
            "assigned_users": users_data,

            "project_id": project_id,
            "page": page_obj.number,
            "limit": limit,
            "total_tasks": paginator.count,
            "total_pages": paginator.num_pages,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
            "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
            "previous_page": page_obj.previous_page_number() if page_obj.has_previous() else None,
            "tasks": tasks_data
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)



def add_comment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Login required"}, status=401)

        user = Users.objects.get(id=user_id)
        payload = json.loads(request.body.decode("utf-8"))
        task_id = payload.get("task_id")
        comment_text = payload.get("comment")

        if not task_id or not comment_text.strip():
            return JsonResponse({"error": "Invalid data"}, status=400)

        task = Task.objects.get(task_id=task_id)
        comment = Comments.objects.create(
            comment=comment_text,
            task=task,
            user=user
        )

        return JsonResponse({
            "message": "Comment added",
            "comment": {
                "id": comment.id,
                "text": comment.comment,
                "user": user.full_name,
                "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M")
            }
        })
    except Exception as e:
        print(e)
        return JsonResponse({"error": str(e)}, status=400)

def get_comments(request, task_id):
    try:
        comments = Comments.objects.filter(task_id=task_id).select_related("user") \
                                  .order_by("created_at")   # oldest first

        data = [{
            "id": c.id,
            "comment": c.comment,
            "user": c.user.full_name,
            "user_id": c.user.id,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M")
        } for c in comments]

        return JsonResponse({"comments": data})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

def get_task_activity_log(request, task_id):
    try:
        task = Task.objects.get(task_id=task_id)
        activity_log = Activity_Log.objects.filter(task=task).order_by("-created_at")

        data = [{
            "id": a.id,
            "action": a.action,
            "old_value": a.old_value,
            "new_value": a.new_value,
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M"),
            "user": a.user.username if a.user else "System"
        } for a in activity_log]

        return JsonResponse({"activity_log": data})

    except Exception as e:
        print(e)
        return JsonResponse({"error": str(e)}, status=400)
