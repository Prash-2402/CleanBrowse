const SAFETY_MODES = {
  KID: { id: "KID", label: "Kid", threshold: 0.2 },
  TEEN: { id: "TEEN", label: "Teen", threshold: 0.5 }
};

function evaluateSafety(score, activeModeId) {
  const threshold = SAFETY_MODES[activeModeId].threshold;
  const isUnsafe = score >= threshold;
  return {
    score: score,
    threshold: threshold,
    label: isUnsafe ? "unsafe" : "safe"
  };
}

const testCases = [
  { score: 0.1, mode: "KID" },
  { score: 0.3, mode: "KID" },
  { score: 0.3, mode: "TEEN" },
  { score: 0.6, mode: "TEEN" }
];

testCases.forEach(tc => {
  const result = evaluateSafety(tc.score, tc.mode);
  console.log(`Score: ${tc.score} | Mode: ${tc.mode} | Result: ${result.label.toUpperCase()}`);
});
