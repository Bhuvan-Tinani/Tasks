function openProfile() { document.getElementById("profileModal").style.display = "block"; }
function closeProfile() { document.getElementById("profileModal").style.display = "none"; }
window.onclick = function (event) {
    const modal = document.getElementById("profileModal");
    if (event.target === modal) { modal.style.display = "none"; }
};