function showResponseModal(status, message) {
    const modal = document.getElementById('responseModal');
    const modalContent = document.getElementById('modalContent');
    const modalMessage = document.getElementById('modalMessage');
    modal.classList.remove('success', 'failure');
    if (status === 'success') {
        modal.classList.add('success');
    } else {
        modal.classList.add('failure');
    }
    modalMessage.textContent = message;
    modal.style.display = 'block';
    setTimeout(() => closeResponseModal(), 10000);
}
function closeResponseModal() {
    const modal = document.getElementById('responseModal');
    modal.style.display = 'none';
}