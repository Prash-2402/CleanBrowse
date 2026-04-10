importScripts("extension-config.js");

const {
  BLOCKED_PAGE_FILENAME,
  LEET_CHARACTER_MAP,
  LOG_PREFIX,
  SAFE_URL_PREFIXES,
  URL_BLOCK_TERMS
} = globalThis.CLEAN_BROWSE_CONFIG;

function normalizeForMatching(value) {
  return value
    .toLowerCase()
    .split("")
    .map((character) => LEET_CHARACTER_MAP[character] || character)
    .join("")
    .replace(/[^a-z]/g, "")
    .replace(/([a-z])\1{2,}/g, "$1");
}

const BLOCKED_PAGE_URL = chrome.runtime.getURL(BLOCKED_PAGE_FILENAME);
const NORMALIZED_BLOCKED_TERMS = URL_BLOCK_TERMS
  .map(normalizeForMatching)
  .filter(Boolean);

function shouldBlockUrl(url) {
  if (!url) {
    return false;
  }

  const loweredUrl = url.toLowerCase();

  if (SAFE_URL_PREFIXES.some((prefix) => loweredUrl.startsWith(prefix))) {
    return false;
  }

  if (loweredUrl.startsWith(BLOCKED_PAGE_URL)) {
    return false;
  }

  const normalizedUrl = normalizeForMatching(url);

  return NORMALIZED_BLOCKED_TERMS.some((term) => normalizedUrl.includes(term));
}

function redirectToBlockedPage(tabId, url) {
  const blockedPageUrl = `${BLOCKED_PAGE_URL}?url=${encodeURIComponent(url)}`;

  chrome.tabs.update(tabId, { url: blockedPageUrl });
}

function handleNavigationCommit(details) {
  if (details.frameId !== 0) {
    return;
  }

  if (shouldBlockUrl(details.url)) {
    redirectToBlockedPage(details.tabId, details.url);
  }
}

chrome.runtime.onInstalled.addListener(() => {
  console.log(`${LOG_PREFIX} Background protection active.`);
});

chrome.webNavigation.onCommitted.addListener(handleNavigationCommit);
