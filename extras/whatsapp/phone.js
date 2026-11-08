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
//  3. A typing box: when WhatsApp says the contact is typing (it only shows
//     "typing…" under their name), a boxed • • • appears in the chat as an
//     incoming message, like on the phone. It lives outside WhatsApp's own
//     markup, positioned over the chat, so it can't disturb the page.

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

// "typing…" / "recording audio…" under the name, in the languages WhatsApp
// most likely runs in here; add yours if the box never shows.
const TYPING = /typing|recording|schreibt|tippt|nimmt .* auf|escribiendo|grabando|écrit|enregistre|sta scrivendo|digitando|pisze/i;

// The scrolling element that holds the messages.
function messageScroller(main) {
  let el = main.querySelector('[data-testid="conversation-panel-messages"]');
  while (el && el !== main) {
    if (/(auto|scroll)/.test(getComputedStyle(el).overflowY) && el.scrollHeight > el.clientHeight) return el;
    el = el.parentElement;
  }
  return null;
}

function typingBox(main) {
  let box = document.getElementById("nc-typing");
  const header = main && main.querySelector('[data-testid="conversation-header"]');
  const title = header && header.querySelector('[data-testid="conversation-info-header-chat-title"]');
  const status = header && title ? header.querySelector('[data-testid="conversation-info-header"]') : null;
  const statusText = status ? status.innerText.replace(title.innerText, "") : "";
  const typing = Boolean(main) && document.body.classList.contains("nc-thread") && TYPING.test(statusText);
  const wasShown = document.body.classList.contains("nc-typing-on");
  document.body.classList.toggle("nc-typing-on", typing);
  if (!typing) {
    if (box) box.classList.remove("nc-show");
    return;
  }
  if (!box) {
    box = document.createElement("div");
    box.id = "nc-typing";
    box.innerHTML = "<i></i><i></i><i></i>";
    document.body.appendChild(box);
  }
  // Line up with the incoming messages, just above the reply line.
  const lastIn = [...main.querySelectorAll('.nc-in [data-testid="msg-container"]')].pop();
  const footer = main.querySelector("footer");
  const area = main.getBoundingClientRect();
  box.style.left = `${lastIn ? lastIn.getBoundingClientRect().left : area.left + 24}px`;
  box.style.top = `${(footer ? footer.getBoundingClientRect().top : area.bottom) - 56}px`;
  box.classList.add("nc-show");
  // phone.css adds room under the last message; keep the chat at the bottom.
  if (!wasShown) {
    const scroller = messageScroller(main);
    if (scroller && scroller.scrollHeight - scroller.scrollTop - scroller.clientHeight < 160) {
      requestAnimationFrame(() => { scroller.scrollTop = scroller.scrollHeight; });
    }
  }
}

function update() {
  const main = document.getElementById("main");
  document.body.classList.toggle("nc-thread", Boolean(main) && !listRequested);
  document.body.classList.toggle("nc-list", Boolean(main) && listRequested);
  typingBox(main);
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
  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true, characterData: true });
  window.addEventListener("resize", schedule);
  schedule();
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = start; // Ferdium calls it with (config, Ferdium)
  module.exports.update = update;
} else {
  start(); // browser extension content script
}
