document.querySelector('#hub-feedback')?.addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget, status = document.querySelector('#feedback-status'), button = form.querySelector('button');
  button.disabled = true;
  status.textContent = 'Sending privately…';
  try {
    const response = await fetch('/api/feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(Object.fromEntries(new FormData(form))), signal: AbortSignal.timeout(15000) });
    if (!response.ok || !response.headers.get('Content-Type')?.includes('application/json') || (await response.json()).ok !== true) throw new Error();
    status.textContent = 'Feedback sent. Thank you!'; form.reset();
  } catch { status.textContent = 'Feedback could not be sent. Please use the email link below; your message is still here.'; }
  finally { button.disabled = false; }
});
