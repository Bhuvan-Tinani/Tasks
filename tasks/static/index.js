$(document).ready(function () {

    let usernameValid = false;
    let emailValid = false;
    let passwordValid = false;
    let confirmPasswordValid = false;

    // Tab switching
    $(".nav-link").click(function (e) {
        e.preventDefault();
        const target = $(this).attr("href");

        $(".nav-link").removeClass("active");
        $(this).addClass("active");

        $(".tab-content").removeClass("show");
        $(target).addClass("show");

        // Reset signup form when switching to signup
        if (target === "#signup") {
            resetSignupForm();
        }
    });

    function resetSignupForm() {
        $("#signupForm")[0].reset();
        $("#usernameMsg").text("");
        $("#emailMsg").text("");
        $("#passwordMsg").text("");
        $("#confirmPasswordMsg").text("");
        usernameValid = false;
        emailValid = false;
        passwordValid = false;
        confirmPasswordValid = false;
        updateSubmitButton();
    }

    function updateSubmitButton() {
        $("#submitBtn").prop("disabled", !(usernameValid && emailValid && passwordValid && confirmPasswordValid));
    }

    // Username validation
    $("#signup-username").on("keyup blur", function () {
        let username = $(this).val().trim();

        if (username.length < 4) {
            $("#usernameMsg").text("username must be 4 characters or longer").css("color", "red");
            usernameValid = false;
            updateSubmitButton();
            return;
        }

        $.ajax({
            url: "/api/check-username/",
            type: "GET",
            data: { username: username },
            success: function (response) {
                if (response.exists) {
                    $("#usernameMsg").text("Username already exists").css("color", "red");
                    usernameValid = false;
                } else {
                    $("#usernameMsg").text("").css("color", "green");
                    usernameValid = true;
                }
                updateSubmitButton();
            }
        });
    });

    // Email validation
    $("#signup-email").on("keyup blur", function () {
        const email = $(this).val().trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (email === "") {
            $("#emailMsg").text("");
            emailValid = false;
            updateSubmitButton();
            return;
        }

        if (!emailRegex.test(email)) {
            $("#emailMsg").text("Invalid email format").css("color", "red");
            emailValid = false;
            updateSubmitButton();
            return;
        }

        $.ajax({
            url: "/api/check-email/",
            type: "GET",
            data: { email: email },
            success: function (response) {
                if (response.exists) {
                    $("#emailMsg").text("Email already exists").css("color", "red");
                    emailValid = false;
                } else {
                    $("#emailMsg").text("").css("color", "green");
                    emailValid = true;
                }
                updateSubmitButton();
            }
        });
    });

    // Password validation
    $("#signup-password").on("keyup blur", function () {
        const password = $(this).val();

        passwordValid =
            password.length >= 8 &&
            /[A-Z]/.test(password) &&
            /[a-z]/.test(password) &&
            /\d/.test(password) &&
            /[@$!%*?&]/.test(password);

        if (passwordValid) {
            $("#passwordMsg").text("").css("color", "green");
        } else {
            $("#passwordMsg").text("Min 8 chars, uppercase, lowercase, number & special char").css("color", "red");
        }

        // Re-validate confirm password if it has a value
        const confirmPassword = $("#signup-confirm-password").val();
        if (confirmPassword) {
            if (password === confirmPassword) {
                $("#confirmPasswordMsg").text("Passwords match").css("color", "green");
                confirmPasswordValid = true;
            } else {
                $("#confirmPasswordMsg").text("Passwords do not match").css("color", "red");
                confirmPasswordValid = false;
            }
        }

        updateSubmitButton();
    });

    // Confirm Password validation
    $("#signup-confirm-password").on("keyup blur", function () {
        const confirmPassword = $(this).val();
        const password = $("#signup-password").val();

        if (confirmPassword === "") {
            $("#confirmPasswordMsg").text("");
            confirmPasswordValid = false;
        } else if (confirmPassword === password) {
            $("#confirmPasswordMsg").text("Passwords match").css("color", "green");
            confirmPasswordValid = true;
        } else {
            $("#confirmPasswordMsg").text("Passwords do not match").css("color", "red");
            confirmPasswordValid = false;
        }
        updateSubmitButton();
    });

    // Toggle password visibility
    $(".toggle-password").click(function () {
        const passwordInput = $(this).closest(".form-group").find("input");
        const icon = $(this);

        if (passwordInput.attr("type") === "password") {
            passwordInput.attr("type", "text");
            icon.removeClass("fa-eye").addClass("fa-eye-slash");
        } else {
            passwordInput.attr("type", "password");
            icon.removeClass("fa-eye-slash").addClass("fa-eye");
        }
    });
});