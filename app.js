const $ = (selector) => document.querySelector(selector);
const form = $('#checkin-form');
const symptoms = $('#symptoms');
const duration = $('#duration');
const checkinResult = $('#checkin-result');
const answerCard = $('#answer');
const notes = { value: '' };
const copyButton = $('#copy-notes');
const today = new Intl.DateTimeFormat(undefined, { weekday: 'short', month: 'short', day: 'numeric' }).format(new Date());
$('#today-label').textContent = today;

async function askGuide(payload) {
  const response = await fetch('/api/guide', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload) });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Something went wrong. Please try again.');
  return data;
}
function toast(message) {
  const node = $('#toast');
  node.textContent = message;
  node.classList.add('show');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => node.classList.remove('show'), 2800);
}
function setBusy(button, busy, label) {
  if (busy) { button.dataset.original = button.innerHTML; button.disabled = true; button.textContent = label; }
  else { button.disabled = false; button.innerHTML = button.dataset.original || button.innerHTML; }
}

symptoms.addEventListener('input', () => { $('#char-count').textContent = `${symptoms.value.length.toLocaleString()} / 2,000`; });
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const note = symptoms.value.trim();
  const selectedSymptoms = [...form.querySelectorAll('input[name="symptom"]:checked')].map((input) => input.value);
  if (!note && !selectedSymptoms.length) { toast('Select a symptom or add a short note first.'); return; }
  const summaryInput = [selectedSymptoms.length ? `Symptoms selected: ${selectedSymptoms.join(', ')}` : '', note ? `Additional notes: ${note}` : ''].filter(Boolean).join('\n');
  const button = form.querySelector('button[type="submit"]');
  setBusy(button, true, 'Preparing your notes…');
  checkinResult.classList.remove('hidden');
  checkinResult.textContent = 'Putting your thoughts into a simple visit summary…';
  try {
    const result = await askGuide({ details: `${summaryInput}${duration.value ? `\nHow long: ${duration.value}` : ''}`, language: $('#response-language').value, message: 'Help me make a brief, neutral summary I can share with a clinician. Include only the symptoms and duration I gave you, then suggest up to three useful details or questions to bring to a visit. Do not infer a diagnosis or invent missing facts.' });
    notes.value = `My care notes\n${today}\n\n${summaryInput}${duration.value ? `\nHow long: ${duration.value}` : ''}\n\nPreparation: ${result.answer}`;
    checkinResult.innerHTML = '<h4>Your starting point</h4>';
    const intro = document.createElement('p'); intro.textContent = `${summaryInput}${duration.value ? ` · ${duration.value}` : ''}`; checkinResult.append(intro);
    const summary = document.createElement('p'); summary.textContent = result.answer; checkinResult.append(summary);
    copyButton.disabled = false;
    toast('Your care notes are ready.');
  } catch (error) {
    checkinResult.textContent = error.message;
  } finally { setBusy(button, false); }
});

const question = $('#question');
$('#ask-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = question.value.trim();
  if (!message) { question.focus(); return; }
  const button = event.currentTarget.querySelector('button[type="submit"]');
  setBusy(button, true, '…');
  answerCard.classList.remove('hidden');
  answerCard.textContent = 'Taking a moment to think…';
  try {
    const result = await askGuide({ message, language: $('#response-language').value });
    answerCard.textContent = result.answer;
    if (result.urgent) answerCard.style.cssText = 'background:#fff4ee;border-color:#d27e59;color:#754a39';
    question.value = '';
  } catch (error) { answerCard.textContent = error.message; }
  finally { setBusy(button, false); button.setAttribute('aria-label', 'Send question'); }
});
document.querySelectorAll('.suggestion').forEach((chip) => chip.addEventListener('click', () => {
  question.value = chip.dataset.question;
  question.focus();
  question.closest('.ask-panel').scrollIntoView({ behavior: 'smooth', block: 'center' });
}));
copyButton.addEventListener('click', async () => {
  if (!notes.value) return;
  try { await navigator.clipboard.writeText(notes.value); toast('Care notes copied to clipboard.'); }
  catch { toast('Clipboard access is unavailable in this browser.'); }
});

const dialog = $('#urgent');
$('#urgent-link').addEventListener('click', (event) => { event.preventDefault(); dialog.showModal(); });
$('.dialog-close').addEventListener('click', () => dialog.close());
$('.dialog-done').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });

fetch('/api/health').then((res) => res.json()).then((data) => {
  $('#connection-label').textContent = data.configured ? `${data.model} · connected` : 'Add Nebius API key to connect';
}).catch(() => { $('#connection-label').textContent = 'Model connection unavailable'; });
