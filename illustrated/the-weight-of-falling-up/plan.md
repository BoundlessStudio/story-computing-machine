# The Weight of Falling Up — illustrated edition plan

Status: Ready for user plan approval; independent pre-generation review PASS. No user approval or new artwork is claimed.

## Source and visual analysis

Classic web-only edition of the canon bundle `stories/the-weight-of-falling-up-rune-shoes`. Complete read-only inputs: `05-story.md`, `00-prompt.md`, `story.json` and inspected `title-image.jpg`. Preserve complete prose, punctuation, emphasis and scene breaks.

Juni wants qualification and apparent ease. Homemade wind curls give exhilarating flight, but concealed effort, scouring and a refused repair produce asymmetric failure. Cutting power, redrawing the channels and spending a three-breath crown earn recovery and a qualified pass. Images move from tactile ink to open sky, peril and ordinary shoes returning to slate. Dovek remains watchful, not villainous.

Source facts: Juni Wex wears a coat, stockings and scuffed ordinary brown shoes, one water-marked; a cuff stylus draws heel/underside curls. Dovek uses they/them, wears an examination coat and gloves, and carries one sheet. Two unnamed broom candidates and one unnamed rider on a pale winged horse establish standard methods. Places are the slate launch roof/ridge/eave, iron arch with blue streamers and bell, four-pole yellow boundary, and distant tower/city/river landscape. The right curl wears through first; the right crown is drawn only during the fall, loses one point per breath and disappears permanently. Both base curls are repaired. Ink and leather never supply autonomous agency.

Visual proposals: inherit Juni's inspected cover face, dark shoulder-length hair, brown eyes, navy/gold coat, cream layers and dark stockings. Specify right-hand drawing, left-hand support/charging, right-shoe water mark; retained stylus after repair avoids an invented restowing event. Dovek's age, complexion, hair and tailoring below are proposed. Roof arrangements and arch supports are edition geography, not canon. Peers appear once as distinct distant role-readable silhouettes; no invented names or unnecessary identity sheets.

Read `AGENTS.md`, illustrated-create Planner contract, `illustrated/STYLE.md`, `universe/README.md`, binding style guide and foundational rules/premise. No Juni/Dovek/Nine Eaves topical authority entry was found. Respect living-agency and deep-time boundaries without assigning an era or importing unrelated lore. New prose profiles do not reopen this finished source.

## Coverage

Anchors obtained with `python -m pages.illustrated_editions anchors the-weight-of-falling-up`. All blocks survive; ranges summarize coverage, never simultaneous instants.

| Exchange/reveal | Blocks | Treatment |
| --- | --- | --- |
| Standard methods; Juni called and jokes | 0001–0007 | Prose; methods visualized at scene-02's later moment |
| Removed shoes; first drawing | 0008–0012 | scene-01 |
| Charging; Dovek questions omitted crown; three-breath limitation; concealed intent | 0013–0028 | Prose-only; no real crown yet |
| Launch, imbalance, correction and joke | 0030–0041 | Prose-only |
| Unconventional flight beside standard methods | 0042–0044 | scene-02 |
| Bell slap, first scouring, Dovek writes | 0045–0055 | Prose-only |
| Broom's successful count; Juni rejects crown option | 0057–0066 | Prose-only |
| First excessive microburst | 0067–0070 | scene-03 |
| Further corrections, forced smile, nick, failed count | 0071–0077 | Prose-only |
| Dovek's warning/repair offer; Juni inspects | 0078–0087 | scene-04 |
| Refusal, measuring challenge, ragged test, permission | 0088–0096 | Prose-only |
| Racing, delayed brake, asymmetric failure | 0098–0115 | Active consequence in scene-05 |
| Dovek's stop offer | 0116–0117 | scene-05 |
| Recognition, power cut and fall | 0118–0126 | Uninterrupted prose |
| Right repair/crown charging; first two breaths | 0128–0152 | Prose-only setup |
| Third-breath left repair | 0153–0155 | **scene-06 centerpiece** |
| Crown spent, paired recovery and admission | 0156–0167 | Prose-only |
| Peers give room, honest flight, early brake | 0168–0176 | Prose-only |
| Both feet land | 0177 | scene-07 |
| Stumble, jokes, failures, credited recovery, pass | 0178–0200 | Prose-only |
| Conditions, acceptance and sheet handover | 0201–0205 | Prose-only |
| Fading honest flight record | 0206–0209 | scene-08 |

Exact placement anchors and required/absent states are in each scene's registration block.

## Art direction

Default premium anime novel illustration: expressive anatomy, variable-width pen contours, fine hatching, restrained transparent washes and warm paper grain. Navy/slate, cream/ochre, copper, clear blue sky and pale wind; sunny morning persists. No painterly, photographic or 3D drift. The accepted Juni sheet becomes the concrete style anchor for Dovek and both locations, using actual attached pixels. Match line, hatching, wash restraint, texture and stylization, not palette alone. Cover influence is subordinate. Wind is air, never a floor, technological engine or autonomous guide. No reference headings in scenes.

Witch Hat Atelier supplies written high-level inspiration, not an attached original or copied design.

## Reference inventory

Only original image: `source-cover`, inspected `stories/the-weight-of-falling-up-rune-shoes/title-image.jpg`, 864×1536, reused unchanged. Its overhead crown, ornate sole seals and single visible broom are nonliteral cover imagery and excluded from interiors. No source attachments or new originals are missing.

Pilot chain: `source-cover → ref-juni-wex → ref-nine-eaves-launch-roof → scene-06-three-breaths`; pilot also directly attaches Juni. Dovek and arch wait until pilot review passes. Four references, each useful below; no object/state/style sheet. Ordinary props and yellow-boundary geometry belong to scene prompts. Filenames are `references/<ID>.png`, derived from exact names/places. Character headings are exactly Juni Wex and Dovek; each sheet has one identity. Each location is one distinct place in one coherent view.

JSON blocks supply exact registration fields. Every input has a `referenceRoles` entry for `--reference-role`; scene `sceneState` is the UTF-8 `--state-file` text. Maximum three inputs per call, within five.

### ref-juni-wex

Consumers: Both location references, ref-dovek and all eight scenes.

```json
{
  "id": "ref-juni-wex",
  "kind": "character",
  "size": "1024x1536",
  "references": [
    "source-cover"
  ],
  "referenceRoles": {
    "source-cover": "Identity/costume and subordinate style: Juni face, dark hair, brown eyes, navy/gold and cream clothing, ordinary brown shoes. Exclude pose, stylus, active wind, overhead crown, ornate sole seals, title and other figures."
  },
  "prompt": "PNG 1024x1536. One identity reference sheet, heading exactly Juni Wex. Show neutral full-body front and three-quarter rear views plus a concentrated face study. Preserve the inspected cover's youthful androgynous face, dark shoulder-length hair, brown eyes, navy/gold open coat, cream shirt and loose knee-length trousers, dark stockings and scuffed brown lace-up shoes. Propose a pale water mark on the right shoe. Hands empty; plain unmarked heels and soles, no stylus, wind or crown. Establish precise variable-width pen contours, fine hatching, restrained transparent washes, warm paper grain and expressive anime anatomy. Keep cover identity while avoiding painterly blending, photography or 3D gloss."
}
```

### ref-nine-eaves-launch-roof

Consumers: Scenes 01, 03–08; pilot uses distant roofscape only.

```json
{
  "id": "ref-nine-eaves-launch-roof",
  "kind": "location",
  "size": "1536x1024",
  "references": [
    "ref-juni-wex",
    "source-cover"
  ],
  "referenceRoles": {
    "ref-juni-wex": "Primary rendering style only: actual accepted pen contours, hatching, wash restraint, paper texture and anime stylization. No character or sheet layout.",
    "source-cover": "Distant architecture geometry/content and subordinate daylight accents only; not a literal site map. Ignore people, flight, crowns, diagrams and title."
  },
  "prompt": "PNG 1536x1024. One coherent environment view of Nine Eaves launch roof, no montage. Look diagonally across warm dark slate from one downslope corner: a traversable ridge to an eave, western chimney at left, white landing ring on open slate away from the gutter. Beyond lie lower black angled roofs, masonry towers joined by bridges, amber windows, terraced city and a silver river bend. Relative arrangement is proposed edition geography. Sunny morning, blue shadow and copper accents. No people, paper, stylus or wind trails. Exclude the separate iron arch and yellow boundary. Match the accepted Juni sheet's actual pen contours, hatching, restrained washes, paper grain and stylization; no copied figures, labels or painterly/3D drift."
}
```

### ref-dovek

Consumers: Scenes 01, 04, 05 and 08.

```json
{
  "id": "ref-dovek",
  "kind": "character",
  "size": "1024x1536",
  "references": [
    "ref-juni-wex"
  ],
  "referenceRoles": {
    "ref-juni-wex": "Rendering style only: accepted pen contours, hatching, restrained washes, paper texture and stylization. Dovek is a distinct adult; do not borrow Juni identity, costume or name."
  },
  "prompt": "PNG 1024x1536. One identity reference sheet, heading exactly Dovek. Full-body front and three-quarter side views, with one attentive face study. Proposed appearance: androgynous middle-aged adult, deep brown skin, short silver-gray curls, dark eyes and clean-shaven angular face. Long charcoal examination coat with slate-blue lining, simple brass fastening, dark practical clothes, low boots and fitted gloves. Alert, composed posture without menace. Hands empty, no examination sheet, clipboard, stylus, rune or wind. Match the attached accepted Juni sheet's actual pen contours, hatching, restrained transparent washes, warm paper texture and anime stylization. Keep a distinct face and age. No painterly/photographic/3D drift."
}
```

### ref-nine-eaves-high-course-iron-arch

Consumers: Scene 02; resolves gate geometry and flight clearances.

```json
{
  "id": "ref-nine-eaves-high-course-iron-arch",
  "kind": "location",
  "size": "1536x1024",
  "references": [
    "ref-juni-wex",
    "source-cover"
  ],
  "referenceRoles": {
    "ref-juni-wex": "Primary rendering style only, using accepted actual image: pen contours, hatching, wash restraint, paper texture and anime stylization. No figures or sheet layout.",
    "source-cover": "Architectural content/geometry cues and subordinate morning-light accent only: slate/copper towers and height. Ignore people, title, wind, crown and shoe diagrams."
  },
  "prompt": "PNG 1536x1024. One coherent view of the high-course iron arch, a distinct place, not the launch roof or a montage. A tall iron arch stands on a narrow slate rooftop platform with clear stone attachment points, proposed support geography. Blue streamers hang from its upper sides; a small metal bell hangs at top center. Open flight clearance lies beneath it. Lower slate/copper roofs and linked towers establish height. Sunny morning, no people, creatures, wind trails or labels. Do not include the launch ring or yellow boundary. Match the accepted Juni image's pen contours, fine hatching, restrained washes, paper texture and anime stylization; cover geometry is subordinate, never painterly or 3D."
}
```

## Illustration plan

Right/left means Juni's anatomy. One instant/image, no captions. Scene paths: `illustrations/<ID>.png`.

### scene-01-ink-before-flight

```json
{
  "id": "scene-01-ink-before-flight",
  "kind": "illustration",
  "size": "1536x1024",
  "references": [
    "ref-juni-wex",
    "ref-dovek",
    "ref-nine-eaves-launch-roof"
  ],
  "referenceRoles": {
    "ref-juni-wex": "Identity/costume/style: accepted Juni; plain shoe geometry only. Scene supplies ink/wind/props. Exclude sheet headings/layout.",
    "ref-dovek": "Dovek identity/costume/style; scene supplies paper/gesture. Exclude headings/layout.",
    "ref-nine-eaves-launch-roof": "Roof geography/materials; adapt camera, preserve visible fixtures. No transient state."
  },
  "sceneState": "b0011–b0012, first right-shoe curl complete but not charged. Both shoes removed; both stockinged feet on slate. Right shoe heel-up across knee, left hand steadying it, right hand with stylus. Left shoe nearby unmarked. Dovek crouches opposite. No wind, glow, crown or later gloved tap. Ring and peers outside crop.",
  "after": "b0012-a29337136b27",
  "layout": "inline",
  "alt": "Juni draws a black curl on a removed brown shoe while Dovek watches; both stockinged feet rest on slate.",
  "caption": "",
  "prompt": "PNG 1536x1024. Juni finishes the first wet black curl on the removed right shoe, before magic activates. Both stockinged feet rest on slate; right shoe lies heel-up across one knee, left hand steadying it, right hand holding one blunt-nib stylus at the finished stroke. The left shoe nearby is unmarked. Dovek crouches opposite watching, hands relaxed. Three simple connected strokes pass around heel and under toward arch, not ornate sole seals. No crown or wind. Medium-wide seated-height three-quarter camera angled down enough to show both feet, shoe, hands and Dovek's face. Shoe fills about one-fifth of width. Crop out ring and peers. Match accepted identities and pen-and-wash anime rendering; no labels."
}
```

### scene-02-handwritten-winds

```json
{
  "id": "scene-02-handwritten-winds",
  "kind": "illustration",
  "size": "1536x1024",
  "references": [
    "ref-juni-wex",
    "ref-nine-eaves-high-course-iron-arch"
  ],
  "referenceRoles": {
    "ref-juni-wex": "Identity/costume/style: accepted Juni; plain shoe geometry only. Scene supplies ink/wind/props. Exclude sheet headings/layout.",
    "ref-nine-eaves-high-course-iron-arch": "Gate geometry, bell, blue streamers, support and tower scale. Same rendering; no ring or yellow boundary."
  },
  "sceneState": "b0042–b0044, Juni approaches arch after correcting first roll. Both curls intact, matched narrow streams, no crown; stylus in cuff, hands empty. First broom banks through arch, second rises upright separately, pale horse higher with wings newly spread and rider in mane. Exactly two brooms and one mount. Bell untouched; no later wear or failure.",
  "after": "b0044-79d6c8a6162a",
  "layout": "inline",
  "alt": "Juni approaches the iron arch on two heel jets beside two broom candidates and a rider on a winged pale horse.",
  "caption": "",
  "prompt": "PNG 1536x1024. Juni approaches the blue-streamered iron arch, full body level after recovering the roll, empty arms balancing, heels swept behind and two matched narrow wind streams trailing. Intact simple curls, no crown. Juni large at right; arch at left. Behind and above, separate readable silhouettes show one pupil banking on a broom, another rising upright with both hands on a level broom, and higher one rider holding a pale winged horse's mane. Exactly two brooms, one horse with two feathered wings. Plain navy peer coats, no readable faces. Each broom spans at least 20% width, horse wings 25%. Bell untouched. Keep silhouettes separated by sky. Match accepted rendering; no labels."
}
```

### scene-03-stationary-bursts

```json
{
  "id": "scene-03-stationary-bursts",
  "kind": "illustration",
  "size": "1024x1536",
  "references": [
    "ref-juni-wex",
    "ref-nine-eaves-launch-roof"
  ],
  "referenceRoles": {
    "ref-juni-wex": "Identity/costume/style: accepted Juni; plain shoe geometry only. Scene supplies ink/wind/props. Exclude sheet headings/layout.",
    "ref-nine-eaves-launch-roof": "Distant school roofscape/material continuity only. The yellow boundary is separate airspace between neighboring roofs; do not copy launch roof floor or ring."
  },
  "sceneState": "b0070, first stationary count: right microburst kicks Juni too far after left burst. One live RIGHT jet, black flecks; left output absent, earlier trace detached if shown. Right edge shedding but no later gray nick yet. Both shoes worn, no crown, broad plume or stylus in hand. Four poles/ribbons enclose empty air, no platform. Dovek/peers outside crop.",
  "after": "b0070-6325223a3c15",
  "layout": "inline",
  "alt": "Inside four yellow ribbons, Juni tilts as a right-heel burst throws pale wind and black ink flecks.",
  "caption": "",
  "prompt": "PNG 1024x1536. Freeze Juni's excessive right-heel microburst inside the stationary boundary. Whole body cants off balance, right heel down and inward. One short live pale jet exits the anatomical RIGHT heel with black ink flecks; left heel inactive, optional earlier wisp clearly detached. No later gray nick or crown. Empty arms counterbalance. Slightly elevated three-quarter camera reveals four yellow ribbons as one horizontal square in perspective, four slender supporting poles anchored on neighboring roofs. Empty air beneath Juni, no floor. Ribbons avoid face and feet; body occupies two-thirds of height. Keep jet origin clear and flecks visible as a cluster. Match accepted rendering; no count text."
}
```

### scene-04-repair-offer

```json
{
  "id": "scene-04-repair-offer",
  "kind": "illustration",
  "size": "1536x1024",
  "references": [
    "ref-juni-wex",
    "ref-dovek",
    "ref-nine-eaves-launch-roof"
  ],
  "referenceRoles": {
    "ref-juni-wex": "Identity/costume/style: accepted Juni; plain shoe geometry only. Scene supplies ink/wind/props. Exclude sheet headings/layout.",
    "ref-dovek": "Dovek identity/costume/style; scene supplies paper/gesture. Exclude headings/layout.",
    "ref-nine-eaves-launch-roof": "Roof geography/materials; adapt camera, preserve visible fixtures. No transient state."
  },
  "sceneState": "b0087, after repair-pause offer, before refusal and ragged test pulse. Airborne Juni raises right heel to inspect pale narrow nick. Dovek on ridge, sheet under arm, looks at heel. Left heel low stream supports brief transitional hover (staging inference); right inactive. No repair, crown, full break, test pulse, rescue contact or held stylus.",
  "after": "b0087-7d747ca09e12",
  "layout": "inline",
  "alt": "Juni raises a worn right heel beside the eave while Dovek watches from the ridge with the sheet under one arm.",
  "caption": "",
  "prompt": "PNG 1536x1024. Juni briefly hovers beside the eave and raises the right heel to inspect its pale narrow nick. Left leg extends downward with a thin supporting stream; right knee raised, ankle turned to expose the damaged outer heel. Arms empty and balancing. Dovek stands securely on the ridge opposite, examination sheet under one arm, watching the heel. No catch or contact. Right shoe emits no wind yet; later test pulse has not happened. No crown or stylus action. Side three-quarter view at heel height keeps whole airborne body, Dovek's supported feet and eave separation readable. Shoe about 15% width. Match accepted rendering. No readable text."
}
```

### scene-05-one-sided-fall

```json
{
  "id": "scene-05-one-sided-fall",
  "kind": "illustration",
  "size": "1024x1536",
  "references": [
    "ref-juni-wex",
    "ref-dovek",
    "ref-nine-eaves-launch-roof"
  ],
  "referenceRoles": {
    "ref-juni-wex": "Identity/costume/style: accepted Juni; plain shoe geometry only. Scene supplies ink/wind/props. Exclude sheet headings/layout.",
    "ref-dovek": "Dovek identity/costume/style; scene supplies paper/gesture. Exclude headings/layout.",
    "ref-nine-eaves-launch-roof": "Roof geography/materials; adapt camera, preserve visible fixtures. No transient state."
  },
  "sceneState": "b0116–b0117, Dovek's raised stop hand BEFORE power cut. Both heels swung ahead; RIGHT curl broken to bare leather, no right output. LEFT alone blasts reverse jet forward; right shoulder drops into rightward corkscrew. Stylus in cuff, no repair/crown/plume. Dovek securely at edge, casting nothing. No crash, injury or rescue contact.",
  "after": "b0117-877e94f5c3df",
  "layout": "inline",
  "alt": "Juni corkscrews as only the left heel blasts wind forward; Dovek raises a gloved hand from the roof edge.",
  "caption": "",
  "prompt": "PNG 1024x1536. Juni corkscrews rightward during the failed reverse brake, full body diagonal, anatomical right shoulder dropping and both heels swung ahead. Only LEFT heel blasts a narrow jet forward; RIGHT heel silent with bare-brown gap in its outer curl. Separate live origin clearly from the other shoe. Alarmed face, flying hair, off-axis hips; no duplicate limbs or montage. Dovek stands at the separated midground roof edge, one gloved hand raised for the declared stop, casting nothing. Slightly elevated side camera shows both shoes, ridge and lower rooftops. Juni fills roughly 65% height; raised-arm silhouette remains visible. No crown, broad plume or diagram arrows. Match accepted rendering."
}
```

### scene-06-three-breaths

```json
{
  "id": "scene-06-three-breaths",
  "kind": "illustration",
  "size": "1024x1536",
  "references": [
    "ref-juni-wex",
    "ref-nine-eaves-launch-roof"
  ],
  "referenceRoles": {
    "ref-juni-wex": "Identity/costume/style: accepted Juni; plain shoe geometry only. Scene supplies ink/wind/props. Exclude sheet headings/layout.",
    "ref-nine-eaves-launch-roof": "Distant lower roofscape/materials and height only, not a literal camera map. Do not transplant ring, roof floor or examiner into foreground."
  },
  "sceneState": "End b0155 during held THIRD breath, before final point vanishes. RIGHT curl repaired/charged, leg extended below, exactly ONE remaining crown point above right heel. Broad plume only from right heel bends beneath center; descent continues. LEFT heel pulled near torso, repair freshly completed: left hand supports, thumb presses wet line; right hand single stylus nib lifted. Both shoes worn. No left output, paired jets, restored crown, overhead crown, platform, steering or rescue.",
  "after": "b0155-35b63c9308a3",
  "layout": "full-page",
  "alt": "Juni presses a thumb to the repaired left shoe while the last point above the right heel feeds a broad plume over distant roofs.",
  "caption": "",
  "prompt": "PNG 1024x1536. During Juni's held third breath, LEFT hand supports the still-worn left shoe near the torso, thumb pressing its freshly finished wet repair. RIGHT hand holds one stylus with nib lifted, not drawing beneath the thumb. Left knee flexes outward, ankle brought across near torso; body diagonally reclines while opening from tuck. RIGHT leg extends below; exactly ONE remaining bright crown point sits above its heel curl. One broad plume flows from RIGHT heel inward beneath center, resisting descent; no left jet. Close three-quarter side view sees face, thumb contact, distinct legs and plume origin. Full figure 70% height; distant roofs occupy bottom quarter. Left shoe at least 14% width. No inset or overhead crown. Match accepted pen-and-wash rendering."
}
```

### scene-07-inside-the-ring

```json
{
  "id": "scene-07-inside-the-ring",
  "kind": "illustration",
  "size": "1536x1024",
  "references": [
    "ref-juni-wex",
    "ref-nine-eaves-launch-roof"
  ],
  "referenceRoles": {
    "ref-juni-wex": "Identity/costume/style: accepted Juni; plain shoe geometry only. Scene supplies ink/wind/props. Exclude sheet headings/layout.",
    "ref-nine-eaves-launch-roof": "Roof geography/materials; adapt camera, preserve visible fixtures. No transient state."
  },
  "sceneState": "b0177, both shoes JUST landed inside ring, after power cut, before three stumbling paces. Both soles touch same slate plane, knees flex, arms balance. Base curls whole, crown gone. NO active wind or glow; residual trails detached only. Stylus lightly retained right hand, no drawing. No sitting, catch, pass sheet or trophy.",
  "after": "b0177-734dfe02e884",
  "layout": "inline",
  "alt": "Juni lands with both shoes inside the white ring, knees bending and arms spread, heel winds extinguished.",
  "caption": "",
  "prompt": "PNG 1536x1024. Both ordinary brown shoes have just touched slate inside the white ring. Juni's knees bend, body pitches slightly forward and arms spread before the coming stumble; face breathless and disbelieving. Full body and both foot contacts clearly visible. Power is already cut: no jet, plume or glow. Repaired curls remain; crown entirely absent. Small stylus loosely retained in right hand, no new action. Low three-quarter roof view shows the elliptical ring enclosing BOTH feet with surrounding slate. Ridge, chimney and city stay secondary. Do not demand visible undersides of flat-planted soles. No examiner catch or pass sheet. Match accepted rendering; no labels."
}
```

### scene-08-honest-record

```json
{
  "id": "scene-08-honest-record",
  "kind": "illustration",
  "size": "1536x1024",
  "references": [
    "ref-juni-wex",
    "ref-dovek",
    "ref-nine-eaves-launch-roof"
  ],
  "referenceRoles": {
    "ref-juni-wex": "Identity/costume/style: accepted Juni; plain shoe geometry only. Scene supplies ink/wind/props. Exclude sheet headings/layout.",
    "ref-dovek": "Dovek identity/costume/style; scene supplies paper/gesture. Exclude headings/layout.",
    "ref-nine-eaves-launch-roof": "Roof geography/materials; adapt camera, preserve visible fixtures. No transient state."
  },
  "sceneState": "b0206–b0209 after pass, conditions and sheet handover. Juni seated, sheet left hand on lap, retained stylus right hand beside thigh. Dovek nearby crouched, continuing last stated posture (staging proposal). Worn shoes dusty, base curls whole, crown absent, power off. Only detached fading wind traces: knot at yellow square, lower corkscrew, broad bloom below, paired ribbons to landing roof. One present vista, no replay figures or new flight.",
  "after": "b0209-9846dc11dd84",
  "layout": "inline",
  "alt": "Juni holds the sheet beside Dovek and looks out at fading tangled winds, a broad bloom and two clean ribbons reaching the roof.",
  "caption": "",
  "prompt": "PNG 1536x1024. Juni sits on slate with examination sheet in left hand over lap and stylus loosely beside right thigh. Dovek crouches nearby at the ring edge. Quiet three-quarter backs and partial profiles face the route; preserve enough of Juni's relieved face. Shoes dusty, crown gone, all power off. Beyond the eave show detached fading traces: small ragged knot near distant yellow boundary, lower corkscrew, broad pale bloom beneath, and two clean ribbons arriving side by side toward the roof. One present landscape, never solid tracks, arrows or replay figures. Seated figures lower 40%; clean ribbons dominant, older traces subtle. Paper marks indistinct. Match accepted morning rendering. No labels."
}
```

## Presentation and counts

Classic: **4 references (2 character, 2 location), 8 interiors, 1 unchanged reused cover, 0 new covers**. No PDF requested. Counts describe coverage, not attempt limits or generation budgets.

After actual plan approval: Juni sheet → launch roof → shared-header layout/input review → centerpiece → actual desktop/mobile pilot review. Then Dovek and arch references, complete reference review, remaining scenes in story order. Inspect accepted pixels before dependent calls; changed dependencies invalidate affected reviews.

Current CSS feasibility, supplied by coordinator: reader max 960px, Classic prose 65ch; mobile padding 20px yields approximately 335px art width at 375px viewport and 280px at 320px. Full-width images, no fine-action spots. Portrait pilot preserves body/contact and distant roofs; 14%-width repair shoe gives roughly 39–47px mobile. Inspect thumb/nib distinction, final crown point, single plume origin and depth in actual layout. These are estimates, not unseen pixel approval. `full-page` adds web spacing, not wider art.

Use Source Serif/Source Sans, selectable unchanged prose, preserved scene breaks and proportional uncropped images. Early and final readers share Pages branding, Library, theme control, repository link and local navigation, with styles scoped to reading area. Replace existing `stories/the-weight-of-falling-up-rune-shoes.html` and its one Library card, preserving metadata, title, canon, order and count. Keep catalog/source intact. Display exact stored Writing Prompt as escaped literal text before prose, including historical wording; do not replace it with edition instructions. No second card, original-reader self-link or PDF link.

## Pre-generation findings and repairs

Planner preflight considered every brief and dependency: source instant/placement, feasible body/hand/sightline, object counts, transient state bias and CSS reading scale.

- Removed cover crown/ornate diagrams from reusable sheets. Plain identity shoes cannot import a later repair state.
- Opening keeps both shoes removed and ink inactive; microburst shows flecks before nick; offer precedes ragged test; failure has left output only.
- Pilot uses exactly one last RIGHT crown point, right leg extended and right-only plume. Left thumb charges finished repair while right stylus lifts; no impossible simultaneous nib/thumb contact or left jet.
- Landing has power off and both contacts visible, without demanding hidden sole views. Ending winds are detached residue, not simultaneous replay.
- Prop sheets omitted; both locations explicitly attach accepted character rendering, with figure content excluded. Every reference has a consumer.

Independent pre-generation review: **PASS**, reviewer `/root/plan_review`. The reviewer independently read the complete source and prompt, inspected the original cover, and checked all twelve assets against their exact registered manifest fields (maximum three references), source states/anchors, reference utility/style dependencies and CSS reading sizes. Pilot b0155 passed with one remaining right crown point, right-only broad plume and separated thumb/nib contact; scene-04's explicitly brief transitional left thrust was compatible. No actionable findings or repairs required. This clears proposed briefs and dependencies only; no new artwork, generated-pixel certification or user approval is claimed.
