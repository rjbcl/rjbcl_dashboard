// Selectors
const tabPolicy = document.getElementById("tabPolicy");
const tabAgent = document.getElementById("tabAgent");

const policyForm = document.getElementById("policyForm");
const agentForm = document.getElementById("agentForm");

// TAB SWITCH LOGIC
tabPolicy.onclick = () => {
    tabPolicy.classList.add("active");
    tabAgent.classList.remove("active");
    policyForm.style.display = "block";
    agentForm.style.display = "none";
};

tabAgent.onclick = () => {
    tabAgent.classList.add("active");
    tabPolicy.classList.remove("active");
    agentForm.style.display = "block";
    policyForm.style.display = "none";
};

// AUTO-SELECT TAB FROM BACKEND
if (window.activeTab === "agent") {
    tabAgent.click();
}

// POPUP LOGIC
const popup = document.getElementById("popup");
const popupIcon = document.getElementById("popupIcon");
const popupTitle = document.getElementById("popupTitle");
const popupMsg = document.getElementById("popupMsg");
const popupOk = document.getElementById("popupOk");

const m = document.querySelector(".js-msg");
if (m) {
    popup.style.display = "flex";
    popupMsg.textContent = m.dataset.text;

    if (m.dataset.tags.includes("success")) {
        popupTitle.textContent = "Success";
        popupIcon.innerHTML = `<i class="bi bi-check-circle-fill" style="font-size:32px;color:#16a34a"></i>`;
        popupOk.onclick = () => window.location.reload();
    } else {
        popupTitle.textContent = "Error";
        popupIcon.innerHTML = `<i class="bi bi-x-circle-fill" style="font-size:32px;color:#dc3545"></i>`;
        popupOk.onclick = () => (popup.style.display = "none");
    }
}
