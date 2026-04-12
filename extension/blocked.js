// Using a short timeout ensures the DOM and URL bar have completely synced in Chrome Extensions
setTimeout(() => {
  try {
    const rawUrl = window.location.href;
    if (rawUrl.includes("?")) {
      const query = rawUrl.substring(rawUrl.indexOf("?") + 1);
      
      const getParam = (param) => {
        const regex = new RegExp(`(^|&)${param}=([^&]*)`);
        const match = query.match(regex);
        return match ? decodeURIComponent(match[2]) : null;
      };

      const blockedUrl = getParam("url");
      const blockReason = getParam("reason");

      if (blockedUrl && blockedUrl !== "undefined") {
        document.getElementById("details").textContent = "Blocked address:";
        document.getElementById("url").textContent = blockedUrl;
      } else {
        document.getElementById("details").textContent = "Raw URL: " + rawUrl;
      }
      
      if (blockReason && blockReason !== "undefined" && blockReason !== "") {
        const titleCaseReason = blockReason.charAt(0).toUpperCase() + blockReason.slice(1);
        const reasonPara = document.getElementById("details");
        reasonPara.innerHTML = `CleanBrowse proactively blocked this page due to <b>${titleCaseReason}</b> detection.`;
      }

      const score = getParam("score");
      if (score && !isNaN(score)) {
        const confidence = (parseFloat(score) * 100).toFixed(0);
        document.getElementById("score").textContent = confidence;
        document.getElementById("ai-score-container").style.display = "flex";
      }
    } else {
      document.getElementById("details").textContent = "Raw URL without params: " + rawUrl;
    }
  } catch(e) {
    document.getElementById("details").textContent = "Error parsing parameters: " + e.toString();
  }
}, 50);
