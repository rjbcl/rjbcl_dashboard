document.addEventListener("DOMContentLoaded", () => {
    // basic mobile sanitization
    const mobile = document.querySelector('input[name="mobile"]');
    if (mobile) {
        mobile.addEventListener("input", () => {
            mobile.value = mobile.value.replace(/[^\d+\-\s()]/g, "");
        });
    }

    // disable submit after first click
    const form = document.querySelector("form");
    if (form) {
        form.addEventListener("submit", () => {
            const btn = form.querySelector(".btn-green");
            if (btn) {
                btn.disabled = true;
                btn.style.opacity = "0.8";
            }
        });
    }
});
