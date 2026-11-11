document.querySelectorAll('[data-support-send]').forEach(form => {
    form.addEventListener('submit', async event => {
        event.preventDefault();
        if (form.dataset.submitting) {
            return;
        }
        const button = form.querySelector('button[type="submit"]');
        const text = form.querySelector('textarea');
        const result = form.querySelector('[data-support-result]');
        form.dataset.submitting = 'true';
        button.disabled = true;
        text.readOnly = true;
        result.hidden = true;
        try {
            const response = await fetch(form.action, {
                method: 'POST', body: new FormData(form), credentials: 'same-origin',
            });
            if (response.ok && response.redirected) {
                window.location.assign(response.url);
                return;
            }
            const page = new DOMParser().parseFromString(await response.text(), 'text/html');
            const error = page.querySelector('[role="alert"]');
            result.textContent = error ? error.textContent : 'Сервер не подтвердил отправку. Проверьте авторизацию и повторите с тем же ID.';
            if (response.status >= 400 && response.status < 500) text.readOnly = false;
        } catch {
            result.textContent = 'Результат отправки неизвестен. Повторите: сохранены тот же текст и ID, дубликат не будет создан.';
        }
        result.hidden = false;
        delete form.dataset.submitting;
        button.disabled = false;
    });
});
