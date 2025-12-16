console.log("KYC Admin JS Loaded!");

document.addEventListener("DOMContentLoaded", function () {
    const status = document.querySelector("#id_kyc_status");
    const lock = document.querySelector("#id_is_lock");

    const row = document.querySelector(".field-rejection_comment_input");

    function ensureTextarea() {
        const input = document.querySelector("#id_rejection_comment_input");

        // If Django rendered <input type="hidden">, replace it with a textarea
        if (input && input.tagName === "INPUT") {
            const textarea = document.createElement("textarea");
            textarea.id = input.id;
            textarea.name = input.name;
            textarea.rows = 3;
            textarea.placeholder = "Provide rejection reason…";
            textarea.value = input.value;

            input.replaceWith(textarea);
        }
    }

    function updateRejectionCommentVisibility() {
        ensureTextarea();

        if (!row) return;
        if (status.value === "REJECTED") {
            row.classList.remove("hidden");
        } else {
            row.classList.add("hidden");
        }
    }

    function updateLockField() {
        if (!lock) return;
        if (status.value === "VERIFIED") {
            lock.disabled = false;
        } else {
            lock.checked = false;
            lock.disabled = true;
        }
    }

    // Initial
    updateLockField();
    updateRejectionCommentVisibility();

    // On change
    status.addEventListener("change", function () {
        updateLockField();
        updateRejectionCommentVisibility();
    });
});
