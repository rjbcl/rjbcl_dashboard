function showPopup(type, message, redirectUrl = null) {
    const popup = document.getElementById("popup");
    const icon = document.getElementById("popupIcon");
    const title = document.getElementById("popupTitle");
    const msg = document.getElementById("popupMsg");
    const ok = document.getElementById("popupOk");

    // Set values
    msg.textContent = message;

    if (type === "success") {
        title.textContent = "Success";
        icon.innerHTML = `<i class="bi bi-check-circle-fill text-success popup-icon"></i>`;
        ok.style.background = "#00a45a";
    } else {
        title.textContent = "Error";
        icon.innerHTML = `<i class="bi bi-x-circle-fill text-danger popup-icon"></i>`;
        ok.style.background = "#dc3545";
    }

    // Show popup
    popup.style.display = "flex";

    ok.onclick = () => {
        popup.style.display = "none";
        if (redirectUrl) {
            window.location.href = redirectUrl;
        }
    };
}

// Auto-trigger popup from Django messages
document.addEventListener("DOMContentLoaded", () => {
    const msgs = document.querySelectorAll(".js-msg");

    if (!msgs || msgs.length === 0) return;

    msgs.forEach(m => {
        const type = m.dataset.tags.includes("success") ? "success" : "error";
        const message = m.dataset.text;
        const redirect = m.dataset.redirect || null;

        showPopup(type, message, redirect);
    });
});
