importScripts("extension-config.js");

const {
  BLOCKED_PAGE_FILENAME,
  LEET_CHARACTER_MAP,
  LOG_PREFIX,
  SAFE_URL_PREFIXES,
  URL_BLOCK_CATEGORIES
} = globalThis.CLEAN_BROWSE_CONFIG;

const STRICT_MATCH_TERMS = new Set([
  "sex", "ass", "dick", "kill", "weed", "bet", "odds", "cock", 
  "tits", "gore", "beer", "drunk", "lust", "strip", "escort", 
  "nude", "drugs", "xxx", "nsfw","kiss"
]);

const BLOCKED_PAGE_URL = chrome.runtime.getURL(BLOCKED_PAGE_FILENAME);

function shouldBlockUrl(url) {
  if (!url) {
    return { blocked: false, reason: "" };
  }

  const loweredUrl = url.toLowerCase();

  if (SAFE_URL_PREFIXES.some((prefix) => loweredUrl.startsWith(prefix))) {
    return { blocked: false, reason: "" };
  }

  if (loweredUrl.startsWith(BLOCKED_PAGE_URL)) {
    return { blocked: false, reason: "" };
  }

  // Preserve symbols but un-leet the URL
  const leetUrl = loweredUrl
    .split("")
    .map((character) => LEET_CHARACTER_MAP[character] || character)
    .join("");

  const alphanumericUrl = leetUrl.replace(/[^a-z0-9]/g, "");

  for (const [category, terms] of Object.entries(URL_BLOCK_CATEGORIES)) {
    for (const term of terms) {
      const normalizedTerm = term
        .toLowerCase()
        .split("")
        .map((character) => LEET_CHARACTER_MAP[character] || character)
        .join("");

      let isMatch = false;

      if (STRICT_MATCH_TERMS.has(term)) {
        // Must not be immediately surrounded by other letters/numbers (word boundary)
        const regex = new RegExp(`(^|[^a-z0-9])${normalizedTerm}([^a-z0-9]|$)`, "i");
        isMatch = regex.test(leetUrl);
      } else {
        // For longer, highly specific terms, aggressive substring matching is fine
        const noSpaceTerm = normalizedTerm.replace(/ /g, "");
        isMatch = alphanumericUrl.includes(noSpaceTerm);
      }

      if (isMatch) {
         return { blocked: true, reason: category };
      }
    }
  }

  return { blocked: false, reason: "" };
}

function redirectToBlockedPage(tabId, url, reason) {
  const blockedPageUrl = `${BLOCKED_PAGE_URL}?url=${encodeURIComponent(url)}&reason=${encodeURIComponent(reason)}`;

  chrome.tabs.update(tabId, { url: blockedPageUrl });
}

function reportEvent(eventType, url, snippet = "", severity = "medium") {
  fetch(`${globalThis.CLEAN_BROWSE_CONFIG.LOCAL_API_BASE_URL}${globalThis.CLEAN_BROWSE_CONFIG.REPORT_EVENT_ROUTE}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      event_type: eventType,
      url: url,
      snippet: snippet,
      severity: severity
    })
  }).catch((error) => console.error(`${LOG_PREFIX} Failed to report event:`, error));
}


function handleNavigationCommit(details) {
  if (details.frameId !== 0) {
    return;
  }

  const result = shouldBlockUrl(details.url);
  if (result.blocked) {
    redirectToBlockedPage(details.tabId, details.url, result.reason);
    reportEvent(`blocked_site`, details.url, result.reason, "high");
  }
}

chrome.runtime.onInstalled.addListener(() => {
  console.log(`${LOG_PREFIX} Background protection active.`);
});

// Shifted from onCommitted to onBeforeNavigate to intercept instantly (Pre-Load Blocking)
chrome.webNavigation.onBeforeNavigate.addListener(handleNavigationCommit);

// Proxy for Content script to talk to the local AI Server (Bypasses CORS restrictions)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "analyzeText") {
    fetch(`${globalThis.CLEAN_BROWSE_CONFIG.LOCAL_API_BASE_URL}${globalThis.CLEAN_BROWSE_CONFIG.ANALYZE_TEXT_ROUTE}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ text: request.text })
    })
      .then((response) => response.json())
      .then((data) => {
        sendResponse(data);
      })
      .catch((error) => {
        console.error(`${LOG_PREFIX} AI server unreachable -`, error);
        sendResponse({ error: "AI Server unreachable", label: "safe" });
      });
      
    // Return true ensures the message channel stays open for the async fetch response
    return true; 
  } else if (request.action === "reportEvent") {
    reportEvent(
       request.eventType, 
       sender.tab ? sender.tab.url : "unknown", 
       request.snippet, 
       request.severity
    );
  }
});
