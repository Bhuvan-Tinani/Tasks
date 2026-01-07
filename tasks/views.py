from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from tasks.models import Project_User
from tasks.models.Project import Project
from tasks.models.Role import Role
from tasks.models.Users import Users
from tasks.serailizers import ProjectSerializer
from django.views.decorators.http import require_POST

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
        return render(request,"tasks/user/dashboard.html")
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

def get_project_users(request, project_id):
    try:
        admin_id = request.session.get("user_id")
        admin = Users.objects.get(id=admin_id)

        if admin.role.name != "admin":
            return JsonResponse({"error": "Unauthorized"}, status=403)

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