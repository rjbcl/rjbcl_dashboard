document.addEventListener("DOMContentLoaded", function () {
    const select = document.getElementById("occupation");

    if (!select) return;

    fetch("/static/kycform/json/occupations.json")
        .then(res => res.json())
        .then(data => {
            data.occupations.forEach(item => {
                select.innerHTML += `
                    <option value="${item.name}">${item.name}</option>
                `;
            });
        })
        .catch(err => console.error("Occupation Load Error:", err));
});
