let showMyTasksOnly = false;

$(document).ready(function () {
    const modal = $("#taskModal");
    const taskForm = $("#taskForm");
    let currentProjectId = $("#projectInfo").data("project-id");

    loadTasks(currentProjectId);

    $(".add-task-btn").on("click", function () {
        modal.show();
    });

    modal.find(".close").on("click", function () {
        closeModal();
    });

    $(window).on("click", function (e) {
        if ($(e.target).is(modal)) {
            closeModal();
        }
    });

    function closeModal() {
        modal.hide();
        taskForm[0].reset();
    }

    taskForm.on("submit", function (e) {
        e.preventDefault();

        $.ajax({
            url: "/user/api/task/create/",
            type: "POST",
            data: new FormData(this),
            processData: false,
            contentType: false,
            headers: {
                "X-CSRFToken": csrf_token,
            },
            success: function (res) {
                if (res.error) {
                    // alert(res.error);
                    showToast(res.error, true)
                } else {
                    showToast("Task created successfully")
                    // alert("Task created successfully");////////////////////////////////////////////
                    setTimeout(function () {
                        closeModal();
                        location.reload();
                    }, 1000);

                }
            },
            error: function (err) {
                showToast(err.responseJSON.error, true)
            },
        });
    });

    $("#myTasksBtn").on("click", function () {
        showMyTasksOnly = true;
        $(this).css("background-color", "#1565c0");
        $("#allTasksBtn").css("background-color", "#1976d2");
        applyFilters();
    });

    $("#allTasksBtn").on("click", function () {
        showMyTasksOnly = false;
        $(this).css("background-color", "#1565c0");
        $("#myTasksBtn").css("background-color", "#1976d2");
        applyFilters();
    });

    $(document).on("click", ".btn-edit", function () {
        const taskId = $(this).data("id");
        $.get(
            "/tasks/user/api/task/get_task_details/" + taskId + "/",
            function (res) {
                const form = $("#editTaskForm");

                form.find("input[name=task_id]").val(res.id);
                form.find("input[name=title]").val(res.title);
                form.find("textarea[name=description]").val(res.description);
                form.find("select[name=status]").val(res.status);
                form.find("select[name=priority]").val(res.priority);
                form.find("input[name=due_date]").val(res.due_date);
                form.find("select[name=assigned_to]").val(res.assigned_to ?? "");

                openEditModal();
            }
        );
    });

    $(".edit-close").on("click", function () {
        closeEditModal();
    });

    function showToast(message, isError = false) {
        const toast = document.createElement('div');
        toast.className = 'toast' + (isError ? ' error' : '');
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(toast);
                if (isError) {
                    window.location.reload();
                }
            }, 300);
        }, 2000);

    }

    const editModal = $("#editTaskModal");
    const editForm = $("#editTaskForm");

    function openEditModal() {
        editModal.show();
    }

    function closeEditModal() {
        editModal.hide();
        editForm[0].reset();
    }

    $("#editTaskForm").on("submit", function (e) {
        e.preventDefault();

        const modal = $("#editTaskModal");

        const payload = {
            task_id: modal.find("input[name=task_id]").val(),
            title: modal.find("input[name=title]").val(),
            description: modal.find("textarea[name=description]").val(),
            priority: modal.find("select[name=priority]").val(),
            due_date: modal.find("input[name=due_date]").val(),
            assigned_to: modal.find("select[name=assigned_to]").val(),
        };

        $.ajax({
            url: "/tasks/api/task/update/",
            type: "POST",
            data: JSON.stringify(payload),
            contentType: "application/json",
            headers: { "X-CSRFToken": csrf_token },
            success: function (res) {
                // alert("Task updated");
                showToast("Task updated")
                setTimeout(function () {
                    closeEditModal();
                    location.reload();
                }, 800)

            },
            error: function (err) {
                showToast(err.responseJSON.error, true)
            },
        });
    });

    const statusOrder = ["Todo", "In Progress", "Under Review", "Done"];
    let current = 0;
    let taskId = null;

    $(document).on("click", ".status-btn", function () {
        taskId = $(this).data("id");

        $("#popup").addClass("show");
        $("#overlay").addClass("show");

        $.get(`/tasks/api/task/get-status/${taskId}/`, function (res) {
            current = statusOrder.indexOf(res.task_status);

            $(".workflow-status-box").removeClass("active");

            $("#status" + current).addClass("active");

            if (current === statusOrder.length - 1) {
                $("#nextBtn").prop("disabled", true).text("Completed!");
            } else {
                $("#nextBtn").prop("disabled", false).text("Next");
            }
        });
    });

    $("#closeBtn, #overlay").click(function () {
        location.reload();
        $("#popup").removeClass("show");
        $("#overlay").removeClass("show");
    });

    $("#nextBtn").click(function () {
        if (current < statusOrder.length - 1) {
            current++;

            $(".workflow-status-box").removeClass("active");
            $("#status" + current).addClass("active");

            const newStatus = statusOrder[current];

            updateTaskStatus();

            if (current === statusOrder.length - 1) {
                $("#nextBtn").prop("disabled", true).text("Completed!");
            }
        }
    });

    function updateTaskStatus() {
        $.ajax({
            url: `/tasks/api/task/update-task/${taskId}/`,
            type: "POST",
            contentType: "application/json",
            headers: { "X-CSRFToken": csrf_token },
            success: function (res) {
                console.log("Status updated:", res);
            },
            error: function (err) {

                showToast(err.responseJSON.error, true)
            },
        });
    }

    $(document).on("click", ".btn-comment", function () {
        const taskId = $(this).data("id");

        $("#commentsModal").data("task-id", taskId);
        // $("#commentsModal").addClass("show");
        $("#commentsModal").show();
        loadComments(taskId);
    });

    $(document).on("click", ".close-comment", function () {
        closeCommentsModal();
    });

    $("#sendCommentBtn").on("click", function () {
        taskId = $("#commentsModal").data("task-id");

        const commentText = $("#newComment").val().trim();
        // const taskId = $("#commentsModal").data("task-id");

        if (!commentText) return;

        $.ajax({
            url: "/tasks/api/comment/add-comment/",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                task_id: taskId,
                comment: commentText,
            }),
            headers: { "X-CSRFToken": csrf_token },
            success: function (res) {
                $("#newComment").val("");

                $("#commentsList").append(`
                            <div class="comment-item">
                                <div class="comment-header">
                                    <span class="comment-user">${res.comment.user}</span>
                                </div>
                                <div class="comment-body">
                                    ${res.comment.text}
                                </div>
                                <div class="comment-footer">
                                    <span class="comment-time">${res.comment.created_at}</span>
                                </div>
                            </div>
                        `);
            },
            error: function (err) {
                console.log(err);

                showToast(err.responseJSON.error, true)
            },
        });
    });

    $("#searchType").on("change", function () {
        const type = $(this).val();

        $("#searchInput").toggle(type === "title");
        $("#priorityFilter").toggle(type === "priority");
        $("#statusFilter").toggle(type === "status");
        console.log("from 289");
        

        applyFilters();
    });

    $("#searchInput").on("input change",function(){
        const title = $("#searchInput").val()
        if(title.length!=0){
            applyFilters()
        }
    })

    $("#priorityFilter").change(function(){
        applyFilters();
    })

    $("#statusFilter").change(function(){
        applyFilters();
    })

    // $("#priorityFilter, #statusFilter").on("input change", function () {
    //     console.log("303");
        
    //     applyFilters();
    // });

    function applyFilters() {
        currentProjectId = $("#projectInfo").data("project-id");
        
        if (currentProjectId) loadTasks(currentProjectId);
        
    }
});

function loadTasks(projectId, page = 1, limit = 10) {
    
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
    if (showMyTasksOnly) {
        query += `&assigned_to=${SESSION_USER_ID}`;
    }

    $.ajax({
        url: `/tasks/api/project/${projectId}/tasks/?page=${page}&limit=${limit}`,
        url: `/tasks/api/project/${projectId}/tasks/?${query}`,
        type: "GET",
        dataType: "json",
        success: function (res) {
            const tbody = $("#taskTableBody");
            tbody.empty();

            if (res.tasks.length === 0) {
                tbody.append(
                    `<tr><td colspan="8" class="empty">No tasks found</td></tr>`
                );
                return;
            }

            res.tasks.forEach((task) => {
                let assignedTo = task.assigned_to ?? "-";
                let createdBy = task.created_by ?? "-";
                let updatedBy = task.updated_by ?? "-";

                let overdueBadge = "";
                if (task.is_overdue) {
                    overdueBadge = `<span class="overdue-badge">Overdue by ${task.overdue_days} days</span>`;
                }

                let statusClass =
                    "badge-status-" +
                    task.status.replace(/\s+/g, "-").toLowerCase();
                if (task.is_overdue && task.status !== "Done")
                    statusClass = "badge-status-overdue";

                let priorityClass =
                    "badge-priority-" + (task.priority || "low").toLowerCase();

                let commentBadge = "";
                if (task.comment_count > 0) {
                    commentBadge = `<span class="comment-count">${task.comment_count}</span>`;
                }

                let actions = `
              <button class="icon-btn btn-comment" data-id="${task.task_id}" title="Comments">
                  <i class="fa fa-comments"></i>${commentBadge}
              </button>
            `;

                if (task.assigned_to_id == SESSION_USER_ID) {
                    actions =
                        `
                                <button class="icon-btn btn-edit" data-id="${task.task_id}" title="Edit">
                                    <i class="fa fa-pencil"></i>
                                </button>
                                <button class="icon-btn status-btn" data-id="${task.task_id}" title="Update Status">
                                    <i class="fa fa-refresh"></i>
                                </button>
                            ` + actions;
                }

                actions = `<div class="action-btn-group">${actions}</div>`;

                const row = `
                            <tr class="${task.is_overdue ? "row-overdue" : ""}">
                                <td>
                                    ${task.title}<br>
                                    ${overdueBadge}
                                </td>
                                <td>
                                    <span class="badge ${priorityClass}">${task.priority}</span>
                                </td>
                                <td>
                                    <span class="badge ${statusClass}">${task.status}</span>
                                </td>
                                <td>${assignedTo}</td>
                                <td>${task.due_date}</td>
                                <td>${createdBy}</td>
                                <td>${updatedBy}</td>
                                <td>${actions}</td>
                            </tr>
                        `;

                tbody.append(row);
            });

            renderPagination(res);
        },
        error: function (xhr) {
            console.error(xhr.responseText);
        },
    });
}
function renderPagination(res) {

    let paginationDiv = $("#pagination");

    if (paginationDiv.length === 0) {
        $(".col-tasks").append(
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

        if (p) loadTasks(currentProjectId, p);
    });
}

function closeCommentsModal() {
    $("#commentsModal").hide();
}

function appendComment(c) {
    $("#commentsList").append(`
                <div class="comment-item">
                    <div class="comment-header">
                        <span class="comment-user">${c.user}</span>
                    </div>
                   <div class="comment-body">
                        ${c.comment}
                    </div>
                    <div class="comment-footer">
                        <span class="comment-time">${c.created_at}</span>
                    </div>
                </div>
            `);
}

function loadComments(taskId) {
    $("#commentsList").html(`<div class="loading">Loading...</div>`);

    $.get(`/tasks/api/comments/get-comments/${taskId}/`)
        .done(function (res) {
            $("#commentsList").empty();

            if (!res.comments || res.comments.length === 0) {
                $("#commentsList").html(
                    `<div class="no-comments">No comments yet</div>`
                );
                return;
            }

            res.comments.forEach((c) => appendComment(c));

            const container = document.getElementById("commentsList");
            container.scrollTop = container.scrollHeight;
        })
        .fail(function (xhr) {
            showToast(xhr.responseJSON.error, true);
        });

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
            if (isError) {
                window.location.reload();
            }
        }, 300);
    }, 2000);

}