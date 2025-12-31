// Reads Django messages and shows popup via popup.js
const msgNode = document.querySelector(".js-msg");

if (msgNode) {
    showPopup(msgNode.dataset.tags, msgNode.dataset.text);
}
