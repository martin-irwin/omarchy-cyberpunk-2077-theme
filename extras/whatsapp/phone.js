// Night City phone layer for WhatsApp. Runs as the Ferdium service's user.js,
// or as the content script of the Cyberphone extension (extras/bin/cyberphone).
// It does two things phone.css can't do alone:
//
//  1. Marks each message row as yours (nc-out) or incoming (nc-in). WhatsApp's
//     class names are generated and don't say, so it goes by where the bubble
//     sits: bubbles centred right of the middle of the chat are yours.
//  2. Thread mode, like opening a conversation on V's phone: picking a contact
//     hides the contact list and WhatsApp's icon column so the chat fills the
//     window. "◀ CONTACTS" in the chat header (or Esc, which closes the chat)
//     brings back the contact list, full width, the way the phone does.

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

// Mark the layout around #main. Ancestors of #main (nc-chain) get their
// minimum widths lifted, since WhatsApp's layout is wider than a half-screen
// window. On the way up, the column holding #main is nc-maincol, and any
// sibling column holding the contact list or the icon column is nc-col
// (nc-col-side / nc-col-nav). Only those, so pop-ups and drawers mounted
// elsewhere are never touched.
function markLayout(main) {
  for (const cls of ["nc-chain", "nc-col", "nc-col-side", "nc-col-nav", "nc-maincol"]) {
    for (const el of document.querySelectorAll("." + cls)) el.classList.remove(cls);
  }
  const app = document.getElementById("app");
  for (let node = main; node && node !== app && node.parentElement; node = node.parentElement) {
    node.classList.add("nc-chain");
    for (const sib of node.parentElement.children) {
      if (sib === node) continue;
      const side = sib.id === "side" || sib.querySelector("#side");
      const nav = sib.querySelector("[data-testid='navbar-primary-section']");
      if (side || nav) {
        sib.classList.add("nc-col", side ? "nc-col-side" : "nc-col-nav");
        node.classList.add("nc-maincol");
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
  document.body.classList.toggle("nc-list", Boolean(main) && listRequested);
  if (!main) return;
  tagRows(main);
  markLayout(main);
  addBackButton(main);
}

function start() {
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
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = start; // Ferdium calls it with (config, Ferdium)
  module.exports.update = update;
} else {
  start(); // browser extension content script
}
