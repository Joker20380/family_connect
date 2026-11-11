document.querySelectorAll('[data-support-send]').forEach(form => {
    form.addEventListener('submit', event => {
        if (form.dataset.submitting) {
            event.preventDefault();
            return;
        }
        form.dataset.submitting = 'true';
        form.querySelector('button[type="submit"]').disabled = true;
    });
});
