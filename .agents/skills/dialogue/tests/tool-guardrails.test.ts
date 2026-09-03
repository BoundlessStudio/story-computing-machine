const decoder = new TextDecoder();

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

async function runScript(script: URL, args: string[]): Promise<string> {
  const command = new Deno.Command(Deno.execPath(), {
    args: ["run", "--allow-read", script.href, ...args],
    stdout: "piped",
    stderr: "piped",
  });
  const result = await command.output();
  const stderr = decoder.decode(result.stderr);
  assert(result.success, `Script failed: ${stderr}`);
  return decoder.decode(result.stdout);
}

Deno.test("dialogue audit never presents heuristic output as a coherence pass", async () => {
  const script = new URL("../scripts/dialogue-audit.ts", import.meta.url);
  const impossibleChronology =
    '"I need to trust you because my father died tomorrow. Maybe we will plan together."';

  const report = await runScript(script, ["--text", impossibleChronology]);
  assert(
    report.includes("This report is not a dialogue PASS"),
    "Human-readable output must disclaim dialogue certification",
  );
  assert(
    report.includes("physical and temporal possibility"),
    "Human-readable output must name the missing chronology judgment",
  );
  assert(
    !report.includes("Dialogue passes basic checks"),
    "A heuristic match must never be described as a basic pass",
  );

  const json = JSON.parse(
    await runScript(script, ["--json", "--text", impossibleChronology]),
  );
  assert(
    json.manualReview?.required === true,
    "JSON must require manual review",
  );
  assert(
    json.manualReview.cannotAssess.includes(
      "listener uptake and reply causality",
    ),
    "JSON must expose listener-uptake limitations",
  );
  assert(
    !("functionScore" in json),
    "JSON must not expose a generic function score that can be mistaken for quality",
  );
});

Deno.test("dialogue audit does not punish earned direct emotion", async () => {
  const script = new URL("../scripts/dialogue-audit.ts", import.meta.url);
  const directClinicalAnswer =
    '"Are you hurt anywhere else?" "No. I\'m scared, but just the arm."';

  const json = JSON.parse(
    await runScript(script, ["--json", "--text", directClinicalAnswer]),
  );
  assert(
    !json.issues.some((issue: string) => issue.includes("On-The-Nose")),
    "A direct emotion must not be an automatic issue",
  );
  assert(
    !json.recommendations.some((recommendation: string) =>
      recommendation.includes("shown behavior or subtext")
    ),
    "A direct emotion must not trigger an automatic subtext rewrite",
  );
  assert(
    !json.recommendations.some((recommendation: string) =>
      recommendation.includes("additional character")
    ),
    "A coherent single-purpose exchange must not trigger an automatic extra-function rewrite",
  );
});

Deno.test("voice statistics never present surface difference as dialogue quality", async () => {
  const script = new URL("../scripts/voice-check.ts", import.meta.url);
  const fluentNonsense = [
    "Auden: It is locked during the cycle.",
    "Mica: I know how dryers work.",
    "Auden: You just tried to peel one.",
  ].join("\n");

  const report = await runScript(script, ["--text", fluentNonsense]);
  assert(
    report.includes("Surface-pattern distinctiveness is not dialogue quality"),
    "Human-readable output must separate voice statistics from quality",
  );
  assert(
    report.includes("Surface-pattern index: not reported"),
    "Tiny samples must not receive a numeric surface-pattern index",
  );

  const json = JSON.parse(
    await runScript(script, ["--json", "--text", fluentNonsense]),
  );
  assert(
    json.manualReview?.required === true,
    "JSON must require manual review",
  );
  assert(
    json.manualReview.limitation.includes("never certifies PASS"),
    "JSON must expose the certification limitation",
  );
  assert(json.sampleAdequate === false, "JSON must flag an inadequate sample");
  assert(
    json.surfacePatternIndex === null,
    "JSON must suppress the index for an inadequate sample",
  );
});

Deno.test("production and review contracts keep coherence ahead of style", async () => {
  const files = {
    craft: new URL(
      "../../creative-writing-craft/resources/scene-construction.md",
      import.meta.url,
    ),
    writer: new URL("../../short-story-writing/SKILL.md", import.meta.url),
    reviewer: new URL("../../story-room/SKILL.md", import.meta.url),
    agents: new URL("../../../../AGENTS.md", import.meta.url),
    styleGuide: new URL(
      "../../../../universe/style-guide.md",
      import.meta.url,
    ),
  };

  const content = Object.fromEntries(
    await Promise.all(
      Object.entries(files).map(async ([name, url]) => [
        name,
        await Deno.readTextFile(url),
      ]),
    ),
  );

  assert(
    content.craft.includes("Shared reality comes first"),
    "General scene craft must put shared reality first",
  );
  assert(
    content.writer.includes("Ground dialogue before styling it") &&
      content.writer.includes("Never draft a punchline"),
    "Writer contract must prevent delivery-first drafting",
  );
  assert(
    content.reviewer.includes("Before judging higher-order dialogue craft"),
    "Reviewer contract must run coherence before style",
  );
  for (
    const [name, text] of Object.entries({
      craft: content.craft,
      writer: content.writer,
      reviewer: content.reviewer,
      agents: content.agents,
      styleGuide: content.styleGuide,
    })
  ) {
    assert(
      /\blie(?:s)?\b/.test(text) && /\bguess(?:es)?\b/.test(text) &&
        /\bmistake(?:s)?\b/.test(text),
      `${name} must preserve marked nonliteral and epistemic modes`,
    );
    assert(
      /semantic or\s+technical content/.test(text),
      `${name} must prevent replies from inventing a missing mapping`,
    );
    assert(
      /(?:could (?:plausibly )?have (?:seen|observed|inferred)|possible speaker access)/
        .test(text),
      `${name} must preserve explicit evidence boundaries`,
    );
  }
});

Deno.test("semantic corpus preserves the failure and exception coverage", async () => {
  const corpus = await Deno.readTextFile(
    new URL("semantic-coherence-cases.md", import.meta.url),
  );
  const caseCount = corpus.match(/^###\s+\d{2}\s+—/gm)?.length ?? 0;
  const verdictCount = corpus.match(
    /^\*\*Expected:\*\* (?:PASS|FAIL|CONTEXT)$/gm,
  )?.length ?? 0;

  assert(caseCount === 33, `Expected 33 semantic cases, found ${caseCount}`);
  assert(
    verdictCount === caseCount,
    "Every semantic case must have exactly one expected verdict",
  );
  assert(
    /You just tried to peel one[\s\S]*?\*\*Expected:\*\* FAIL/.test(corpus),
    "The originating setup-delivery regression must remain a failure",
  );
  for (
    const positiveControl of [
      "Character-supported lie",
      "Panic creates a legible non sequitur",
      "Visible fact used as relationship contact",
      "Ordinary single-purpose coordination",
      "Fresh metaphor with a recoverable image",
      "Earned directness",
      "Deliberate non sequitur registered as play",
      "Inference stays inside the evidence boundary",
    ]
  ) {
    assert(
      corpus.includes(positiveControl),
      `Missing positive control: ${positiveControl}`,
    );
  }
  assert(
    corpus.includes("**Expected:** CONTEXT"),
    "The corpus must preserve an underdetermined-context outcome",
  );
});
