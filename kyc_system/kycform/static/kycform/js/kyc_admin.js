console.log("KYC Admin JS Loaded!");

document.addEventListener("DOMContentLoaded", function () {
    const status = document.querySelector("#id_kyc_status");
    const lock = document.querySelector("#id_is_lock");

    if (!status || !lock) return;

    function updateLockField() {
        if (status.value === "VERIFIED") {
            lock.disabled = false;
        } else {
            lock.checked = false;
            lock.disabled = true;
        }
    }

    // initial load
    updateLockField();

    // when admin changes dropdown
    status.addEventListener("change", updateLockField);
});
