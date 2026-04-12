importScripts("extension-config.js");

const {
  BLOCKED_PAGE_FILENAME,
  LEET_CHARACTER_MAP,
  LOG_PREFIX,
  SAFE_URL_PREFIXES,
  URL_BLOCK_CATEGORIES,
  SAFETY_MODES,
  DEFAULT_MODE_ID
} = globalThis.CLEAN_BROWSE_CONFIG;

let activeThreshold = SAFETY_MODES[DEFAULT_MODE_ID].threshold;
const IMAGE_RESULTS_CACHE = new Map();

// Load initial settings and listen for changes
extAPI.storage.local.get("activeModeId", (data) => {
  if (data.activeModeId && SAFETY_MODES[data.activeModeId]) {
    activeThreshold = SAFETY_MODES[data.activeModeId].threshold;
  }
});

extAPI.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && changes.activeModeId) {
    const newModeId = changes.activeModeId.newValue;
    if (SAFETY_MODES[newModeId]) {
      activeThreshold = SAFETY_MODES[newModeId].threshold;
      console.log(`${LOG_PREFIX} Switched to ${SAFETY_MODES[newModeId].label} mode (Threshold: ${activeThreshold})`);
    }
  }
});

const STRICT_MATCH_TERMS = new Set([
  "sex", "ass", "dick", "kill", "weed", "bet", "odds", "cock", 
  "tits", "gore", "beer", "drunk", "lust", "strip", "escort", 
  "nude", "drugs", "xxx", "nsfw","kiss"
]);

const BLOCKED_PAGE_URL = extAPI.runtime.getURL(BLOCKED_PAGE_FILENAME);

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

function shouldBlockSearch(query) {
  if (!query) {
    return { blocked: false, reason: "" };
  }

  const loweredQuery = query.toLowerCase();

  for (const [category, terms] of Object.entries(URL_BLOCK_CATEGORIES)) {
    for (const term of terms) {
      const lowerTerm = term.toLowerCase();
      if (STRICT_MATCH_TERMS.has(term)) {
        const regex = new RegExp(`(^|[^a-z0-9])${lowerTerm}([^a-z0-9]|$)`, "i");
        if (regex.test(loweredQuery)) {
          return { blocked: true, reason: category };
        }
      } else {
        if (loweredQuery.includes(lowerTerm)) {
          return { blocked: true, reason: category };
        }
      }
    }
  }

  return { blocked: false, reason: "" };
}

function redirectToBlockedPage(tabId, url, reason, score = null) {
  let blockedPageUrl = `${BLOCKED_PAGE_URL}?url=${encodeURIComponent(url)}&reason=${encodeURIComponent(reason)}`;
  
  if (score !== null) {
    blockedPageUrl += `&score=${encodeURIComponent(score)}`;
  }

  extAPI.tabs.update(tabId, { url: blockedPageUrl });
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

function reportHeartbeat() {
  fetch(`${globalThis.CLEAN_BROWSE_CONFIG.LOCAL_API_BASE_URL}${globalThis.CLEAN_BROWSE_CONFIG.HEARTBEAT_ROUTE}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ 
      timestamp: Date.now(),
      activeMode: activeMode // Reports current safety mode (Kid/Teen)
    })
  }).catch(() => {
    // Fail silently, likely server or extension off
  });
}

// Start heartbeat!
setInterval(reportHeartbeat, globalThis.CLEAN_BROWSE_CONFIG.HEARTBEAT_INTERVAL);
// Initial ping
reportHeartbeat();

function checkUrlForUnsafeSearch(url, tabId, frameId = 0) {
  if (frameId !== 0 || !url) {
    return false;
  }

  try {
    const urlObj = new URL(url);
    const isGoogleSearch = urlObj.hostname.includes("google.") && urlObj.pathname.startsWith("/search");
    const isYouTubeSearch = urlObj.hostname.includes("youtube.com") && urlObj.pathname.startsWith("/results");

    if (isGoogleSearch || isYouTubeSearch) {
      // YouTube uses 'search_query' on desktop and 'q' or 'search_query' on mobile/app-like views
      const query = isGoogleSearch 
        ? urlObj.searchParams.get("q") 
        : (urlObj.searchParams.get("search_query") || urlObj.searchParams.get("q"));

      if (query) {
        const searchCheck = shouldBlockSearch(query);
        if (searchCheck.blocked) {
          redirectToBlockedPage(tabId, url, searchCheck.reason);
          reportEvent("unsafe_search", url, query, "high");
          return true;
        }

        // Safe search enforcement for Google
        if (isGoogleSearch && urlObj.searchParams.get("safe") !== "active") {
          urlObj.searchParams.set("safe", "active");
          extAPI.tabs.update(tabId, { url: urlObj.toString() });
          return true;
        }
      }
    }
  } catch (error) {
    console.error(`${LOG_PREFIX} URL Parse error during navigation interception:`, error);
  }

  const result = shouldBlockUrl(url);
  if (result.blocked) {
    redirectToBlockedPage(tabId, url, result.reason);
    reportEvent(`blocked_site`, url, result.reason, "high");
    return true;
  }

  return false;
}

function handleNavigationCommit(details) {
  checkUrlForUnsafeSearch(details.url, details.tabId, details.frameId);
}

extAPI.runtime.onInstalled.addListener(() => {
  console.log(`${LOG_PREFIX} Background protection active.`);
  
  // Set Uninstall URL to report extension disable/uninstall
  const uninstallUrl = `${globalThis.CLEAN_BROWSE_CONFIG.LOCAL_API_BASE_URL}${globalThis.CLEAN_BROWSE_CONFIG.REPORT_UNINSTALL_ROUTE}`;
  if (extAPI.runtime.setUninstallURL) {
    extAPI.runtime.setUninstallURL(uninstallUrl);
  }

  // Check if Incognito access is allowed
  if (extAPI.extension && extAPI.extension.isAllowedIncognitoAccess) {
    extAPI.extension.isAllowedIncognitoAccess((isAllowed) => {
      if (!isAllowed) {
        reportEvent("bypass_attempt", "Incognito Protection Missing", "Parent has not enabled incognito access for CleanBrowse in Chrome extensions settings.", "high");
      }
    });
  }
});

// Reinforce interception by listening to History state changes (SPA apps like YouTube/Google)
if (extAPI.webNavigation) {
  if (extAPI.webNavigation.onBeforeNavigate) {
    extAPI.webNavigation.onBeforeNavigate.addListener(handleNavigationCommit);
  }
  if (extAPI.webNavigation.onHistoryStateUpdated) {
    extAPI.webNavigation.onHistoryStateUpdated.addListener(handleNavigationCommit);
  }
}

// Proxy for Content script to talk to the local AI Server (Bypasses CORS restrictions)
extAPI.runtime.onMessage.addListener((request, sender, sendResponse) => {
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
        // Dynamic Threshold Intervention:
        // We ignore the backend's "label" and apply our own based on parent-selected mode
        const score = data.toxicity_score || 0;
        const isUnsafe = score >= activeThreshold;
        
        sendResponse({ 
          ...data, 
          label: isUnsafe ? "unsafe" : "safe",
          activeThreshold: activeThreshold
        });
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
  } else if (request.action === "analyzeImage") {
    const imageUrl = request.imageUrl;
    const altText = request.altText || "";
    const title = request.title || "";

    if (IMAGE_RESULTS_CACHE.has(imageUrl)) {
      sendResponse(IMAGE_RESULTS_CACHE.get(imageUrl));
      return;
    }

    fetch(`${globalThis.CLEAN_BROWSE_CONFIG.LOCAL_API_BASE_URL}${globalThis.CLEAN_BROWSE_CONFIG.ANALYZE_IMAGE_ROUTE}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ 
        image_url: imageUrl,
        alt_text: altText,
        title: title
      })
    })
      .then((response) => response.json())
      .then((data) => {
        // Apply safety threshold logic for images as well if score is provided
        const score = data.score !== undefined ? data.score : (data.label === "unsafe" ? 1.0 : 0.0);
        const isUnsafe = score >= activeThreshold;
        
        const finalResult = { 
          ...data, 
          label: isUnsafe ? "unsafe" : "safe",
          score: score
        };
        
        IMAGE_RESULTS_CACHE.set(imageUrl, finalResult);
        sendResponse(finalResult);
      })
      .catch((error) => {
        console.error(`${LOG_PREFIX} AI server unreachable for image analysis -`, error);
        sendResponse({ error: "AI Server unreachable", label: "safe" });
      });

    return true; // Keep channel open
  }
});
