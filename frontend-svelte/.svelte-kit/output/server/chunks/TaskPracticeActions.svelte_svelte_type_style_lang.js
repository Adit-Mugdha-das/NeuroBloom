const TASK_PLAY_MODE = Object.freeze({
  PRACTICE: "practice",
  RECORDED: "recorded"
});
const TRAINING_TASK_CODES = [
  "wcst",
  "visual-search",
  "pasat",
  "verbal-fluency",
  "operation-span",
  "useful-field-of-view",
  "multiple-object-tracking",
  "twenty-questions",
  "spatial-span",
  "letter-number-sequencing",
  "trail-making-b",
  "landmark-task",
  "trail-making-a",
  "inspection-time",
  "tower-of-london",
  "gonogo",
  "stroop",
  "stockings-of-cambridge",
  "flanker",
  "choice-reaction-time",
  "dual-n-back",
  "category-fluency",
  "cancellation-test",
  "digit-span",
  "plus-minus",
  "dccs",
  "pattern-comparison",
  "rule-shift",
  "sdmt",
  "sart"
];
const BASELINE_TASK_CODES = [
  "attention",
  "flexibility",
  "planning",
  "processing-speed",
  "visual-scanning",
  "working-memory"
];
const PATIENT_TASK_CODES = [...TRAINING_TASK_CODES, ...BASELINE_TASK_CODES];
const PROFILES = {
  "dual-n-back": {
    strategy: "requery",
    trialLimit: 2,
    query: { difficulty: 1, num_trials: 2 }
  },
  "digit-span": {
    strategy: "requery",
    trialLimit: 3,
    query: { difficulty: 1, num_trials: 3 }
  },
  "spatial-span": {
    strategy: "requery",
    trialLimit: 3,
    query: { difficulty: 1, num_trials: 3 }
  },
  "operation-span": {
    strategy: "requery",
    trialLimit: 2,
    query: { difficulty: 1, num_trials: 2 }
  },
  "letter-number-sequencing": {
    strategy: "requery",
    trialLimit: 3,
    query: { difficulty: 1, num_trials: 3 }
  },
  "choice-reaction-time": {
    strategy: "requery",
    trialLimit: 4,
    query: { difficulty: 1 }
  },
  "trail-making-a": {
    strategy: "requery",
    trialLimit: 8,
    query: { difficulty: 1 }
  },
  "pattern-comparison": {
    strategy: "requery",
    trialLimit: 8,
    query: { difficulty: 1 }
  },
  "sdmt": {
    strategy: "requery",
    trialLimit: 8,
    query: { difficulty: 1 }
  },
  "sart": {
    strategy: "requery",
    trialLimit: 12,
    query: { difficulty: 1 }
  },
  "rule-shift": {
    strategy: "requery",
    trialLimit: 6,
    query: { difficulty: 1 }
  },
  "landmark-task": {
    strategy: "requery",
    trialLimit: 6,
    query: { difficulty: 1 }
  },
  "pasat": {
    strategy: "existing",
    trialLimit: 4
  },
  "wcst": {
    strategy: "existing",
    trialLimit: 12
  },
  "stroop": {
    strategy: "existing",
    trialLimit: 6
  },
  "gonogo": {
    strategy: "existing",
    trialLimit: 6
  },
  "flanker": {
    strategy: "existing",
    trialLimit: 8
  },
  "inspection-time": {
    strategy: "existing",
    trialLimit: 6
  },
  "trail-making-b": {
    strategy: "existing",
    trialLimit: 6
  },
  "visual-search": {
    strategy: "local",
    timeLimitSeconds: 12
  },
  "category-fluency": {
    strategy: "local",
    timeLimitSeconds: 20
  },
  "verbal-fluency": {
    strategy: "local",
    timeLimitSeconds: 15
  },
  "cancellation-test": {
    strategy: "local",
    timeLimitSeconds: 15
  },
  "useful-field-of-view": {
    strategy: "local",
    trialLimit: 4
  },
  "multiple-object-tracking": {
    strategy: "local",
    trialLimit: 3
  },
  "twenty-questions": {
    strategy: "local",
    trialLimit: 1
  },
  "tower-of-london": {
    strategy: "local",
    trialLimit: 2
  },
  "stockings-of-cambridge": {
    strategy: "local",
    trialLimit: 2
  },
  "plus-minus": {
    strategy: "local",
    trialLimit: 2
  },
  "dccs": {
    strategy: "local",
    trialLimit: 2
  },
  "attention": {
    strategy: "local",
    trialLimit: 12,
    timeLimitSeconds: 14
  },
  "flexibility": {
    strategy: "local",
    trialLimit: 8
  },
  "planning": {
    strategy: "local",
    trialLimit: 3
  },
  "processing-speed": {
    strategy: "local",
    trialLimit: 6
  },
  "visual-scanning": {
    strategy: "local",
    trialLimit: 10
  },
  "working-memory": {
    strategy: "local",
    trialLimit: 6,
    timeLimitSeconds: 18
  }
};
const PRACTICE_COPY = {
  en: {
    trigger: "Try Practice",
    helper: "Practice only. Not recorded.",
    bannerTitle: "Practice Round",
    bannerText: "This practice run will not affect your recorded performance.",
    complete: "Practice complete. Start when ready."
  },
  bn: {
    trigger: "অনুশীলন করুন",
    helper: "শুধু অনুশীলন। এটি রেকর্ড হবে না।",
    bannerTitle: "অনুশীলনী রাউন্ড",
    bannerText: "এই অনুশীলনের ফল রেকর্ড হবে না।",
    complete: "অনুশীলন শেষ। প্রস্তুত হলে শুরু করুন।"
  }
};
function getPracticeCopy(locale = "en") {
  return PRACTICE_COPY[locale === "bn" ? "bn" : "en"];
}
function assertPracticeCoverage() {
  const missing = PATIENT_TASK_CODES.filter((taskCode) => !PROFILES[taskCode]);
  if (missing.length > 0) {
    throw new Error(`Missing practice profiles for: ${missing.join(", ")}`);
  }
}
assertPracticeCoverage();
export {
  TASK_PLAY_MODE as T,
  getPracticeCopy as g
};
