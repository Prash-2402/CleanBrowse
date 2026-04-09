console.log("Extension Active");

const UNSAFE_TERMS = [
  "sex",
  "sexvideo",
  "pornographic",
  "explicit content",
  "adult video",
  "adult site",
  "adult streaming",
  "adult subscription",
  "erotic video",
  "sex tape",
  "leaked video",
  "private video",
  "hidden cam",
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
  "testes",
  "nude",
  "nudity",
  "porn",
  "xxx",
  "nsfw",
  "escort",
  "escort service",
  "call girl",
  "brothel",
  "massage parlor",
  "paid sex",
  "sex service",
  "fetish",
  "bdsm",
  "domination",
  "submissive",
  "erotic",
  "seduction",
  "making out",
  "foreplay",
  "climax",
  "orgasm",
  "penetration",
  "moaning",
  "arousal",
  "seducing",
  "striptease",
  "lap dance",
  "dirty talk",
  "intimate",
  "lust",
  "pleasure",
  "hookup",
  "one night stand",
  "sugar daddy",
  "sugar baby",
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
  "violence",
  "violent",
  "gore",
  "gore video",
  "bloodshed",
  "blood scene",
  "abuse",
  "murder",
  "murder video",
  "kill",
  "killing",
  "suicide methods",
  "suicide tips",
  "self harm",
  "cutting",
  "how to die",
  "kill someone",
  "violent video",
  "torture",
  "execution",
  "gambling",
  "casino",
  "casino app",
  "gambling site",
  "online casino",
  "betting",
  "sportsbook",
  "betting tips",
  "betting app",
  "online betting",
  "betting odds",
  "odds",
  "wager",
  "wager money",
  "parlay",
  "spread betting",
  "live betting",
  "crypto betting",
  "fantasy betting",
  "real money games",
  "cash games",
  "rummy cash",
  "teen patti cash",
  "lottery",
  "scratch cards",
  "poker",
  "roulette",
  "slots",
  "drugs",
  "drugs online",
  "buy drugs",
  "narcotics",
  "weed",
  "smoking",
  "cigarettes",
  "hookah",
  "alcohol",
  "alcohol drink",
  "beer",
  "testicle",
  "testicles",
  "liquor",
  "drunk",
  "vodka",
  "whiskey",
  "vaping",
  "vape",
  "vape pen",
  "ecigarette",
  "drugs",
  "cocaine",
  "meth",
  "heroin",
  "mdma",
  "lsd",
  "ecstasy",
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
  "sperm",
  "cum",
  "ejaculate",
  "orgy",
  "anal",
  "vaginal",
  "fuck"
];

const CHARACTER_VARIANTS = {
  a: "[aA4@]",
  b: "[bB8]",
  e: "[eE3]",
  g: "[gG69]",
  i: "[iI1!|]",
  l: "[lL1|!]",
  o: "[oO0]",
  s: "[sS5$]",
  t: "[tT7+]",
  x: "[xX%*]",
  z: "[zZ2]"
};

function createFuzzyCharacterPattern(character) {
  if (/\s/.test(character)) {
    return "[\\W_]*";
  }

  const lowerCharacter = character.toLowerCase();
  const variantPattern = CHARACTER_VARIANTS[lowerCharacter];

  if (variantPattern) {
    return `${variantPattern}+[\\W_]*`;
  }

  const escapedCharacter = character.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return `${escapedCharacter}+[\\W_]*`;
}

function createUnsafePattern(term) {
  const joinedPattern = term
    .split("")
    .map((character) => createFuzzyCharacterPattern(character))
    .join("");

  return new RegExp(`(^|[^a-z0-9])(${joinedPattern})(?=[^a-z0-9]|$)`, "gi");
}

const UNSAFE_PATTERNS = UNSAFE_TERMS.map((term) => createUnsafePattern(term));
const TARGET_SELECTOR = "p, span, div";
const BLUR_CLASS = "kid-safe-blur";
const BLUR_SELECTOR = `span.${BLUR_CLASS}`;

function ensureBlurStyle() {
  if (document.getElementById("kid-safe-blur-style")) {
    return;
  }

  const style = document.createElement("style");
  style.id = "kid-safe-blur-style";
  style.textContent = `
    .${BLUR_CLASS} {
      filter: blur(8px);
      transition: filter 0.2s ease;
      display: inline-block;
    }
  `;
  document.documentElement.appendChild(style);
}

function shouldSkipElement(element) {
  if (!element) {
    return true;
  }

  return Boolean(
    element.closest("script, style, noscript, textarea, input, code, pre")
  );
}

function unwrapBlurSpans(rootNode) {
  if (!rootNode || rootNode.nodeType !== Node.ELEMENT_NODE) {
    return;
  }

  const blurSpans = rootNode.matches(BLUR_SELECTOR)
    ? [rootNode]
    : rootNode.querySelectorAll(BLUR_SELECTOR);

  for (const blurSpan of blurSpans) {
    blurSpan.replaceWith(document.createTextNode(blurSpan.textContent || ""));
  }
}

function getReplacementFragment(text) {
  const matches = [];

  for (const pattern of UNSAFE_PATTERNS) {
    pattern.lastIndex = 0;

    for (const match of text.matchAll(pattern)) {
      const fullMatch = match[0];
      const prefix = match[1] || "";
      const matchedText = match[2] || "";
      const startIndex = match.index + prefix.length;
      const endIndex = startIndex + matchedText.length;

      if (matchedText) {
        matches.push({ startIndex, endIndex });
      }
    }
  }

  if (matches.length === 0) {
    return null;
  }

  matches.sort((left, right) => left.startIndex - right.startIndex);

  const mergedMatches = [];

  for (const match of matches) {
    const previousMatch = mergedMatches[mergedMatches.length - 1];

    if (!previousMatch || match.startIndex > previousMatch.endIndex) {
      mergedMatches.push({ ...match });
      continue;
    }

    previousMatch.endIndex = Math.max(previousMatch.endIndex, match.endIndex);
  }

  const fragment = document.createDocumentFragment();
  let currentIndex = 0;

  for (const match of mergedMatches) {
    if (match.startIndex > currentIndex) {
      fragment.appendChild(
        document.createTextNode(text.slice(currentIndex, match.startIndex))
      );
    }

    const blurSpan = document.createElement("span");
    blurSpan.className = BLUR_CLASS;
    blurSpan.textContent = text.slice(match.startIndex, match.endIndex);
    fragment.appendChild(blurSpan);
    currentIndex = match.endIndex;
  }

  if (currentIndex < text.length) {
    fragment.appendChild(document.createTextNode(text.slice(currentIndex)));
  }

  return fragment;
}

function blurUnsafeWordsInElement(element) {
  if (!element || shouldSkipElement(element)) {
    return;
  }

  unwrapBlurSpans(element);

  const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.nodeValue || !node.nodeValue.trim()) {
        return NodeFilter.FILTER_REJECT;
      }

      const parentElement = node.parentElement;

      if (!parentElement || shouldSkipElement(parentElement) || parentElement.closest(BLUR_SELECTOR)) {
        return NodeFilter.FILTER_REJECT;
      }

      return NodeFilter.FILTER_ACCEPT;
    }
  });

  const textNodes = [];
  let currentNode = walker.nextNode();

  while (currentNode) {
    textNodes.push(currentNode);
    currentNode = walker.nextNode();
  }

  for (const textNode of textNodes) {
    const replacementFragment = getReplacementFragment(textNode.nodeValue);

    if (replacementFragment) {
      textNode.replaceWith(replacementFragment);
    }
  }
}

function scrubDocument(rootNode = document.body) {
  if (!rootNode) {
    return;
  }

  if (rootNode.nodeType === Node.ELEMENT_NODE && rootNode.matches(TARGET_SELECTOR)) {
    blurUnsafeWordsInElement(rootNode);
  }

  if (rootNode.nodeType !== Node.ELEMENT_NODE) {
    return;
  }

  const matchingElements = rootNode.querySelectorAll(TARGET_SELECTOR);

  for (const element of matchingElements) {
    blurUnsafeWordsInElement(element);
  }
}

const observer = new MutationObserver((mutations) => {
  for (const mutation of mutations) {
    if (mutation.type === "characterData") {
      blurUnsafeWordsInElement(mutation.target.parentElement?.closest(TARGET_SELECTOR));
      continue;
    }

    for (const node of mutation.addedNodes) {
      if (node.nodeType === Node.ELEMENT_NODE) {
        scrubDocument(node);
      }
    }
  }
});

ensureBlurStyle();
scrubDocument();
observer.observe(document.documentElement, {
  childList: true,
  subtree: true,
  characterData: true
});
