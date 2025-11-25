document.addEventListener("DOMContentLoaded", () => {
    
    // Prevent autofill poisoning
    const fakeInputs = document.querySelectorAll("input[style*='display:none']");
    fakeInputs.forEach(input => input.value = "");

    // Disable submit on click (avoid double submit)
    const form = document.querySelector("form");
    if (form) {
        form.addEventListener("submit", () => {
            const btn = form.querySelector(".btn-green");
            if (btn) {
                btn.disabled = true;
                btn.style.opacity = "0.7";
            }
        });
    }

});
