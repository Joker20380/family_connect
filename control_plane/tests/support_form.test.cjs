const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../static/console/support.js'), 'utf8');

function fixture(fetch) {
    const button = {disabled: false};
    const text = {value: 'synthetic message', readOnly: false};
    const result = {hidden: true, textContent: ''};
    const redirects = [];
    const form = {
        dataset: {}, action: '/inventory/canonical/messages/send/', token: 'same-signed-id',
        querySelector: selector => ({'button[type="submit"]': button, textarea: text,
            '[data-support-result]': result})[selector],
        addEventListener: (name, handler) => { form.submit = handler; },
    };
    vm.runInNewContext(source, {
        document: {querySelectorAll: () => [form]}, fetch,
        FormData: class { constructor(value) { this.token = value.token; this.text = text.value; } },
        DOMParser: class { parseFromString(body) { return {querySelector: () => ({textContent: body})}; } },
        window: {location: {assign: url => redirects.push(url)}},
    });
    return {form, button, text, result, redirects};
}

test('double click is suppressed and a lost reply retains the same ID and text', async () => {
    const requests = [];
    let rejectFirst;
    const view = fixture((url, options) => {
        requests.push({url, token: options.body.token, text: options.body.text, method: options.method});
        return requests.length === 1 ? new Promise((resolve, reject) => { rejectFirst = reject; })
            : Promise.resolve({ok: true, redirected: true, url: '/inventory/canonical/messages/'});
    });
    let prevented = 0;
    const event = {preventDefault: () => { prevented += 1; }};
    const first = view.form.submit(event);
    await view.form.submit(event);
    assert.equal(requests.length, 1);
    assert.equal(view.button.disabled, true);
    rejectFirst(new TypeError('Network reply lost'));
    await first;
    assert.equal(view.button.disabled, false);
    assert.equal(view.text.readOnly, true);
    assert.equal(view.result.hidden, false);
    assert.match(view.result.textContent, /тот же текст и ID/);
    await view.form.submit(event);
    assert.deepEqual(requests[0], requests[1]);
    assert.equal(prevented, 3);
    assert.deepEqual(view.redirects, ['/inventory/canonical/messages/']);
});

test('a definite validation refusal shows text safely and permits correction', async () => {
    const view = fixture(async () => ({ok: false, status: 400, redirected: false,
        text: async () => '<synthetic validation error>'}));
    await view.form.submit({preventDefault() {}});
    assert.equal(view.result.textContent, '<synthetic validation error>');
    assert.equal(view.text.readOnly, false);
    assert.equal(view.button.disabled, false);
    assert.deepEqual(view.redirects, []);
});
