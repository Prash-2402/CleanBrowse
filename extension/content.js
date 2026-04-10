const {
  BLUR_CLASS_NAME,
  CHARACTER_VARIANTS,
  LOG_PREFIX,
  TEXT_FILTER_TERMS,
  TEXT_SCAN_TARGET_SELECTOR
} = globalThis.CLEAN_BROWSE_CONFIG;

console.log(`${LOG_PREFIX} Content filtering active.`);

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

const UNSAFE_PATTERNS = TEXT_FILTER_TERMS.map((term) => createUnsafePattern(term));
const TARGET_SELECTOR = TEXT_SCAN_TARGET_SELECTOR;
const BLUR_CLASS = BLUR_CLASS_NAME;
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

      if (
        !parentElement ||
        shouldSkipElement(parentElement) ||
        parentElement.closest(BLUR_SELECTOR)
      ) {
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
      blurUnsafeWordsInElement(
        mutation.target.parentElement?.closest(TARGET_SELECTOR)
      );
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
