const domainOrder = [
  "working_memory",
  "attention",
  "processing_speed",
  "flexibility",
  "visual_scanning",
  "planning"
];
const domainNames = {
  working_memory: "Working Memory",
  attention: "Attention",
  flexibility: "Cognitive Flexibility",
  planning: "Planning",
  processing_speed: "Processing Speed",
  visual_scanning: "Visual Scanning"
};
function getDomainName(domain) {
  return domainNames[domain] || domain;
}
function calculateOverallScore(metrics) {
  const domainMetrics = Object.values({});
  if (domainMetrics.length === 0) return 0;
  const total = domainMetrics.reduce((sum, domain) => sum + (domain.average_score || 0), 0);
  return Number((total / domainMetrics.length).toFixed(1));
}
function calculateTrendDelta(trendsData) {
  const points = [];
  if (points.length < 2) return 0;
  const first = points[0]?.avg_score || 0;
  const last = points[points.length - 1]?.avg_score || 0;
  return Number((last - first).toFixed(1));
}
function calculateBaselineDifficulty(score) {
  return Math.max(1, Math.floor((score || 0) / 10));
}
function getClinicalStatusLabel(value) {
  if ((value || 0) >= 5) return "Improving";
  if ((value || 0) <= -5) return "Needs Attention";
  return "Stable";
}
function getClinicalStatusTone(value) {
  if ((value || 0) >= 5) return "improving";
  if ((value || 0) <= -5) return "attention";
  return "stable";
}
function formatPointChange(value) {
  if (Math.abs(value || 0) < 1) return "No meaningful change since baseline";
  return `${value > 0 ? "+" : ""}${Number(value || 0).toFixed(0)} points since baseline`;
}
export {
  calculateTrendDelta as a,
  getClinicalStatusLabel as b,
  calculateOverallScore as c,
  getDomainName as d,
  calculateBaselineDifficulty as e,
  formatPointChange as f,
  getClinicalStatusTone as g,
  domainOrder as h
};
