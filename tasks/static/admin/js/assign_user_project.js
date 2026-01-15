$(document).ready(function () {
    const projectId = "{{ project.id }}";
    loadUsers();

    function loadUsers() {
        $.get(`/api/project/${projectId}/users/`, function (res) {
            let html = `
                        <div class="box">
                            <h3>Assigned Users</h3>
                    `;

            if (res.assigned_users.length === 0) {
                html += `<div class="empty">No users assigned</div>`;
            } else {
                res.assigned_users.forEach(u => {
                    html += `
                            <div class="user-row">
                                <span>${u.username}</span>
                                <button class="unassign-btn" data-user="${u.id}">Unassign</button>
                            </div>`;
                });
            }

            html += `</div><div class="box">
                        <h3>Available Users</h3>`;

            if (res.unassigned_users.length === 0) {
                html += `<div class="empty">All users assigned</div>`;
            } else {
                res.unassigned_users.forEach(u => {
                    html += `
                            <div class="user-row">
                                <span>${u.username}</span>
                                <button class="assign-btn" data-user="${u.id}">Assign</button>
                            </div>`;
                });
            }

            html += `</div>`;
            $("#userGrid").html(html);
        });
    }

    $(document).on("click", ".assign-btn", function () {
        const userId = $(this).data("user");
        $.post("/api/project/assign-user/", {
            project_id: projectId,
            user_id: userId,
            csrfmiddlewaretoken: "{{ csrf_token }}"
        }, loadUsers);
    });

    $(document).on("click", ".unassign-btn", function () {
        const userId = $(this).data("user");

        $.post("/tasks/api/project/unassign-user/", {
            project_id: projectId,
            "user_ids[]": userId,
            csrfmiddlewaretoken: "{{ csrf_token }}"
        }, loadUsers);
    });

});