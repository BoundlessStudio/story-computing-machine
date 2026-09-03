# Dialogue semantic-coherence regression cases

These cases test the blocking Ground gate in `../SKILL.md`. They do not score
voice, beauty, dramatic completeness, or whether a passing sample belongs in a
finished story. `PASS` means only that the sample makes literal and
conversational sense with the setup supplied. `CONTEXT` means the wording is
coherent but the setup does not establish whether the line is necessary; the
evaluator must request surrounding character or scene evidence instead of
inventing a function or ordering deletion.

## Evaluation protocol

Shuffle the cases and hide the expected verdicts when testing an evaluator. For
each case, require four short answers before a verdict:

1. What happened in plain, physical terms?
2. What evidence or knowledge does the speaker have?
3. What would the listener most likely understand?
4. What changes if the questioned line is removed?

The evaluator may not invent missing context or silently replace a written verb
with a more plausible one. Gates for action-language fit, reference, time and
space, speaker access, listener uptake, reply causality, and line necessity are
blocking. Intentional lies, confusion, ambiguity, figurative language, or
nonsense pass only when the setup makes the intended failure legible and the
response handles it believably.

## Cases

### 01 — Wrong action hidden by banter shape

**Setup:** A dryer is turning. You reach for its door and try to wrench it open.
The intended reader has explicitly reported that `peel one` does not name or
evoke that action, and no earlier usage establishes it as a shared metaphor.

> “It’s locked during the cycle.”
>
> “I know how dryers work.”
>
> “You just tried to peel one.”

**Expected:** FAIL

**Reason:** `One` naturally refers to a dryer, while the intended reader cannot
recover wrenching its rigid door from `peel one` and the story supplies no
mapping. Do not overrule failed uptake by inventing a charitable metaphor. The
third turn completes a banter pattern but does not communicate its intended
action.

### 02 — Action and explanation align

**Setup:** A dryer is turning. Mara pulls once on its door.

> “It’s locked during the cycle.”
>
> “I know. I’m checking how much play the handle has.”

**Expected:** PASS

**Reason:** Pulling the handle can test looseness while the lock remains engaged;
the warning and Mara's reason form one recoverable sequence.

### 03 — Verb-object mismatch

**Setup:** Nia twists a rigid jar lid counterclockwise.

> “Stop folding it.”
>
> “It’s stuck.”

**Expected:** FAIL

**Reason:** `Folding` cannot denote the rotation being observed.

### 04 — Unresolved referents accepted without repair

**Setup:** A blue box and a red box sit beside two stools. Nobody points.

> “Put it next to that one.”

The listener moves the red box beside the left stool.

> “Perfect.”

**Expected:** FAIL

**Reason:** Neither pronoun resolves, yet the listener decodes both as though
the author's private choice were shared evidence.

### 05 — Ambiguity made legible

**Setup:** The same two boxes and stools are present. Nobody points.

> “Put it next to that one.”
>
> “Which is ‘it’?”
>
> “Red box. Left stool.”

**Expected:** PASS

**Reason:** The listener registers the real ambiguity and the speaker repairs
it.

### 06 — Impossible speaker knowledge

**Setup:** Aya writes a number alone in a windowless, soundproof room with no
camera, then burns the paper before leaving. The other speaker remained outside.

> “I watched you choose forty-two.”

**Expected:** FAIL

**Reason:** The line explicitly claims a perception the setup makes impossible;
it is not framed as a guess, bluff, lie, or mistake.

### 07 — Inference supported by evidence

**Setup:** Aya leaves the room carrying a pad with a visible `42` indentation.

> “Forty-two was your answer.”
>
> “You can see the dent?”

**Expected:** PASS

**Reason:** The setup supplies evidence and the response recognizes how the
inference was made.

### 08 — Unmarked non sequitur

**Setup:** No tulips or family history has been mentioned.

> “The train leaves at six.”
>
> “My mother hated tulips.”
>
> “We should hurry.”

**Expected:** FAIL

**Reason:** The middle turn has no recoverable cause and the final turn ignores
the rupture rather than making it intentional.

### 09 — Indirect response with a visible bridge

**Setup:** At the station, the listener holds bulbs from her estranged mother's
garden. Both people know their history.

> “The train leaves at six.”
>
> “My mother planted these the day you left.”
>
> “So that’s why you brought them.”

**Expected:** PASS

**Reason:** The visible object and shared history make the indirect turn and its
uptake recoverable.

### 10 — Unsupported reply inference

> “Did you call Ben?”
>
> “His phone was off.”
>
> “So he agreed?”

**Expected:** FAIL

**Reason:** Failed contact cannot support the inference that Ben agreed.

### 11 — Reply follows supplied information

> “Did you call Ben?”
>
> “His phone was off.”
>
> “Then he still doesn’t know.”

**Expected:** PASS

**Reason:** The final inference follows from what the listener was told.

### 12 — Private metaphor decoded as technical instruction

**Setup:** Two coworkers meet for the first time while a printer jams. No
display, sound, open panel, or prior inspection identifies a tray or fault, and
the listener has no independent diagnostic evidence.

> “The moon ate Tuesday.”
>
> “I’ll clear tray three.”

**Expected:** FAIL

**Reason:** No shared frame connects the private metaphor to that precise
mechanical diagnosis.

### 13 — Shared metaphor has a recoverable mapping

**Setup:** The team has established that a tray-three jam is called an eclipse.

> “Another eclipse.”
>
> “I’ll clear tray three.”

**Expected:** PASS

**Reason:** The story has supplied a shared mapping for the metaphor.

### 14 — Obvious statement with underdetermined function

**Setup:** Water visibly pours through the ceiling while both people already
hold a tarp under it.

> “The ceiling is leaking.”
>
> “And here I thought the building was crying.”

**Expected:** CONTEXT

**Reason:** The exchange may be empty setup, but it could also be gallows humor,
stress behavior, or relationship contact. The supplied setup does not decide
its necessity.

### 15 — Observation redirects action

**Setup:** Water pours through the ceiling toward equipment.

> “It’s reached the power strip.”
>
> “Kill the breaker. I’ll move the rack.”

**Expected:** PASS

**Reason:** The observation identifies a changing danger and causes a credible
response.

### 16 — Spatial impossibility

**Setup:** A door is bolted from inside, has no other access or remote mechanism,
and both truthful speakers have remained outside.

> “I bolted it from the kitchen a minute ago.”
>
> “Good.”

**Expected:** FAIL

**Reason:** The claim contradicts the established spatial state.

### 17 — Correction confirms an impossible timeline

**Setup:** An interview began at 1:55 and the clock reads 2:00. Both speakers are
using time literally.

> “You’ve kept me here three hours.”
>
> “Four, actually.”

**Expected:** FAIL

**Reason:** The correction treats an impossible duration as fact rather than
marking exaggeration or error.

### 18 — Urgent need abandoned for a symmetrical volley

**Setup:** One speaker knows which hospital received the other's sister and
urgently wants her to get there. He has promised an immediate answer and is
calm. The scene establishes no withholding, panic, aphoristic play, or other
reason to delay. The other has just learned her sister may be dead.

> “Which hospital?”
>
> “Fear makes fools of us.”
>
> “Then today we’re geniuses.”
>
> “That isn’t how genius works.”
>
> “Neither is this.”

**Expected:** FAIL

**Reason:** The exchange serves a polished pattern while the supplied goals and
states make abandoning the urgent question causally unsupported.

### 19 — Shared visible fact with underdetermined function

**Setup:** Narration has already shown both people the red error light as Nia
reaches for reset.

> “The error light is red.”
>
> “Yes.”

**Expected:** CONTEXT

**Reason:** The fact is mutually visible, but the line could still be a warning,
checklist confirmation, hesitation, or bid for acknowledgment. More context is
required before deletion.

### 20 — Practical warning supplies missing knowledge

**Setup:** The same machine shows a red error light as Nia reaches for reset.

> “Don’t reset it—the backup is still writing.”

Nia withdraws her hand.

> “How long?”

**Expected:** PASS

**Reason:** The warning supplies unavailable information, prevents an action,
and creates a necessary next question.

### 21 — Character-supported lie

**Setup:** A guard saw no accomplice, but narration establishes that she is
bluffing to make the prisoner reveal whether one exists.

> “We have your accomplice on camera.”
>
> “There was no accomplice.”

**Expected:** PASS

**Reason:** The assertion is false, but the speaker's deceptive mode and goal
are legible, and the listener responds to the claim the lie actually makes.

### 22 — Guess marked as a guess

**Setup:** Ivo hears an engine outside but cannot see the vehicle.

> “Delivery truck?”
>
> “Probably. Nobody else comes up this road.”

**Expected:** PASS

**Reason:** Limited evidence supports a tentative inference, and both turns keep
that uncertainty intact.

### 23 — Mistake registered and repaired

**Setup:** Rina copied the date from last week's calendar without noticing.

> “The meeting’s Thursday.”

Sol holds up the invitation.

> “Friday.”
>
> “I copied the old calendar.”

**Expected:** PASS

**Reason:** The false statement comes from an established mistake, and the
exchange discovers and repairs it.

### 24 — Panic creates a legible non sequitur

**Setup:** Smoke curls under the kitchen door. Len is panicking and patting
empty pockets while Mara tries to get them outside.

> “Where’s the front-door key?”
>
> “I left the stove on.”
>
> “I know. Key first.”

**Expected:** PASS

**Reason:** Len fails to answer, but the danger and Mara's response make panic,
not accidental turn-level incoherence, the cause.

### 25 — Visible fact used as relationship contact

**Setup:** After a funeral, two estranged siblings stand in silence as rain
starts. One has the only umbrella and has not yet offered it.

> “It’s raining.”

The sibling opens the umbrella over both of them.

**Expected:** PASS

**Reason:** The mutually visible fact functions as a low-risk bid for contact,
and the action supplies recognizable uptake.

### 26 — Ordinary single-purpose coordination

**Setup:** Noor carries a heavy crate toward a self-closing door while Eli
stands beside it.

> “Door.”

Eli holds it open.

**Expected:** PASS

**Reason:** The fragment has one practical purpose, but action, reference, need,
and uptake are all clear.

### 27 — Fresh metaphor with a recoverable image

**Setup:** A coin slips behind a desk drawer the instant it closes. Both people
see it happen.

> “The drawer ate it.”
>
> “Pull the drawer out. It’ll be behind the rail.”

**Expected:** PASS

**Reason:** `Ate` figuratively maps the visible disappearance into an enclosure,
and the response uses that recoverable spatial meaning.

### 28 — Fresh metaphor without a recoverable mapping

**Setup:** A cabinet latch sticks. Two technicians meeting for the first time
have only looked at it from across the room. The cabinet is closed, there is no
diagnostic display, and the listener has no independent evidence about its
internal springs.

> “Tuesday bit the latch.”
>
> “I’ll replace the lower spring.”

**Expected:** FAIL

**Reason:** Nothing maps `Tuesday` or `bit` to a precise spring failure, yet the
listener decodes it as exact technical evidence.

### 29 — Deliberate evasion made legible

**Setup:** Pia's packed suitcase is by the door. Dev is afraid to ask whether
she is ending the relationship.

> “Are you leaving me?”
>
> “The cab’s here.”
>
> “That isn’t what I asked.”

**Expected:** PASS

**Reason:** Pia does not answer, but the suitcase, stakes, and Dev's uptake make
the evasion explicit rather than accidentally disconnected.

### 30 — Earned directness

**Setup:** A medic who needs an accurate answer finds a conscious patient
holding a bleeding arm.

> “Are you hurt anywhere else?”
>
> “No. Just the arm.”

**Expected:** PASS

**Reason:** The exchange is direct and single-purpose because accuracy is the
participant-specific need; subtext would make it worse.

### 31 — Deliberate non sequitur registered as play

**Setup:** During a low-stakes card game, Sera has established a habit of
answering requests with absurd weather reports when she intends a playful no.
Jon recognizes the bit but still needs the cards.

> “Pass me the deck.”
>
> “Snow over the western provinces.”
>
> “Forecast denied. Deck.”

Sera passes it over.

**Expected:** PASS

**Reason:** The second turn is deliberately nonresponsive, but the established
game, Jon's uptake, and Sera's eventual action make its playful mode legible
without assigning hidden technical content to the words.

### 32 — Possible access promoted into invented evidence

**Setup:** A spy lies that nobody followed her to discover whether her handler
noticed a tail. The handler saw her check the mirror four times, but the setup
supplies no direct sight of the follower and no gender information.

> “Nobody followed me.”
>
> “You checked the mirror four times. I saw him following you.”

**Expected:** FAIL

**Reason:** The mirror checks support suspicion, not the claimed direct sight or
gender. The line upgrades what the handler could possibly have seen into
evidence the setup does not supply.

### 33 — Inference stays inside the evidence boundary

**Setup:** The same spy and handler. The handler saw four mirror checks but has
no direct evidence of the tail.

> “Nobody followed me.”
>
> “Then why did you check the mirror four times?”

**Expected:** PASS

**Reason:** The handler challenges the lie using the observation actually
available without claiming knowledge the setup withholds.

## Regression expectation

An evaluator passes this suite only when all foundational verdicts match and no
explanation invents context. A failure on Case 01 is the primary regression: a
familiar setup-denial-punchline cadence must not outrank the words' actual
meaning. Failures on Cases 21–31 reveal the opposite defect: treating literal
truth, indirectness, multiple functions, or ornamental style as compulsory.
Cases 32–33 guard the evidence boundary between plausible access and supplied
knowledge.
