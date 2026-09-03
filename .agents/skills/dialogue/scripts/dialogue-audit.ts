#!/usr/bin/env -S deno run --allow-read

/**
 * Heuristic Dialogue Pattern Audit
 *
 * Analyzes dialogue for function coverage (plot, character, subtext, relationship)
 * and common anti-patterns (exposition dump, identical twins, etc.).
 * It cannot judge literal or conversational coherence and never certifies PASS.
 *
 * Usage:
 *   deno run --allow-read dialogue-audit.ts scene.txt
 *   deno run --allow-read dialogue-audit.ts --text "dialogue here"
 */

interface DialogueAudit {
  lineCount: number;
  wordCount: number;
  dialogueRatio: number;

  // Function detection
  functions: {
    plotAdvancement: FunctionSignals;
    characterReveal: FunctionSignals;
    subtextPresent: FunctionSignals;
    relationshipDynamics: FunctionSignals;
  };

  // Tag analysis
  tagAnalysis: {
    saidCount: number;
    otherTagCount: number;
    actionBeatCount: number;
    saidBookisms: string[];
    tagHealthy: boolean;
  };

  // Anti-pattern detection
  antiPatterns: AntiPattern[];

  // Overall assessment
  issues: string[];
  recommendations: string[];
  manualReview: {
    required: boolean;
    cannotAssess: string[];
  };
}

interface FunctionSignals {
  detected: boolean;
  confidence: "high" | "medium" | "low";
  signals: string[];
}

interface AntiPattern {
  name: string;
  detected: boolean;
  severity: "high" | "medium" | "low";
  evidence: string[];
}

const MANUAL_COHERENCE_GATES = [
  "verb-object and action-language compatibility",
  "referent resolution",
  "physical and temporal possibility",
  "speaker knowledge stance and perception",
  "listener uptake and reply causality",
  "whether a line should exist",
];

// Patterns for detecting dialogue functions

const PLOT_PATTERNS = [
  /\b(must|need to|have to|going to|will|plan|decide|discover|find out|learn that)\b/gi,
  /\b(happened|killed|stole|escaped|arrived|left|died|born|married|divorced)\b/gi,
  /\b(where is|when did|who did|what happened|how did|why did)\b/gi,
  /\b(tomorrow|tonight|next|before|after|deadline|time)\b/gi,
];

const CHARACTER_PATTERNS = [
  /\b(I always|I never|I believe|I think|I feel|I want|I need|I hate|I love)\b/gi,
  /\b(my father|my mother|my family|when I was|I remember|I grew up)\b/gi,
  /\b(I'm the kind of|I'm not the type|that's not who I am|that's just how I)\b/gi,
  /\b(afraid of|proud of|ashamed of|sorry for|grateful for)\b/gi,
];

const SUBTEXT_INDICATORS = [
  // Questions that aren't really questions
  /\b(don't you think|wouldn't you say|isn't it|aren't you)\b/gi,
  // Deflection and evasion
  /\b(I don't know|maybe|perhaps|we'll see|it depends|that's one way)\b/gi,
  // Loaded statements
  /\b(interesting|fine|whatever|sure|if you say so|I suppose)\b/gi,
  // Changing subject
  /\b(anyway|but what about|speaking of|by the way|never mind)\b/gi,
];

const RELATIONSHIP_PATTERNS = [
  /\b(you always|you never|you used to|remember when we|between us)\b/gi,
  /\b(trust|believe|forgive|understand|know me|don't know me)\b/gi,
  /\b(we|us|our|together|apart|between|relationship)\b/gi,
  /\b(like you|love you|hate you|miss you|need you|want you)\b/gi,
];

// Anti-pattern detection

const EXPOSITION_PATTERNS = [
  /\b(as you know|as I'm sure you're aware|you remember|of course you know)\b/gi,
  /\b(let me explain|I'll tell you|you see|the thing is|basically)\b/gi,
  /\b(founded in|established in|years ago when|the history of)\b/gi,
];

const SAID_BOOKISMS = [
  "exclaimed",
  "declared",
  "announced",
  "proclaimed",
  "stated",
  "uttered",
  "articulated",
  "vocalized",
  "verbalized",
  "intoned",
  "opined",
  "remarked",
  "observed",
  "noted",
  "commented",
  "retorted",
  "countered",
  "snapped",
  "barked",
  "growled",
  "hissed",
  "snarled",
  "spat",
  "thundered",
  "boomed",
  "cooed",
  "purred",
  "breathed",
  "sighed",
  "moaned",
  "whimpered",
  "sobbed",
  "wailed",
  "shrieked",
  "screamed",
  "chuckled",
  "giggled",
  "laughed",
  "snickered",
  "guffawed",
];

function countMatches(text: string, patterns: RegExp[]): string[] {
  const matches: string[] = [];
  for (const pattern of patterns) {
    const found = text.match(pattern);
    if (found) {
      matches.push(...found.slice(0, 3));
    }
  }
  return [...new Set(matches)];
}

function detectFunction(text: string, patterns: RegExp[]): FunctionSignals {
  const signals = countMatches(text, patterns);
  const count = signals.length;

  let confidence: "high" | "medium" | "low";
  if (count >= 3) confidence = "high";
  else if (count >= 1) confidence = "medium";
  else confidence = "low";

  return {
    detected: count > 0,
    confidence,
    signals: signals.slice(0, 5),
  };
}

function analyzeDialogueTags(text: string): DialogueAudit["tagAnalysis"] {
  // Count "said"
  const saidMatches = text.match(/\bsaid\b/gi) || [];

  // Count other tags (said-bookisms)
  const bookismPattern = new RegExp(`\\b(${SAID_BOOKISMS.join("|")})\\b`, "gi");
  const bookismMatches = text.match(bookismPattern) || [];

  // Count action beats (sentences with dialogue followed by action, not tag)
  // Heuristic: dialogue ending with period followed by capital letter action
  const actionBeatPattern =
    /"\s+[A-Z][a-z]+\s+(walked|stood|sat|turned|looked|crossed|nodded|shook|smiled|frowned|leaned|moved|stepped|grabbed|picked|put|set|ran|jumped)/gi;
  const actionBeats = text.match(actionBeatPattern) || [];

  const foundBookisms = [
    ...new Set(bookismMatches.map((m) => m.toLowerCase())),
  ];

  return {
    saidCount: saidMatches.length,
    otherTagCount: bookismMatches.length,
    actionBeatCount: actionBeats.length,
    saidBookisms: foundBookisms,
    tagHealthy: bookismMatches.length <= saidMatches.length,
  };
}

function detectAntiPatterns(text: string): AntiPattern[] {
  const patterns: AntiPattern[] = [];

  // Exposition dump
  const expositionMatches = countMatches(text, EXPOSITION_PATTERNS);
  patterns.push({
    name: "Exposition Dump",
    detected: expositionMatches.length > 0,
    severity: expositionMatches.length >= 2 ? "high" : "medium",
    evidence: expositionMatches,
  });

  // Emotional Narrator (adverbs in tags)
  const emotionalTagPattern =
    /said\s+(angrily|sadly|happily|nervously|anxiously|fearfully|hopefully|desperately|quietly|loudly|softly|firmly|gently|harshly)/gi;
  const emotionalMatches = text.match(emotionalTagPattern) || [];
  patterns.push({
    name: "Emotional Narrator",
    detected: emotionalMatches.length > 0,
    severity: emotionalMatches.length >= 3 ? "high" : "medium",
    evidence: [...new Set(emotionalMatches)].slice(0, 3),
  });

  // The Philosopher (explicit theme statements)
  const philosopherPattern =
    /\b(the moral is|what this means|the lesson here|you see|the truth is|life is about|that's what .* is really about)\b/gi;
  const philosopherMatches = text.match(philosopherPattern) || [];
  patterns.push({
    name: "The Philosopher",
    detected: philosopherMatches.length > 0,
    severity: "medium",
    evidence: [...new Set(philosopherMatches)].slice(0, 3),
  });

  // Court Reporter (too much filler)
  const fillerPattern = /\b(um|uh|er|ah|well,|so,|like,|you know,|I mean,)\b/gi;
  const fillerMatches = text.match(fillerPattern) || [];
  const fillerDensity = fillerMatches.length / (text.split(/\s+/).length || 1);
  patterns.push({
    name: "Court Reporter",
    detected: fillerDensity > 0.05,
    severity: fillerDensity > 0.1 ? "high" : "low",
    evidence: [...new Set(fillerMatches)].slice(0, 5),
  });

  return patterns;
}

function calculateDialogueRatio(text: string): number {
  const quotes = text.match(/"[^"]+"/g) || [];
  const quotedChars = quotes.join("").length;
  return quotedChars / text.length;
}

function auditDialogue(text: string): DialogueAudit {
  const words = text.split(/\s+/).filter((w) => w.length > 0);
  const dialogueContent = (text.match(/"[^"]+"/g) || []).join(" ");

  // Detect functions
  const functions = {
    plotAdvancement: detectFunction(dialogueContent, PLOT_PATTERNS),
    characterReveal: detectFunction(dialogueContent, CHARACTER_PATTERNS),
    subtextPresent: detectFunction(dialogueContent, SUBTEXT_INDICATORS),
    relationshipDynamics: detectFunction(
      dialogueContent,
      RELATIONSHIP_PATTERNS,
    ),
  };

  // Analyze tags
  const tagAnalysis = analyzeDialogueTags(text);

  // Detect anti-patterns
  const antiPatterns = detectAntiPatterns(text);

  // Generate issues and recommendations
  const issues: string[] = [];
  const recommendations: string[] = [];

  if (!tagAnalysis.tagHealthy) {
    issues.push("Too many said-bookisms relative to 'said'");
    recommendations.push(
      "Replace descriptive tags with action beats or let dialogue carry emotion",
    );
  }

  for (const pattern of antiPatterns) {
    if (pattern.detected && pattern.severity !== "low") {
      issues.push(`Anti-pattern detected: ${pattern.name}`);
    }
  }

  if (antiPatterns.find((p) => p.name === "Exposition Dump" && p.detected)) {
    recommendations.push(
      "Surface information through participant need, discovery, consequence, or genuine disagreement",
    );
  }

  if (antiPatterns.find((p) => p.name === "Emotional Narrator" && p.detected)) {
    recommendations.push(
      "Remove adverbs from tags; let words and action beats carry emotion",
    );
  }

  return {
    lineCount: text.split("\n").filter((l) => l.trim()).length,
    wordCount: words.length,
    dialogueRatio: calculateDialogueRatio(text),
    functions,
    tagAnalysis,
    antiPatterns,
    issues,
    recommendations,
    manualReview: {
      required: true,
      cannotAssess: MANUAL_COHERENCE_GATES,
    },
  };
}

function formatReport(audit: DialogueAudit): string {
  const lines: string[] = [];
  const detectedFunctionSignals =
    Object.values(audit.functions).filter((f) => f.detected).length;

  lines.push("# Heuristic Dialogue Pattern Audit\n");
  lines.push(
    "> This report is not a dialogue PASS. Run the manual Ground check before using any result or recommendation.\n",
  );
  lines.push(
    `Words: ${audit.wordCount} | Dialogue ratio: ${
      (audit.dialogueRatio * 100).toFixed(1)
    }%`,
  );
  lines.push(
    `Function-signal categories: ${detectedFunctionSignals}/4 (keyword heuristics only)\n`,
  );

  lines.push("## Required Manual Ground Check\n");
  lines.push("  This tool cannot assess:");
  for (const gate of audit.manualReview.cannotAssess) {
    lines.push(`  - ${gate}`);
  }
  lines.push("");

  lines.push("## Function-Signal Detection\n");
  const functionNames = {
    plotAdvancement: "Plot Advancement",
    characterReveal: "Character Revelation",
    subtextPresent: "Subtext Present",
    relationshipDynamics: "Relationship Dynamics",
  };

  for (const [key, label] of Object.entries(functionNames)) {
    const func = audit.functions[key as keyof typeof audit.functions];
    const status = func.detected ? "+" : "-";
    const conf = func.detected ? ` (${func.confidence})` : "";
    const signals = func.signals.length > 0
      ? `: ${func.signals.slice(0, 3).join(", ")}`
      : "";
    lines.push(`  ${status} ${label}${conf}${signals}`);
  }
  lines.push("");

  lines.push("## Tag Analysis\n");
  lines.push(`  'said' count: ${audit.tagAnalysis.saidCount}`);
  lines.push(`  Other tags: ${audit.tagAnalysis.otherTagCount}`);
  lines.push(`  Action beats: ${audit.tagAnalysis.actionBeatCount}`);
  if (audit.tagAnalysis.saidBookisms.length > 0) {
    lines.push(
      `  Said-bookisms found: ${audit.tagAnalysis.saidBookisms.join(", ")}`,
    );
  }
  lines.push(
    `  Tag health: ${audit.tagAnalysis.tagHealthy ? "Good" : "Needs work"}`,
  );
  lines.push("");

  const detectedPatterns = audit.antiPatterns.filter((p) => p.detected);
  if (detectedPatterns.length > 0) {
    lines.push("## Anti-Patterns Detected\n");
    for (const pattern of detectedPatterns) {
      lines.push(`  - ${pattern.name} (${pattern.severity})`);
      if (pattern.evidence.length > 0) {
        lines.push(`    Evidence: ${pattern.evidence.slice(0, 2).join(", ")}`);
      }
    }
    lines.push("");
  }

  if (audit.issues.length > 0) {
    lines.push("## Issues\n");
    for (const issue of audit.issues) {
      lines.push(`  - ${issue}`);
    }
    lines.push("");
  }

  if (audit.recommendations.length > 0) {
    lines.push("## Recommendations\n");
    for (const rec of audit.recommendations) {
      lines.push(`  - ${rec}`);
    }
    lines.push("");
  }

  if (audit.issues.length === 0) {
    lines.push("## Assessment\n");
    lines.push(
      "  No heuristic pattern flags were found. This is not a coherence pass. Verify manually that:",
    );
    lines.push(
      "  - Words describe the action and objects actually on the page",
    );
    lines.push(
      "  - Each speaker's knowledge, guess, lie, or mistake is supported",
    );
    lines.push("  - Listeners can recover the meaning their replies depend on");
    lines.push("  - Each line needs to exist");
    lines.push("  - Characters sound distinct (run voice-check)");
    lines.push(
      "  - Any indirection or subtext is character- and context-supported",
    );
    lines.push("  - The exchange performs its participant-specific purpose");
    lines.push("");
  }

  return lines.join("\n");
}

async function main(): Promise<void> {
  const args = Deno.args;

  if (args.includes("--help") || args.includes("-h")) {
    console.log(`Heuristic Dialogue Pattern Audit

Usage:
  deno run --allow-read dialogue-audit.ts <file>
  deno run --allow-read dialogue-audit.ts --text "dialogue here"

Options:
  --text "..."  Provide text inline
  --json        Output as JSON
  --help        Show this message

Checks for:
  - Function coverage (plot, character, subtext, relationship)
  - Tag usage (said vs. said-bookisms)
  - Common anti-patterns (exposition dump, emotional narrator, etc.)

Cannot assess literal action-language fit, referents, speaker knowledge stance,
listener uptake, reply causality, or whether a line should exist. This tool
never certifies dialogue PASS; run the manual Ground check first.
`);
    Deno.exit(0);
  }

  const jsonOutput = args.includes("--json");
  let text = "";

  if (args.includes("--text")) {
    const textIndex = args.indexOf("--text");
    text = args[textIndex + 1] || "";
  } else {
    const file = args.find((a) => !a.startsWith("--"));
    if (file) {
      try {
        text = await Deno.readTextFile(file);
      } catch (e) {
        console.error(`Error reading file: ${e}`);
        Deno.exit(1);
      }
    }
  }

  if (!text.trim()) {
    console.error(
      "Error: No text provided. Use --text or provide a file path.",
    );
    Deno.exit(1);
  }

  const audit = auditDialogue(text);

  if (jsonOutput) {
    console.log(JSON.stringify(audit, null, 2));
  } else {
    console.log(formatReport(audit));
  }
}

main();
