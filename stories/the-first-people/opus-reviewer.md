---
slug: the-first-people
title: "The First People"
story-file: story.md
canon: false
craft-profile: prospective-2026-08-23
reviewer: claude-opus-5-5
audited: 2026-09-25
dialogue: REVISE
edit-scope: targeted-dialogue
blocking: 1
major: 5
minor: 9
---

# Opus review: The First People

Independent audit for a later editing pass. It is not a `review.md` verdict,
does not change canon state, and does not authorize edits by itself.

## Verdict

- Dialogue: REVISE — Martin names "the war" before anyone has told him about it, and the burn and consent beats depend on pronouns or cues the listener cannot recover.
- Prose: REVISE — the narration explains the Fermi lesson again after the scenes have landed it, and single-sentence paragraphs set the default rhythm.
- Continuity and prompt: REVISE — the prompt is delivered, but the story never settles what Martin and humanity knew before tonight, which blurs its central reveal; also one small object contradiction.
- Edit scope: targeted-dialogue
- Existing review.md said: `Verdict: PASS`, `Dialogue: PASS`; disagree: it missed a knowledge leak and two Ground failures at decision beats.

This story has more distinct voices than the house default. Heshi speaks in
ceremony and route logic, Martin in dry domestic understatement, the translator
in surreal mistranslations, the pursuer in smooth legal reassurance, and the wall
in all-caps status fragments. The translation medium changes what people do in
the scenes: the war map built without "another successful sentence", the kettle
rebuke, the consent check. The failures are Ground failures at the hinges. Martin
knows about a war he has not been told of. The burn decision runs on "Close it" /
"This closes all of it" / "The road goes everywhere they do", and the reader
cannot tell whose road or which "it". At the consent beat Martin reacts to a
translation loss that only the narrator reports. Around the Fermi reveal, the
story states its answer four times in fourteen lines. The edit should fix what
each speaker can know and hear, pin the pronouns, and cut the restatements. It
should not restyle the voices.

## Edit guardrails

- Prompt: the stars turn to humanity as the oldest people; the Fermi answer (Earth was simply first) must stay legible; complete story that resolves its central promise; 2,500–4,000 words (currently about 3,360 of prose); broadly accessible; craft profile prospective-2026-08-23. Keep close third on Heshi (established, not prompt-mandated).
- Story facts to keep: humans built the road while Earth was alone; the root burn is irreversible, cannot select branches, and ends fast transit for everyone; connecting the census exposes hidden shelters to the pursuer; Heshi gives explicit consent; losses on the last branch; Heshi's home does not answer; the forty-day versus thirty-six-day aid choice; Martin's palm blistered in the root's pattern.
- Universe: "Earth" is the LOCKED era-bound label for the one physical world (`universe/locations.md` "The world across eras"; `universe/premise.md` "The deep-time shared world"). Do not add a real nation, civil date, or Galactic Cycle coordinate, and do not add magic. Humanity's partial memory across deep time fits LOCKED "Memory, myth, and recoverable truth".
- What works: the translator-garble device, the wordless war map, the pursuer's frictionless voice, the kettle exchange, the translator marking humor as "probable apology", Martin's humor dropping out at L267, "Now, Heshi?", and the restrained final choice. Do not flatten these into plain competent talk.

## Voice map

| Speaker | How they sound now | Problem | Target distinction |
| --- | --- | --- | --- |
| Heshi | Ceremonial address, no contractions, imperatives and lists ("Commanders. Elders."), one proverb; becomes terse under pressure ("Wrong order." "Now."); voice fails at the loss count | At L187 her intent at the decisive beat is unreadable ("Close it") | Keep the ceremony early and the curt imperatives late; make what she wants legible at each decision |
| Martin | Contractions, household comparisons, self-deprecating or deflecting jokes, slow simplified speech for the translator; humor drops at L267, then he asks instead of telling | In the first two-thirds his reflex reply re-defines Heshi's word; a few quips don't parse (L99, L199); he knows things he shouldn't (L63, L285) | Keep the dry humor and the move from correcting to asking; let some replies just answer, act, or ask |
| Translator | Surreal literal garbles ("Old mud property", "Incense keeps knives sharp", "funeral before door") | Mostly none; at L97–L99 the garble exists only to set up a Martin quip | Keep garbles that change what the listener does next |
| Pursuer | Smooth, legalistic, reassuring, false either-or ("There is no third responsible choice.") | None; the legal register is earned here | Keep; it should stay the easiest voice to understand |
| Wall / Earth | All-caps terse status fragments | None | Keep |

## Dialogue findings

### D1 · Blocking · Martin names a war nobody has mentioned

- Where: L63–L65, the name exchange at the wreck; compare L75 in the kitchen
- Text:
> “Unless you'd rather explain the war in the rain.”
> She understood only *war* and followed.
> “I know that you arrived through a system we're not supposed to have heard from in a very long time.”
- Problem: Ground/knowledge. At this point Martin has heard only two garbles ("Old mud property. Dependent animals remain in inventory." and "Hands are forbidden."). Nobody has said "war", and at L75 he says he knows only that she came through a long-silent system. The definite article presents the war as known. The story also makes the word carry weight, since it is the one word Heshi catches and the reason she follows him.
- Fix: Have Martin refer only to what he can see: the wreck, the pulse in the sky, her injuries. Then change L65 to whatever word or gesture she actually catches. Illustrative only: "Unless you'd rather explain whatever's up there in the rain." / "She understood only the pointing, and followed." Heshi should be the first to say "war" (she does at L77).

### D2 · Major · Consent check responds to a loss Martin cannot perceive

- Where: L283–L285, the room's question after the spindle is socketed
- Text:
> The room asked a question in both their languages. Heshi's version lost the word that distinguished consent from command.
> Martin pulled his hand away. “No. It has to be clear.”
- Problem: Ground/knowledge. Only the narrator (through Heshi) knows her version lost the consent word. Martin cannot read her language, and Heshi does nothing visible between the question and his reaction, so he appears to answer information he has no access to. This is the consent hinge of the whole story, so he needs a reason the reader can see.
- Fix: Give Martin an observable cue. Heshi could answer as if ordered, repeat the word she heard, or go still in a way he can see, or the translator could flag the rendering as uncertain. Keep "No. It has to be clear." and "Do you choose to hold this open?" Illustrative only: Heshi, before he pulls back: "Your machine commands it."

### D3 · Major · Burn decision turns on pronouns the reader cannot pin

- Where: L187–L199, after the red cover is opened
- Text:
> “Close it,” Heshi said.
> “This closes all of it.” Martin pointed to the counters, one by one.
> “Lead what? The road goes everywhere they do.”
- Problem: Ground/referent at the moral pivot. "Close it" can mean shut the red cover (refuse the burn) or close the road (burn it now). Martin echoes the verb, which leans toward the second reading, but "I did not come to ask this" leans toward the first, so the reader cannot tell what Heshi wants at her key choice. "The road goes everywhere they do" has no nearby antecedent for "they" (the enemy was last named many lines back) and states the logic backwards: the point is that any force humanity leads must travel on routes the enemy holds. Both of Martin's lines also follow the collection's correction-echo pattern (her word, sharpened and handed back).
- Fix: Make Heshi's intent explicit in her own terse register, either as a refusal ("Shut the cover.") or an impulse ("Burn it, then."), and have Martin's cost demonstration follow from that without echoing her verb. Replace "The road goes everywhere they do" with the concrete objection. Illustrative only: "Lead what? Anything we send goes by your road, and they're sitting on it." Keep "Lead what?" and Heshi's silent "She had no answer."

### D4 · Major · Fermi reveal stated four times in fourteen lines

- Where: L159–L173, the deep-date layout on the table
- Text:
> Earth had begun living first. Humanity had called into silence because, then, there had truly been no one to answer.
> “We listened,” Martin said. “There was nobody.”
> Her teachers had called that part devotion because the alternative was absurd.
> Martin stared at the dates with no triumph at all. “Somebody kept the receivers on.”
- Problem: Philosopher plus narration gloss. The narration states the answer (L161) before Martin says it. Martin says it (L163, L167). The narration says it again (L169: "had not emerged from a crowded sky... opened their eyes to no one"). Martin then closes with a fourth summary line. The reader has nothing left to infer at the story's central reveal. L171 also has two unclear referents: "that part" and "the alternative".
- Fix: Keep "We listened... There was nobody.", the counter touch, and "Not yet." They are short, earned by the prompt, and land through gesture. Cut L161's second sentence and the opening restatement in L169, but keep its concrete images (machines sent outward, empty stations, the road waiting). Clarify or cut L171. Keep "Somebody kept the receivers on." only if the narration restatements go; it then carries Martin's own stake as a listener rather than working as a third summary.

### D5 · Minor · Kinship exchange ends on an unreadable quip

- Where: L87–L99, the spindle plea in the kitchen
- Text:
> “Not children,” Martin said.
> “No. I mean, they aren't ours to own. Start again. Less ceremony.”
> Martin glanced at the stove. “Apparently not tonight.”
- Problem: The exchange runs correction, self-correction, counter-proverb, garble, quip. "Not children" and the stumbling backpedal are good: human, a little wrong, and they register Heshi's shock. The closer does not parse, though. It needs the reader to connect "incense" to the stove's scorched-leaf smell, and even then it is unclear what "not tonight" denies. The murky last word also lets her shock dissipate. "ours to own" is a tidy echo of "owners" at L81.
- Fix: Keep "Not children," the face-rub, and "Start again. Less ceremony." Cut "Apparently not tonight" or replace it with a plain reaction to the garble, or with no reply at all (he just touches the wall panel). Optionally loosen "ours to own" so it sounds less like a planted callback.

### D6 · Minor · Tag and uptake slips

- Where: L31 (arrival), L303 (rolling-burn demonstration), L233–L237 (surrender offer)
- Text:
> The human stared at her. “Right,” it rendered.
> She could not. The translator gave him *funeral before door*.
> “And they keep every door.”
- Problem: At L31 "it" reads first as "the human", because the translator was two sentences back. At L303 "Show me" is answered with "She could not", and then she shows him; the line means she could not say it. At L237 "they" follows "Your people live", so it briefly reads as humans rather than the enemy. The next sentence recovers it.
- Fix: "the translator rendered"; "She could not say it."; name the enemy in L237 (for example "the ones up there").

### D7 · Minor · Narration explains the line just heard

- Where: L211 (after the pursuer's first broadcast), L401 (final choice)
- Text:
> Heshi's throat membrane tightened.
> The pursuer's voice always sounded reasonable. It had learned to make terror fluent.
> It was not a command, and he did not make the choice easier by pretending otherwise.
- Problem: The reader has just heard the pursuer's fluent menace and Martin's non-command offer, and the narration then explains both. "Throat membrane tightened" is the stock throat-tightening beat moved onto alien anatomy.
- Fix: Keep one of the two L211 sentences at most, or replace the beat with something Heshi does. Cut the L401 sentence or replace it with an action (Martin waits and does not touch the panel until she chooses).

## Prose findings

### P1 · Major · Aftermath re-explains the lesson

- Where: L377 (road silent), L395 (engines start)
- Text:
> Not the old silence humanity had heard before anyone else existed. This silence had people on both sides of it.
> Heshi had expected the oldest people to answer with an ancient power no one else possessed. Instead, they had destroyed it.
- Problem: L201 has already given Heshi's recognition ("a child's version of age"), and D4 covers the Fermi statement. Here the ending movement restates both: a polished emblem about silence and a recap of what she had expected. Together with D4 and D7, the theme is explained about six times.
- Fix: Cut the L377 pair, or reduce it to the fact that the road was silent. Cut L395's first two sentences and keep "What remained sounded heavy, mechanical, embarrassingly slow." The final image (L409–L411) already carries the point and should stay as it is.

### P2 · Minor · "Not X but Y" reversals

- Where: L35, L267, L295, L337, L377, L401
- Text:
> Not a restraint. Warmth.
> Earth answered not with a speech but with changing intervals.
> The burn ran not like fire but like a door closing through a house too large for sound.
- Problem: Six reversals in about 3,400 words. The same template keeps recurring as a way to describe things.
- Fix: Keep one (the L337 door image is the strongest). State the others directly.

### P3 · Minor · "No A. No B." triplet fragments

- Where: L19 (arrival), L183–L185 (burn explanation)
- Text:
> No towers. No guard vessels.
> No branch selection. No rebuilding from the captured stations. No road for the enemy.
- Problem: The same list rhythm is used twice, and the second closes on the echo line "No road for anyone."
- Fix: Recast one of the two lists as a normal sentence. Keep "No road for anyone." only if the list before it is not also a triplet.

### P4 · Minor · Single-sentence paragraphs as the default pulse

- Where: about 40 narration-only single-sentence paragraphs; in calm scenes L17, L21, L65, L71, L119, L137, L143, L145, L155, L157, L165, L171, L177, L185, L191, L203, L205, L229
- Text:
> Darkness made the room large enough.
> Martin stopped moving.
> The translator rendered it perfectly.
- Problem: In the kitchen and planning scenes, almost every narrative beat gets its own line, so the emphasis wears thin. The climax (L313–L369) earns the short paragraphs; the kitchen does not.
- Fix: Merge beats into their neighboring paragraphs in L67–L205 and L371–L407. Leave the climax rhythm alone.

### P5 · Minor · Small staging and referent slips

- Where: L63 (names), L67 (leak), L145 (table map)
- Text:
> He got close enough.
> Martin moved the bucket two finger-widths before he did anything else.
> The oldest living people in the cosmos had given the leak its own towel.
> He pointed to the spindle, then to Earth.
- Problem: "Got close enough" reads as physical approach, but it means his pronunciation. The leak has a bucket, and then the joke gives it a towel that never appeared. "Pointed... to Earth" leaves unclear what he points at (the floor, a counter, the ceiling point).
- Fix: "His third try came close enough."; make the object consistent (bucket, or show the towel); name the counter or point he indicates.

### P6 · Minor · Seawall as incidental texture

- Where: L409, final launch
- Text:
> Beyond the seawall, a blunt human craft rose into the washed-out morning.
- Problem: A seawall is coastal flood-control infrastructure. Under `universe/style-guide.md` "No default water infrastructure", passing texture counts, and the prompt did not ask for it. L19 already calls it "a stone wall".
- Fix: "Beyond the wall" or "Beyond the shingle".

## Continuity and prompt findings

### C1 · Major · What Martin and humanity knew before tonight is never fixed

- Where: L63, L75, L157–L173; the whole first half
- Text:
> “I know that you arrived through a system we're not supposed to have heard from in a very long time.”
> Martin stopped moving.
> “Not yet,” he said.
- Problem: The text points both ways. Martin's lines at the reveal ("We listened. There was nobody." / "Not yet." / "Somebody kept the receivers on.") read as humanity learning tonight that others came later, which would make Heshi the first voice from outside in all of human memory. Yet he greets her with the calm of a routine call-out, knows about "the war" (D1), and has contact protocols ready (L103–L107). L75's "not supposed to have heard from" is vague about whether Earth had heard the road before. So the story's central Fermi moment has no clear knowledge change. The reader cannot tell whether Martin is learning that others exist, learning the dates, or remembering.
- Fix: Choose one state and put it in one plain clause at L75, in Martin's slow translator-friendly speech. Most of the text supports this one: Earth's listeners had heard nothing from the far road in a very long time and did not know it had filled with peoples; tonight is the first arrival. Then make L157's stillness about what Martin is learning (how many came after, and how late), and let Heshi's learning be that the silence was real. One small physical tell of first contact, early on, would help without breaking his dryness. The alternative (humanity knew of the later peoples but stayed apart) also works if L75 says so and L163–L167 are framed as memory. Coordinate with D1 and D4.

### C2 · Minor · The silver sheet was not refused

- Where: L37 (sheet accepted) vs L373 (aftermath)
- Text:
> She took it.
> He wrapped it in the same silver sheet she had refused outside
- Problem: She recoiled and then took it, so "refused" contradicts the page. She would also need to have taken it off for him to wrap his hand in it.
- Fix: "the same silver sheet he had given her outside" (she could hand it to him).

## Recurring patterns

- Martin re-defines Heshi's word: L81, L89, L93, L181, L189, L199, L237. Earned at L81 (answering a garble) and L181 (the burn reveal); thin it at L89–L93 (D5) and L189/L199 (D3). Keep his arc from correcting (first half) to asking (L267, L285, L321).
- Translator garble followed by a Martin quip: L41–L43, L97–L99, L221–L223. The device works; drop the quip only where it does not parse (D5).
- Theme restatement: L161, L169–L171, L173, L377, L395, L401 (D4, P1, D7).
- Hinge pronouns without clear referents: L31, L187, L199, L237 (D3, D6).
- "Not X but Y" reversals: L35, L267, L295, L337, L377, L401 (P2).
- "No A. No B." triplets: L19, L183–L185 (P3).
- Single-sentence narrative paragraphs outside the climax (P4).

## Preserve

- The first-contact garbles and Martin's reply, which answers the nonsense he actually heard:
> The translator told him, “Old mud property. Dependent animals remain in inventory.”
- The humor-as-apology mechanic and its later payoff (L115, L229):
> He was joking. Heshi could tell because the translator marked the sentence as a probable apology, which was how it handled most human humor.
> The apology was direct enough that even the translator left it alone.
- "How many?" / "Worlds?" / "People." (L127–L131) and the wordless war map:
> They built the war between them without another successful sentence.
- The translators exchange (L215–L217) and the kettle rebuke (L221–L227). The chain from garble to grief works, and "I'm sorry" answers her anger, not her words:
> “They took our translators.”
> “My home used kettles while they entered it.”
- Martin without his humor (L267):
> “I need the census,” he said.
> “I don't have a clean way to ask for it.”
- The handed-over decision, and the pursuer's aphorism, which fits the antagonist's register:
> “Now, Heshi?”
> The polished voice said, “You have mistaken uncertainty for permission.”
- The broken transmissions (L339–L343, L363) and the minimal final choice (L397–L411), including "It kept climbing."
- "We listened... There was nobody." and "Not yet." (see D4).

## Suggested edit order

1. C1: decide what Martin knew before tonight; D1 and D4 depend on it.
2. D1: replace "the war" with what Martin can see, and adjust what Heshi catches.
3. D4 with P1: cut the narration restatements around the reveal and in the aftermath, keeping Martin's short lines.
4. D3: make Heshi's intent explicit at the burn decision and replace the inverted "road goes everywhere they do".
5. D2: give Martin an observable cue before he stops the consent question.
6. D5, D6, D7: small dialogue repairs.
7. C2, P2–P6: sweep the sheet contradiction, templates, paragraph pulse, staging slips, and the seawall.
