
let currentProjectId = null;

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showToast(message, isError = false) {
    const toast = document.createElement('div');
    toast.className = 'toast' + (isError ? ' error' : '');
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

$(document).ready(function () {
    const statusOrder = ["Todo", "In Progress", "Under Review", "Done"];
    const projectsNavItem = document.querySelector(
        '[data-section="projects"]'
    );
    if (projectsNavItem) {
        projectsNavItem.classList.add("active");
    }

    const toggleBtn = document.getElementById("navToggle");
    
    const sidebar = document.querySelector(".sidebar");
    const toggleIcon = toggleBtn.querySelector("i");

    toggleBtn.addEventListener("click", () => {
      
      sidebar.classList.toggle("collapsed");
      if (sidebar.classList.contains("collapsed")) {
        toggleIcon.classList.remove("fa-arrow-left");
        toggleIcon.classList.add("fa-arrow-right");
      } else {
        toggleIcon.classList.remove("fa-arrow-right");
        toggleIcon.classList.add("fa-arrow-left");
      }
    });

    loadProjectsList();

    $("#addTaskBtn").on("click", function () {
        if (!currentProjectId) {
            alert("Please select a project first!");
            return;
        }

        $.ajax({
            url:
                "/tasks/admin/project/api/get_project_userdetails/" +
                currentProjectId +
                "/",
            type: "GET",
            dataType: "json",
            success: function (response) {
                const $dropdown = $("select[name='assigned_to']");
                $dropdown.empty();
                $dropdown.append(`<option value="">-- Select User --</option>`);
                response.users.forEach((u) => {
                    $dropdown.append(
                        `<option value="${u.id}">${u.username}</option>`
                    );
                });
                $("#taskModal").fadeIn(150);
            },
        });
    });

    $("#taskModal .close").on("click", function () {
        $("#taskModal").fadeOut(150);
        $("#taskForm")[0].reset();
    });

    $("#taskForm").on("submit", function (e) {
        e.preventDefault();
        const payload = {
            title: $(this).find("[name='title']").val(),
            description: $(this).find("[name='description']").val(),
            priority: $(this).find("[name='priority']").val(),
            due_date: $(this).find("[name='due_date']").val(),
            assigned_to: $(this).find("[name='assigned_to']").val(),
            project_id: currentProjectId,
        };

        $.ajax({
            url: "/tasks/admin/task/api/create/",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify(payload),
            headers: { "X-CSRFToken": CSRF_TOKEN },
            success: function (res) {
                showToast("Task created successfully!");
                $("#taskModal").fadeOut(150);
                $("#taskForm")[0].reset();
                // Reload project details to show new task
                loadProjectDetail(currentProjectId);
            },
            error: function (xhr) {
                showToast("Error creating task: " + xhr.responseText, true);
            },
        });
    });

    let selectedTaskId = null;

    $(document).on("click", ".action-btn", function () {

        selectedTaskId = $(this).data("task-id");
        if (!selectedTaskId) return;
        $("#taskActionModal").data("task-id", selectedTaskId);

        $(".tab-nav li").removeClass("active");
        $("[data-tab='editTab']").addClass("active");
        $(".tab-pane").removeClass("active");
        $("#editTab").addClass("active");

        loadTaskEdit(selectedTaskId);

        $("#taskActionModal").css("display", "flex").hide().fadeIn(150);
    });

    $(".close-tab").on("click", function () {
        $("#taskActionModal").fadeOut(150);
    });

    $(".tab-nav li").click(function () {
        $(".tab-nav li").removeClass("active");
        $(this).addClass("active");
        $(".tab-pane").removeClass("active");
        $("#" + $(this).data("tab")).addClass("active");

        const tId = $("#taskActionModal").data("task-id");

        if ($(this).data("tab") === "commentTab") loadComments(tId);
        if ($(this).data("tab") === "statusTab") loadStatusFlow(tId);
        if ($(this).data("tab") === "activityTab") loadActivityLog(tId);
    });

    function loadTaskEdit(taskId) {
        if (!taskId) return;
        $.get(`/tasks/user/api/task/get_task_details/${taskId}/`, function (res) {
            const form = $("#editTaskForm");
            form.find("input[name=task_id]").val(res.id);
            form.find("input[name=title]").val(res.title);
            form.find("textarea[name=description]").val(res.description);
            form.find("select[name=priority]").val(res.priority);
            form.find("input[name=due_date]").val(res.due_date);

            loadAssignDropdown(res.assigned_to, currentProjectId);
        });
    }

    function loadAssignDropdown(selectedId, projectId) {
        $.get(`/tasks/admin/project/api/get_project_userdetails/${projectId}/`, function (res) {
            const dropdown = $("#editTaskForm select[name=assigned_to]");
            dropdown.empty();
            dropdown.append(`<option value="">-- None --</option>`);
            res.users.forEach(u => {
                dropdown.append(`<option value="${u.id}" ${selectedId == u.id ? 'selected' : ''}>${u.username}</option>`);
            });
        });
    }

    $("#editTaskForm").on("submit", function (e) {
        e.preventDefault();
        const payload = {
            task_id: $(this).find("input[name=task_id]").val(),
            title: $(this).find("input[name=title]").val(),
            description: $(this).find("textarea[name=description]").val(),
            priority: $(this).find("select[name=priority]").val(),
            due_date: $(this).find("input[name=due_date]").val(),
            assigned_to: $(this).find("select[name=assigned_to]").val()
        };

        $.ajax({
            url: "/tasks/api/task/update/",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify(payload),
            headers: { "X-CSRFToken": CSRF_TOKEN },
            success: function (res) {
                showToast("Task updated successfully!");
                $("#taskActionModal").fadeOut(150);
                loadProjectDetail(currentProjectId);
            }
        });
    });

    function loadComments(taskId) {
        if (!taskId) return;
        $("#commentsList").html("Loading...");
        $.get(`/tasks/api/comments/get-comments/${taskId}/`, function (res) {
            $("#commentsList").empty();
            if (!res.comments || res.comments.length === 0) {
                $("#commentsList").html('<div style="text-align:center; color:#999; padding:10px;">No comments yet</div>');
                return;
            }
            res.comments.forEach(c => {
                $("#commentsList").append(`
                <div class="comment-item">
                  <div class="comment-header"><strong>${c.user}</strong> <span class="time">${c.created_at}</span></div>
                  <div>${c.comment}</div>
                </div>
              `);
            });
        });
    }

    $("#sendCommentBtn").on("click", function () {
        const text = $("#newComment").val().trim();
        if (!text) return;
        $.ajax({
            url: `/tasks/api/comment/add-comment/`,
            type: "POST",
            contentType: "application/json",
            headers: { "X-CSRFToken": CSRF_TOKEN },
            data: JSON.stringify({ task_id: selectedTaskId, comment: text }),
            success: function (res) {
                $("#newComment").val("");
                loadComments(selectedTaskId);
            }
        });
    });

    function loadStatusFlow(taskId) {
        if (!taskId) return;
        $.get(`/tasks/api/task/get-status/${taskId}/`, function (res) {
            const currentIdx = statusOrder.indexOf(res.task_status);
            $(".workflow-status-box").removeClass("active");
            $("#status" + currentIdx).addClass("active");

            if (currentIdx === statusOrder.length - 1) {
                $("#nextBtn").prop("disabled", true).text("Completed");
            } else {
                $("#nextBtn").prop("disabled", false).text("Move to Next Stage");
            }
        });
    }

    $("#nextBtn").click(function () {
        $.ajax({
            url: `/tasks/api/task/update-task/${selectedTaskId}/`,
            type: "POST",
            headers: { "X-CSRFToken": CSRF_TOKEN },
            success: function (res) { loadStatusFlow(selectedTaskId); loadProjectDetail(currentProjectId); }
        });
    });

    function loadActivityLog(taskId) {
        if (!taskId) return;
        $("#activityList").html("Loading...");
        $.get(`/tasks/api/task/get-activitylog/${taskId}/`, function (res) {
            $("#activityList").empty();
            if (!res.activity_log || res.activity_log.length === 0) {
                $("#activityList").html('<div style="text-align:center; color:#999;">No activity recorded</div>');
                return;
            }
            res.activity_log.forEach(log => {
                $("#activityList").append(`
                <div class="activity-item">
                  <div><b>${log.user}</b> ${log.action}</div>
                  <small>${log.created_at}</small>
                </div>
              `);
            });
        });
    }

    function loadUsers(page = 1, limit = 10) {
        $.get(`/tasks/admin/manage_user?page=${page}&limit=${limit}`, function (res) {
            const tbody = $("#usersTableBody");
            tbody.empty();

            res.users.forEach(u => {
                tbody.append(`
                <tr>
                    <td>${u.full_name}</td>
                    <td>${u.username}</td>
                    <td>${u.email}</td>
                    <td>${u.role}</td>
                    <td>${u.created_by}</td>
                    <td>${u.created_at}</td>
                    <td>${u.note}</td>
                    <td><i class="fa fa-info-circle"></i></td>
                </tr>
            `);
            });

            renderPaginationuser(res);
        });
    }

    function renderPaginationuser(res) {
        let paginationDiv = $("#pagination1");
        if (paginationDiv.length === 0) {
            $(".section.active").append(
                `<div id="pagination1" class="pagination-container"></div>`
            );
            paginationDiv = $("#pagination1");
        }
        paginationDiv.empty();


        let prevDisabled = res.has_previous ? "" : "disabled";
        let nextDisabled = res.has_next ? "" : "disabled";

        paginationDiv.append(`
                <button class="page-btn" ${prevDisabled} data-page="${res.previous_page}"><i class="fa fa-chevron-left"></i> Prev</button>
                <span class="page-info"> Page ${res.page} of ${res.total_pages} </span>
                <button class="page-btn" ${nextDisabled} data-page="${res.next_page}">Next <i class="fa fa-chevron-right"></i></button>
            `);

        $(".page-btn").on("click", function () {
            const p = $(this).data("page");

            if (p) loadUsers(p);
        });
    }
    function loadRolesList() {
        $("#rolesTableBody").html('<tr><td colspan="3" style="text-align:center; padding: 20px;">Loading...</td></tr>');
        $.ajax({
            url: "/tasks/admin/manage_role",
            type: "GET",
            dataType: "json",
            success: function (response) {
                const $tbody = $("#rolesTableBody").empty();
                let roles = response.roles || [];

                if (roles.length === 0) {
                    $tbody.html('<tr><td colspan="3" style="text-align:center; padding: 20px;">No roles found</td></tr>');
                    return;
                }

                roles.forEach(r => {
                    $tbody.append(`
                  <tr>
                    <td>${r.id}</td>
                    <td>${r.name}</td>
                    <td>
                        <button class="action-btn edit-role-btn" data-id="${r.id}" data-name="${r.name}"><i class="fas fa-edit"></i></button>
                        <button class="action-btn delete-role-btn" data-id="${r.id}" style="color: #d32f2f;"><i class="fas fa-trash"></i></button>
                    </td>
                  </tr>
                `);
                });
            },
            error: function (xhr) {
                $("#rolesTableBody").html('<tr><td colspan="3" style="text-align:center; color:red; padding: 20px;">Error loading roles</td></tr>');
            }
        });
    }

    $("#openAddRoleModalBtn").click(function () { $("#addRoleModal").fadeIn(150); });
    $("#addRoleModal .close").click(function () { $("#addRoleModal").fadeOut(150); });

    $("#addRoleForm").submit(function (e) {
        e.preventDefault();
        $.ajax({
            url: "/tasks/admin/role",
            type: "POST",
            data: $(this).serialize(),
            headers: { "X-CSRFToken": CSRF_TOKEN },
            success: function (res) {
                showToast("Role added successfully");
                $("#addRoleModal").fadeOut(150);
                $("#addRoleForm")[0].reset();
                loadRolesList();
            }
        });
    });

    $(document).on("click", ".edit-role-btn", function () {
        const id = $(this).data("id");
        const name = $(this).data("name");
        $("#editRoleForm [name=role_id]").val(id);
        $("#editRoleForm [name=role_name]").val(name);
        $("#editRoleModal").fadeIn(150);
    });
    $("#editRoleModal .close").click(function () { $("#editRoleModal").fadeOut(150); });

    $("#editRoleForm").submit(function (e) {
        e.preventDefault();
        $.ajax({
            url: "/tasks/admin/edit_role",
            type: "POST",
            data: $(this).serialize(),
            headers: { "X-CSRFToken": CSRF_TOKEN },
            success: function (res) {
                showToast("Role updated successfully");
                $("#editRoleModal").fadeOut(150);
                loadRolesList();
            }
        });
    });

    $(document).on("click", ".delete-role-btn", function () {
        const id = $(this).data("id");
        $("#deleteRoleForm [name=role_id]").val(id);
        $("#deleteRoleModal").fadeIn(150);
    });
    $("#deleteRoleModal .close, #cancelDeleteRoleBtn").click(function () { $("#deleteRoleModal").fadeOut(150); });

    $("#deleteRoleForm").submit(function (e) {
        e.preventDefault();
        $.ajax({
            url: "/tasks/admin/delete_role",
            type: "POST",
            data: $(this).serialize(),
            headers: { "X-CSRFToken": CSRF_TOKEN },
            success: function (res) {
                showToast("Role deleted successfully");
                $("#deleteRoleModal").fadeOut(150);
                loadRolesList();
            }
        });
    });

    $("#openAddUserModalBtn").on("click", function () {
        $("#addUserModal").fadeIn(150);
    });

    $("#addUserModal .close").on("click", function () {
        $("#addUserModal").fadeOut(150);
        $("#addUserForm")[0].reset();
        $("#u_usernameMsg, #u_passwordMsg, #u_emailMsg").text("");
    });

    let usernameValid = false;
    let emailValid = false;
    let passwordValid = false;

    function toggleUserSubmit() {
        $("#submitUserBtn").prop("disabled", !(usernameValid && emailValid && passwordValid));
    }

    $("#u_username").on("keyup blur", function () {
        let username = $(this).val().trim();
        if (username.length < 4) {
            $("#u_usernameMsg").text("Username must be 4+ chars").css("color", "red");
            usernameValid = false;
            toggleUserSubmit();
            return;
        }
        $.ajax({
            url: "/api/check-username/",
            type: "GET",
            data: { username: username },
            success: function (res) {
                if (res.exists) {
                    $("#u_usernameMsg").text("Username already exists").css("color", "red");
                    usernameValid = false;
                } else {
                    $("#u_usernameMsg").text("Available").css("color", "green");
                    usernameValid = true;
                }
                toggleUserSubmit();
            }
        });
    });

    $("#u_email").on("keyup blur", function () {
        const email = $(this).val().trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            $("#u_emailMsg").text("Invalid email format").css("color", "red");
            emailValid = false;
            toggleUserSubmit();
            return;
        }
        $.ajax({
            url: "/api/check-email/",
            type: "GET",
            data: { email: email },
            success: function (res) {
                if (res.exists) {
                    $("#u_emailMsg").text("Email already exists").css("color", "red");
                    emailValid = false;
                } else {
                    $("#u_emailMsg").text("Available").css("color", "green");
                    emailValid = true;
                }
                toggleUserSubmit();
            }
        });
    });

    $("#u_password").on("keyup blur", function () {
        const password = $(this).val();
        passwordValid = password.length >= 8 && /[A-Z]/.test(password) && /[a-z]/.test(password) && /\d/.test(password) && /[@$!%*?&]/.test(password);

        if (passwordValid) {
            $("#u_passwordMsg").text("Strong password").css("color", "green");
        } else {
            $("#u_passwordMsg").text("Min 8 chars, upper, lower, number & special").css("color", "red");
        }
        toggleUserSubmit();
    });

    $("#addUserForm").on("submit", function (e) {
        e.preventDefault();
        const formData = $(this).serialize();

        $.ajax({
            url: "/tasks/admin/add_user",
            type: "POST",
            data: formData,
            headers: { "X-CSRFToken": CSRF_TOKEN },
            success: function (res) {
                showToast("User created successfully!");
                $("#addUserModal").fadeOut(150);
                $("#addUserForm")[0].reset();
                loadUsers();
            },
            error: function (xhr) {
                showToast("Error creating user", true);
            }
        });
    });

    $("#assignUserModal .close").on("click", function () {
        $("#assignUserModal").fadeOut(150);
    });

    $(document).on("click", ".open-assign-modal", function (e) {
        e.stopPropagation();
        const projectId = $(this).data("project-id");
        const projectName = $(this).data("project-name");

        $("#assignProjectName").text(projectName);
        $("#assignUserModal").data("project-id", projectId).fadeIn(150);
        loadAssignUsers(projectId);
    });

    function loadAssignUsers(projectId) {
        $("#assignUserGrid").html('<div style="grid-column: 1/-1; text-align:center;">Loading...</div>');
        $.ajax({
            url: `/tasks/admin/project/api/get_project_users_admin/${projectId}/`,
            type: "GET",
            success: function (res) {

                let html = `<div class="assign-box"><h4>Assigned Users</h4>`;
                if (res.assigned_users.length === 0) {
                    html += `<div class="assign-empty">No users assigned</div>`;
                } else {
                    res.assigned_users.forEach(u => {
                        html += `<div class="assign-user-row">
                                <span>${u.username}</span>
                                <button class="assign-action-btn btn-unassign" data-user="${u.id}">Unassign</button>
                            </div>`;
                    });
                }
                html += `</div><div class="assign-box"><h4>Available Users</h4>`;
                if (res.unassigned_users.length === 0) {
                    html += `<div class="assign-empty">All users assigned</div>`;
                } else {
                    res.unassigned_users.forEach(u => {
                        html += `<div class="assign-user-row">
                                <span>${u.username}</span>
                                <button class="assign-action-btn btn-assign" data-user="${u.id}">Assign</button>
                            </div>`;
                    });
                }
                html += `</div>`;
                $("#assignUserGrid").html(html);
            },
            error: function (xhr) {
                $("#assignUserGrid").html('<div style="color:red; text-align:center;">Error loading users</div>');
            }
        });
    }


    $(document).on("click", ".btn-assign", function () {
        const userId = $(this).data("user");
        const projectId = $("#assignUserModal").data("project-id");
        $.post("/tasks/admin/project/api/assign_user/", {
            project_id: projectId, user_id: userId, csrfmiddlewaretoken: CSRF_TOKEN
        }, function () {
            loadAssignUsers(projectId);
            loadProjectDetail(projectId);
        });
    });

    $(document).on("click", ".btn-unassign", function () {
        const userId = $(this).data("user");
        const projectId = $("#assignUserModal").data("project-id");
        $.post("/tasks/admin/project/api/unassign_user/", {
            project_id: projectId, user_id: userId, csrfmiddlewaretoken: CSRF_TOKEN
        }, function () {
            loadAssignUsers(projectId);
            loadProjectDetail(projectId);
        });
    });

    const projectsSection = document.querySelector(
        '[data-section="projects"]'
    );
    if (projectsSection) {
        projectsSection.click();
    }

    $("#addProjectBtn").on("click", function () {
        $("#projectModal").fadeIn(150);
    });

    $("#projectModal .close").on("click", function () {
        $("#projectModal").fadeOut(150);
        $("#projectForm")[0].reset();
    });

    $("#projectForm").on("submit", function (e) {
        e.preventDefault();

        const payload = {
            title: $(this).find("[name='title']").val(),
            detail: $(this).find("[name='description']").val(),
            created_by: getCookie("user_id")
        };

        const $btn = $(this).find("button[type='submit']").prop("disabled", true);

        $.ajax({
            url: "/tasks/admin/api/project/",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify(payload),
            headers: { "X-CSRFToken": CSRF_TOKEN },
            success: function (res) {
                $("#projectModal").fadeOut(150);
                $("#projectForm")[0].reset();
                showToast("Project created successfully!");
                loadProjectsList();
            },
            error: function (xhr) {
                showToast("Error creating project: " + (xhr.responseText || xhr.statusText), true);
            },
            complete: function () {
                $btn.prop("disabled", false);
            },
        });
    });


    function loadProjectsList() {
        $.ajax({
            url: "/tasks/admin/project/api/get_projects/",
            type: "GET",
            dataType: "json",
            success: function (response) {
                let projectData = [];
                try {
                    if (!response) {
                        projectData = [];
                    } else if (Array.isArray(response)) {
                        projectData = response;
                    } else if (response.projects) {
                        if (typeof response.projects === "string") {
                            projectData = JSON.parse(response.projects);
                        } else if (Array.isArray(response.projects)) {
                            projectData = response.projects;
                        }
                    } else if (response.data && Array.isArray(response.data)) {
                        projectData = response.data;
                    } else if (response.pk || response.id) {
                        projectData = [response];
                    }
                } catch (err) {
                    console.error("Failed to parse projects response", err, response);
                    projectData = [];
                }

                const projectsContainer = document.querySelector(".projects-items-wrapper");
                if (!projectsContainer) return;

                projectsContainer.innerHTML = "";

                if (!projectData || projectData.length === 0) {
                    const emptyEl = document.createElement("div");
                    emptyEl.className = "project-item";
                    emptyEl.innerHTML =
                        '<div class="project-name">No projects found</div>';
                    projectsContainer.appendChild(emptyEl);
                    return;
                }

                projectData.forEach((item, index) => {

                    const title =
                        (item.fields && item.fields.title) ||
                        item.title ||
                        item.name ||
                        "Untitled";
                    const status =
                        (item.fields && item.fields.status) || item.fields.detail || "Active";
                    const pk = item.pk || item.id || item.project_id;


                    const projectEl = document.createElement("div");
                    projectEl.className =
                        "project-item" + (index === 0 ? " active" : "");
                    projectEl.setAttribute("data-project", pk);
                    projectEl.innerHTML = `
                        <div>
                            <div class="project-name">${title}</div>
                            <div class="project-status">${status}</div>
                        </div>
                        <a class="assign-btn-list open-assign-modal" data-project-id="${pk}" data-project-name="${title}" title="Assign Users" href='admin/assign_users?project_id=${item.pk}'>
                            <i class="fas fa-user-plus"></i>
                        </a>
                    `;

                    projectEl.addEventListener("click", function () {
                        document
                            .querySelectorAll(".project-item")
                            .forEach(i => i.classList.remove("active"));

                        this.classList.add("active");

                        currentProjectId = pk;

                        document.querySelector(".page-title").textContent = title;


                        $("#projectInfo").data("project-id", pk);

                        loadProjectDetail(pk);
                    });
                    if (index === 0) {
                        projectEl.classList.add("active");
                    }
                    projectsContainer.appendChild(projectEl);
                });
                const firstItem = projectData[0];
                const firstPk = firstItem.pk || firstItem.id || firstItem.project_id;


                if (firstPk) {
                    currentProjectId = firstPk;
                    $("#projectInfo").data("project-id", currentProjectId);
                    loadProjectDetail(firstPk);

                    document.querySelector(".page-title").textContent =
                        (firstItem.fields && firstItem.fields.title) ||
                        firstItem.title ||
                        firstItem.name ||
                        "Untitled";
                }
            },
        });
    }

    function loadProjectDetail(projectId, page = 1, limit = 10) {
        // $.ajax({
        //   url: `/tasks/api/project/${projectId}/tasks/?page=${page}&limit=${limit}`,
        //   type: "GET",
        //   dataType: "json",
        //   success: function (response) {
        //     try {

        //       const payload = response.project || response || {};
        //       setProjectUsers(payload);
        //     } catch (err) {
        //       console.error("Error processing project detail", err, response);
        //     }
        //   },
        //   error: function (xhr) {
        //     console.error("Error loading project detail:", xhr.responseText);
        //   },
        // });

        const searchType = $("#searchType").val();
        let query = `page=${page}&limit=${limit}`;

        if (searchType === "title") {
            const title = $("#searchInput").val();
            if (title) query += `&title=${encodeURIComponent(title)}`;
        }
        if (searchType === "priority") {
            const val = $("#priorityFilter").val();
            if (val) query += `&priority=${val}`;
        }
        if (searchType === "status") {
            const val = $("#statusFilter").val();
            if (val) query += `&status=${encodeURIComponent(val)}`;
        }


        $.get(`/tasks/api/project/${projectId}/tasks/?${query}`, function (res) {
            setProjectUsers(res);
        });
    }

    function setProjectUsers(response) {

        const name =
            response.project.title ||
            response.name ||
            (response.fields && response.fields.title) ||
            "";
        const desc =
            response.project.detail ||
            response.description ||
            (response.fields && response.fields.description) ||
            "";
        const statusText =
            response.status || (response.fields && response.fields.status) || "";
        const progress = response.progress || response.progress_percent || "";


        $("#detail-project-name").text(name);
        $("#detail-project-desc").text(desc);
        $("#detail-project-status").text(
            statusText || (statusText === "" ? "" : "")
        );
        if (progress) $(".detail-progress").text(progress);

        const $usersList = $(".users-list").empty();
        const users =
            response.users || response.user_list || response.assigned_users || [];

        if (!users || users.length === 0) {
            $usersList.append(
                `<div class="user-badge"><i class="fas fa-user-circle"></i><span>No users assigned</span></div>`
            );
        } else {
            users.forEach((u) => {
                const label = u.full_name || u.username || u.name || "-";
                const role = u.role || u.designation || "";
                $usersList.append(`
                    <div class="user-badge">
                        <i class="fas fa-user-circle"></i>
                        <span>${label}</span>
                        ${role ? `<small>${role}</small>` : ""}
                    </div>
                `);
            });
        }


        const $tasksBody = $("#projectTasksBody").empty();
        const tasks = response.tasks || response.task_list || [];
        if (!tasks || tasks.length === 0) {
            $tasksBody.append(`<tr><td colspan="6">No tasks</td></tr>`);
        } else {
            tasks.forEach((t) => {
                let assignedTo = t.assigned_to ?? "-";
                let createdBy = t.created_by ?? "-";
                let updatedBy = t.updated_by ?? "-";


                let overdueBadge = "";
                if (t.is_overdue) {
                    overdueBadge = `<span class="overdue-badge">Overdue by ${t.overdue_days} days</span>`;
                }

                if (t.is_overdue) {
                    overdueBadge = `<span class="overdue-badge">Overdue by ${t.overdue_days} days</span>`;
                }

                let statusClass =
                    "badge-status-" +
                    t.status.replace(/\s+/g, "-").toLowerCase();
                if (t.is_overdue && t.status !== "Done")
                    statusClass = "badge-status-overdue";

                let priorityClass =
                    "badge-priority-" + (t.priority || "low").toLowerCase();

                let commentBadge = "";
                if (t.comment_count > 0) {
                    commentBadge = `<span class="comment-count">${t.comment_count}</span>`;
                }
                const taskId = t.id || t.pk || "" || t.task_id

                const title = t.title || t.name || "";
                const assignee =
                    t.assigned_to_name ||
                    t.assigned_to ||
                    t.assigned_to_username ||
                    "-";
                const status = (t.status || "").toLowerCase();
                const due = t.due_date || t.due || "-";
                const priority = (t.priority || "").toLowerCase();

                const statusCls =
                    status === "completed"
                        ? "completed"
                        : status === "in progress" || status === "in-progress"
                            ? "in-progress"
                            : "pending";
                const priorityCls =
                    priority === "high"
                        ? "high"
                        : priority === "medium"
                            ? "medium"
                            : "low";

                $tasksBody.append(`
                    <tr class="${t.is_overdue ? "row-overdue" : ""}">
                        <td>
                                    ${t.title}<br>
                                    ${overdueBadge}
                                </td>
                                <td>
                                    <span class="badge ${priorityClass}">${t.priority}</span>
                                </td>
                                <td>
                                    <span class="badge ${statusClass}">${t.status}</span>
                                </td>
                                <td>${assignedTo}</td>
                                <td>${t.due_date}</td>
                                <td>${createdBy}</td>
                                <td>${updatedBy}</td>
                        <td><button class="action-btn" data-task-id="${taskId}"><i class="fas fa-ellipsis-v"></i></button></td>
                    </tr>
                `);

            });
            renderPagination(response);
        }

    }
    function renderPagination(res) {


        let paginationDiv = $("#pagination");

        if (paginationDiv.length === 0) {
            $(".project-tasks").append(
                `<div id="pagination" class="pagination-container"></div>`
            );
            paginationDiv = $("#pagination");
        }
        paginationDiv.empty();

        let prevDisabled = res.has_previous ? "" : "disabled";
        let nextDisabled = res.has_next ? "" : "disabled";

        paginationDiv.append(`
                <button class="page-btn" ${prevDisabled} data-page="${res.previous_page}"><i class="fa fa-chevron-left"></i> Prev</button>
                <span class="page-info"> Page ${res.page} of ${res.total_pages} </span>
                <button class="page-btn" ${nextDisabled} data-page="${res.next_page}">Next <i class="fa fa-chevron-right"></i></button>
            `);

        $(".page-btn").on("click", function () {
            const p = $(this).data("page");

            currentProjectId = $("#projectInfo").data("project-id");

            if (p) loadProjectDetail(currentProjectId, p);
        });
    }

    document.querySelectorAll(".nav-item").forEach((item) => {
        item.addEventListener("click", function (e) {
            e.preventDefault();

            const sectionName = this.getAttribute("data-section");
            const sectionId = sectionName + "-section";

            document
                .querySelectorAll(".nav-item")
                .forEach((i) => i.classList.remove("active"));
            this.classList.add("active");

            document.querySelectorAll(".section").forEach((section) => {
                section.classList.remove("active");
            });
            document.getElementById(sectionId).classList.add("active");

            const titleMap = {
                projects: "Projects",
                users: "Users",
                roles: "Roles",
            };
            document.querySelector(".page-title").textContent =
                titleMap[sectionName];

            if (sectionName === 'users') {
                loadUsers();
            }
            if (sectionName === 'roles') {
                loadRolesList();
            }
        });
    });

    $("#searchType").on("change", function () {
        const type = $(this).val();

        $("#searchInput").toggle(type === "title");
        $("#priorityFilter").toggle(type === "priority");
        $("#statusFilter").toggle(type === "status");

        applyFilters();
    });

    $("#searchInput, #priorityFilter, #statusFilter").on("input change", function () {
        applyFilters();
    });

    function applyFilters() {
        currentProjectId = $("#projectInfo").data("project-id");
        if (currentProjectId) loadProjectDetail(currentProjectId);
    }
});

