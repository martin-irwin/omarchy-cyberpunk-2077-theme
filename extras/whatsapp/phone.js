// Night City phone layer for WhatsApp in Ferdium (loaded as the service's
// user.js). WhatsApp's class names are generated and don't say which side a
// message is on, so this marks each message row from where it sits: rows
// whose bubble ends at the right edge of the chat are yours (nc-out), the
// rest are incoming (nc-in). phone.css styles the two.

function tagRows() {
  const main = document.getElementById("main");
  if (!main) return;
  const mid = main.getBoundingClientRect().left + main.clientWidth / 2;
  for (const bubble of main.querySelectorAll('[data-testid="msg-container"]')) {
    const row = bubble.closest('[role="row"]');
    if (!row) continue;
    const box = bubble.getBoundingClientRect();
    if (!box.width) continue;
    const out = box.left + box.width / 2 > mid;
    row.classList.toggle("nc-out", out);
    row.classList.toggle("nc-in", !out);
  }
}

module.exports = () => {
  let queued = false;
  const schedule = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      tagRows();
    });
  };
  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener("resize", schedule);
  schedule();
};

// Exposed for live testing from DevTools.
module.exports.tagRows = tagRows;
