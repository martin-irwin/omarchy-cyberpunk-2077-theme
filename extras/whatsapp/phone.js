// Night City phone layer for WhatsApp in Ferdium (loaded as the service's
// user.js). It does two things phone.css can't do alone:
//
//  1. Marks each message row as yours (nc-out) or incoming (nc-in). WhatsApp's
//     class names are generated and don't say, so it goes by where the bubble
//     sits: bubbles centred right of the middle of the chat are yours.
//  2. Thread mode, like opening a conversation on V's phone: picking a contact
//     hides the contact list and WhatsApp's icon column so the chat fills the
//     window. "◀ CONTACTS" in the chat header (or Esc, which closes the chat)
//     brings the list back.

let listRequested = false; // true after "◀ CONTACTS", until a contact is picked

function tagRows(main) {
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

// The layout columns to hide in thread mode: on the way up from #main, any
// sibling that holds the contact list or the icon column. Only those, so
// pop-ups and side drawers mounted elsewhere are never touched.
function markColumns(main) {
  for (const el of document.querySelectorAll(".nc-col")) el.classList.remove("nc-col");
  const app = document.getElementById("app");
  for (let node = main; node && node !== app && node.parentElement; node = node.parentElement) {
    for (const sib of node.parentElement.children) {
      if (sib === node) continue;
      if (sib.querySelector("#side, [data-testid='navbar-primary-section']") || sib.id === "side") {
        sib.classList.add("nc-col");
      }
    }
  }
}

function addBackButton(main) {
  const header = main.querySelector('[data-testid="conversation-header"]');
  if (!header || header.querySelector(".nc-back")) return;
  const back = document.createElement("button");
  back.className = "nc-back";
  back.type = "button";
  back.textContent = "◀ CONTACTS";
  back.addEventListener("click", event => {
    event.stopPropagation();
    listRequested = true;
    update();
  });
  header.prepend(back);
}

function update() {
  const main = document.getElementById("main");
  document.body.classList.toggle("nc-thread", Boolean(main) && !listRequested);
  if (!main) return;
  tagRows(main);
  markColumns(main);
  addBackButton(main);
}

module.exports = () => {
  let queued = false;
  const schedule = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      update();
    });
  };
  // Picking a contact (in the list or search results) opens thread mode again.
  document.addEventListener("click", event => {
    if (event.target.closest && event.target.closest("#pane-side, #side [role='row'], #side [role='listitem']")) {
      listRequested = false;
      schedule();
    }
  }, true);
  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener("resize", schedule);
  schedule();
};

module.exports.update = update;
