const BLOCKED_TERMS = [
  "porn",
  "pornographic",
  "explicit content",
  "xxx",
  "adult",
  "adult video",
  "adult site",
  "adult streaming",
  "adult subscription",
  "sex",
  "sexvideo",
  "sex tape",
  "sexvideo live",
  "sexvideo call",
  "sexvideo site",
  "sexvideo app",
  "sexvideo chat",
  "sexvideo room",
  "sexvideo live stream",
  "blowjob",
  "handjob",
  "gangbang",
  "threesome",
  "erotic video",
  "private video",
  "leaked video",
  "hidden cam",
  "nude",
  "nudity",
  "nsfw",
  "escort",
  "escort service",
  "call girl",
  "brothel",
  "paid sex",
  "sex service",
  "camgirl",
  "cam site",
  "webcamsex",
  "onlyfans",
  "strip",
  "striptease",
  "lap dance",
  "fetish",
  "bdsm",
  "domination",
  "submissive",
  "erotic",
  "seduction",
  "intimate",
  "lust",
  "pleasure",
  "hookup",
  "one night stand",
  "sugar daddy",
  "sugar baby",
  "making out",
  "foreplay",
  "climax",
  "orgasm",
  "penetration",
  "moaning",
  "arousal",
  "seducing",
  "dirty talk",
  "lewd",
  "thirst trap",
  "spicy content",
  "fanhouse",
  "fansly",
  "patreon adult",
  "private snaps",
  "premium snaps",
  "sexting",
  "dirty chat",
  "roleplay sex",
  "gambling",
  "casino",
  "casino app",
  "gambling site",
  "online casino",
  "crypto betting",
  "sportsbook",
  "bet",
  "betting",
  "betting app",
  "betting tips",
  "online betting",
  "betting odds",
  "odds",
  "wager",
  "wager money",
  "parlay",
  "spread betting",
  "live betting",
  "fantasy betting",
  "real money games",
  "cash games",
  "rummy cash",
  "teen patti cash",
  "lottery",
  "scratch cards",
  "poker",
  "blackjack",
  "roulette",
  "slots",
  "bingo",
  "jackpot",
  "jackpot win",
  "drugs",
  "drugs online",
  "buy drugs",
  "narcotics",
  "weed",
  "cocaine",
  "heroin",
  "mdma",
  "lsd",
  "ecstasy",
  "smoking",
  "vaping",
  "vape",
  "vape pen",
  "cigarettes",
  "hookah",
  "ecigarette",
  "alcohol",
  "alcohol drink",
  "beer",
  "liquor",
  "drunk",
  "vodka",
  "whiskey",
  "violence",
  "violent",
  "gore",
  "gore video",
  "murder",
  "murder video",
  "blood scene",
  "suicide methods",
  "suicide tips",
  "self harm",
  "cutting",
  "how to die",
  "kill someone",
  "violent video",
  "torture",
  "execution",
  "abuse",
  "kill",
  "killing",
  "boobs",
  "tits",
  "ass",
  "booty",
  "pussy",
  "dick",
  "penis",
  "vagina",
  "breasts",
  "nipples",
  "genital",
  "cleavage",
  "pr0n",
  "p0rn",
  "s3x",
  "fxck",
  "fuk",
  "fck",
  "seggs",
  "sx",
  "pron",
  "po rn",
  "p orn",
  "fuck"
];

const LEET_CHARACTER_MAP = {
  "0": "o",
  "1": "i",
  "3": "e",
  "4": "a",
  "5": "s",
  "7": "t",
  "@": "a",
  "$": "s",
  "!": "i"
};

const SAFE_URL_PREFIXES = [
  "chrome://",
  "edge://",
  "about:",
  "devtools://",
  "chrome-extension://",
  "moz-extension://"
];

function normalizeForMatching(value) {
  return value
    .toLowerCase()
    .split("")
    .map((character) => LEET_CHARACTER_MAP[character] || character)
    .join("")
    .replace(/[^a-z]/g, "")
    .replace(/([a-z])\1{2,}/g, "$1");
}

const NORMALIZED_BLOCKED_TERMS = BLOCKED_TERMS.map(normalizeForMatching).filter(Boolean);

function isBlockedUrl(url) {
  if (!url) {
    return false;
  }

  const loweredUrl = url.toLowerCase();

  if (SAFE_URL_PREFIXES.some((prefix) => loweredUrl.startsWith(prefix))) {
    return false;
  }

  if (loweredUrl.startsWith(chrome.runtime.getURL("blocked.html"))) {
    return false;
  }

  const normalizedUrl = normalizeForMatching(url);

  return NORMALIZED_BLOCKED_TERMS.some((term) => normalizedUrl.includes(term));
}

function redirectToBlockedPage(tabId, url) {
  const blockedPageUrl =
    `${chrome.runtime.getURL("blocked.html")}?url=${encodeURIComponent(url)}`;

  chrome.tabs.update(tabId, { url: blockedPageUrl });
}

function handleNavigation(details) {
  if (details.frameId !== 0) {
    return;
  }

  if (isBlockedUrl(details.url)) {
    redirectToBlockedPage(details.tabId, details.url);
  }
}

chrome.runtime.onInstalled.addListener(() => {
  console.log("Extension Active");
});

chrome.webNavigation.onCommitted.addListener(handleNavigation);
