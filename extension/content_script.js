function isVisible(el) {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  const rect = el.getBoundingClientRect();
  return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
}

function isSensitiveInput(el) {
  const type = (el.getAttribute("type") || "").toLowerCase();
  const name = (el.getAttribute("name") || "").toLowerCase();
  const id = (el.getAttribute("id") || "").toLowerCase();
  const sensitiveHints = ["password", "token", "otp", "card", "cvv", "ssn"];
  if (type === "password") return true;
  return sensitiveHints.some((hint) => name.includes(hint) || id.includes(hint));
}

function collectContext() {
  const buttons = Array.from(document.querySelectorAll('button,[role="button"],input[type="button"],input[type="submit"]'))
    .filter(isVisible)
    .slice(0, 10)
    .map((el) => (el.innerText || el.value || el.getAttribute("aria-label") || "").trim())
    .filter(Boolean);

  const links = Array.from(document.querySelectorAll("a[href]"))
    .filter(isVisible)
    .slice(0, 10)
    .map((el) => ({
      text: (el.innerText || el.getAttribute("aria-label") || "").trim(),
      href: el.href
    }));

  const inputs = Array.from(document.querySelectorAll("input, textarea, select"))
    .filter(isVisible)
    .filter((el) => !isSensitiveInput(el))
    .slice(0, 10)
    .map((el) => ({
      type: el.getAttribute("type") || el.tagName.toLowerCase(),
      name: el.getAttribute("name") || "",
      placeholder: el.getAttribute("placeholder") || ""
    }));

  const summary = (document.body?.innerText || "").replace(/\s+/g, " ").trim().slice(0, 1000);

  return {
    url: window.location.href,
    title: document.title || "",
    buttons,
    links,
    inputs,
    summary
  };
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type !== "COLLECT_CONTEXT") return;
  sendResponse(collectContext());
});
