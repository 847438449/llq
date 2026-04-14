const DEFAULT_API_URL = "http://localhost:8000/api/tasks/run";

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
});

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function collectCurrentPageContext() {
  const tab = await getActiveTab();
  if (!tab?.id) {
    throw new Error("No active tab found");
  }

  const response = await chrome.tabs.sendMessage(tab.id, { type: "COLLECT_CONTEXT" });
  return {
    url: tab.url || response?.url || "about:blank",
    title: tab.title || response?.title || "",
    buttons: response?.buttons || [],
    links: response?.links || [],
    inputs: response?.inputs || [],
    summary: response?.summary || ""
  };
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    try {
      if (message.type === "GET_CURRENT_TAB") {
        const tab = await getActiveTab();
        sendResponse({ ok: true, tab });
        return;
      }

      if (message.type === "RUN_TASK") {
        const pageContext = await collectCurrentPageContext();
        const apiUrl = message.apiUrl || DEFAULT_API_URL;
        const payload = {
          task: message.task,
          current_page: pageContext,
          debug: true
        };

        const result = await fetch(apiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        const data = await result.json();
        sendResponse({ ok: result.ok, data, payload });
      }
    } catch (error) {
      sendResponse({ ok: false, error: error.message || String(error) });
    }
  })();

  return true;
});
