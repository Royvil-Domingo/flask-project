document.addEventListener('DOMContentLoaded', () => {
    const today = new Date().toISOString().split('T')[0];
    const dueInput = document.getElementById('due_on');
    if (dueInput) {
        dueInput.setAttribute('min', today);
    }

    setTimeout(() => {
        document.querySelectorAll('.alert').forEach((alert) => {
            alert.classList.remove('show');
        });
    }, 5000);
});