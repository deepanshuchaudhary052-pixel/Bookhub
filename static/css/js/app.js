
document.addEventListener("DOMContentLoaded", function () {
    const menuToggle = document.getElementById("menuToggle");
    const sidebar = document.getElementById("sidebar");

    if (menuToggle && sidebar) {
        menuToggle.addEventListener("click", function () {
            sidebar.classList.toggle("open");
        });

        document.addEventListener("click", function (event) {
            if (
                window.innerWidth <= 760 &&
                sidebar.classList.contains("open") &&
                !sidebar.contains(event.target) &&
                !menuToggle.contains(event.target)
            ) {
                sidebar.classList.remove("open");
            }
        });
    }

    document.querySelectorAll(".alert").forEach(function (alertBox) {
        setTimeout(function () {
            alertBox.style.transition = "opacity 0.4s";
            alertBox.style.opacity = "0";

            setTimeout(function () {
                alertBox.remove();
            }, 400);
        }, 4000);
    });
});