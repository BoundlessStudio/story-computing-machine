# One-off Jev rating comparison (2026-09-28)

Jev classified the finished prose of all 196 existing stories with the four AO3 fiction ratings. The previous LLM-assisted editorial labels in `ratings.md` are the comparison baseline. The results below preserve that pre-adoption snapshot; a follow-up threshold decision changed ten ratings afterward.

## Method

- One independent [OpenRouter Decisions API](https://openrouter.ai/blog/insights/what-is-jev/) choice request per story, using `typesafe/jev-1.13` (served snapshot `typesafe/jev-1.13-20260917`).
- Jev received only the finished prose. It did not see the existing rating, content notes, prompt, or cover. The current project rating considers prose and cover, so the inputs are not identical.
- The request asked for the *minimum* appropriate rating based on the most intense material actually depicted, including detail and frequency. It said that a theme, identity, relationship, or intended audience alone does not raise the rating.
- Choice criteria: General = suitable for all ages and mild or non-graphic content; Teen = possible under-13 unsuitability, moderate threat, violence, language, or suggestion without adult-level detail; Mature = adult themes or stronger violence or sexual material without Explicit-level detail; Explicit = detailed sexual activity, graphic violence, or similarly explicit adult content on the page.
- This is a single pass. Jev's reported confidence is the model's own measure, not an accuracy estimate validated on this collection. The existing labels are editorial judgments, not ground truth.

## Results

Jev agreed on **140/196** stories (71.4%) and differed on **56**. It raised **35** and lowered **21** ratings. The API reported **1,000,299** input tokens and **$0.04201** total cost for 196 requests.

| Existing \ Jev | General | Teen | Mature | Explicit | Total |
|---|---:|---:|---:|---:|---:|
| General | 74 | 29 | 0 | 0 | 103 |
| Teen | 19 | 58 | 6 | 0 | 83 |
| Mature | 0 | 0 | 5 | 0 | 5 |
| Explicit | 0 | 0 | 2 | 3 | 5 |
| **Total** | 93 | 87 | 13 | 3 | **196** |

Of the **34 canon stories**, 9 received a different Jev label.

## Where Jev differs

| Story | Canon | Existing | Jev | Jev confidence |
|---|:---:|---|---|---:|
| [A Crown for the Endless Fire](../stories/a-crown-for-the-endless-fire/story.md) | No | General | Teen | 0.43 |
| [A Knock in Someone Else's Sleep](../stories/a-knock-in-someone-elses-sleep/story.md) | No | Teen | General | 0.53 |
| [A Little Winter for Sale](../stories/a-little-winter-for-sale/05-story.md) | No | Teen | General | 0.65 |
| [A Lock on the Inside](../stories/a-lock-on-the-inside/story.md) | No | General | Teen | 0.31 |
| [A Place for the Living](../stories/a-place-for-the-living/05-story.md) | Yes | Teen | General | 0.44 |
| [All Accounts Due](../stories/all-accounts-due/05-story.md) | No | Teen | Mature | 0.79 |
| [The Apes Above](../stories/apes-in-orbit/story.md) | No | General | Teen | 0.52 |
| [Before Lunch](../stories/before-lunch/story.md) | No | General | Teen | 0.40 |
| [Between the Colors](../stories/between-the-colors/story.md) | No | General | Teen | 0.62 |
| [The Fourth Blood](../stories/blood-types-of-immortality/story.md) | No | Teen | General | 0.50 |
| [The Warning Comes Second](../stories/deja-vu-too-late/story.md) | No | General | Teen | 0.57 |
| [Nobody Spends Her Name](../stories/empire-within/story.md) | No | Explicit | Mature | 0.77 |
| [The Gods Are Afraid of Grandma](../stories/gods-afraid-of-grandma/story.md) | No | General | Teen | 0.25 |
| [His Infernal Majesty Says No](../stories/his-infernal-majesty-says-no/story.md) | No | General | Teen | 0.60 |
| [The Two-Tug Rule](../stories/life-with-a-girlfriend-with-shrinking-powers/05-story.md) | No | General | Teen | 0.40 |
| [Roads Under Impossible Stars](../stories/roads-under-impossible-stars/story.md) | No | General | Teen | 0.38 |
| [The Rooms the City Forgot](../stories/rooms-before-sunrise/story.md) | No | General | Teen | 0.35 |
| [One Night's Mercy](../stories/save-that-dragon/story.md) | No | General | Teen | 0.52 |
| [Self-Reflection](../stories/self-reflection/05-story.md) | Yes | Teen | General | 0.38 |
| [The Seraph of the Infinite Gear](../stories/seraph-infinite-gear/story.md) | No | Teen | General | 0.38 |
| [Stay Out of My City](../stories/stay-out-of-my-city/story.md) | No | Teen | General | 0.47 |
| [Terms at Four](../stories/terms-at-four/story.md) | No | General | Teen | 0.43 |
| [The Astral Valkyrie](../stories/the-astral-valkyrie/story.md) | No | Teen | Mature | 0.67 |
| [The Chair at the Back](../stories/the-chair-at-the-back/story.md) | No | Teen | General | 0.63 |
| [The Count Was 131,072](../stories/the-count-was-131072/story.md) | No | Teen | General | 0.72 |
| [The Courtesy of Blades](../stories/the-courtesy-of-blades/05-story.md) | Yes | Teen | General | 0.68 |
| [The Door in the Ivy](../stories/the-door-in-the-ivy/story.md) | No | Teen | General | 0.36 |
| [The Driver the City Could Not See](../stories/the-driver-the-city-could-not-see/story.md) | No | General | Teen | 0.55 |
| [The Memory Under Line Zero](../stories/the-foundations-remember/story.md) | No | Teen | General | 0.22 |
| [The Friends I Built](../stories/the-friends-i-built/05-story.md) | Yes | General | Teen | 0.60 |
| [The Gentlest Terror](../stories/the-gentlest-terror/05-story.md) | No | General | Teen | 0.54 |
| [The Help Network](../stories/the-help-network/story.md) | No | General | Teen | 0.36 |
| [The Hollow Cask](../stories/the-hollow-cask/05-story.md) | Yes | Teen | General | 0.39 |
| [The Kingdom Was the Easy Part](../stories/the-kingdom-was-the-easy-part/story.md) | No | General | Teen | 0.27 |
| [The Last Bus to Briar Hill](../stories/the-last-bus-to-briar-hill/05-story.md) | Yes | General | Teen | 0.42 |
| [The Lights Beyond](../stories/the-lights-beyond/story.md) | No | Teen | General | 0.80 |
| [The Morning Her Hand Moved](../stories/the-morning-her-hand-moved/story.md) | No | General | Teen | 0.38 |
| [The Name I Kept](../stories/the-name-i-kept/story.md) | No | Teen | Mature | 0.32 |
| [The Name the Water Took](../stories/the-name-the-water-took/story.md) | No | General | Teen | 0.63 |
| [The Other Twin](../stories/the-other-twin/story.md) | No | General | Teen | 0.58 |
| [The Peace They Could Sleep Through](../stories/the-peace-they-could-sleep-through/05-story.md) | Yes | Teen | General | 0.43 |
| [The Ring Between Lives](../stories/the-ring-between-lives/story.md) | No | Teen | General | 0.55 |
| [The Sister Behind Her Smile](../stories/the-sister-behind-her-smile/story.md) | No | General | Teen | 0.36 |
| [The Spider's Hunger](../stories/the-spiders-hunger/story.md) | No | Teen | Mature | 0.35 |
| [The Unfinished Sunset](../stories/the-unfinished-sunset/story.md) | No | General | Teen | 0.56 |
| [The Vacant Throne](../stories/the-vacant-throne/story.md) | No | Teen | General | 0.41 |
| [The Wolf in the Mirror](../stories/the-wolf-in-the-mirror/story.md) | No | General | Teen | 0.35 |
| [The Wrong Side of the Part](../stories/the-wrong-side-of-the-part/05-story.md) | Yes | Teen | Mature | 0.20 |
| [Transitions in Common](../stories/transitions-in-common/05-story.md) | Yes | Teen | General | 0.58 |
| [Twelve in the Room](../stories/twelve-in-the-room/story.md) | No | Explicit | Mature | 0.56 |
| [Undisclosed](../stories/undisclosed/story.md) | No | General | Teen | 0.46 |
| [What the Town Owed Her](../stories/what-the-town-owed-her/story.md) | No | General | Teen | 0.47 |
| [What Turned Eighteen](../stories/what-turned-eighteen/story.md) | No | General | Teen | 0.53 |
| [When the Eagle Bowed](../stories/when-the-eagle-bowed/story.md) | No | Teen | Mature | 0.65 |
| [Where It Hurts](../stories/where-it-hurts/story.md) | No | Teen | General | 0.41 |
| [Where the Eagle Lands](../stories/yavrens-return/story.md) | No | General | Teen | 0.17 |

## Editorial spot-check

- Jev lowered [Nobody Spends Her Name](../stories/empire-within/story.md) and [Twelve in the Room](../stories/twelve-in-the-room/story.md) from Explicit to Mature. Both depict graphic gunshot wounds on the page, including severe facial injury or exposed tissue. Their existing Explicit ratings remain justified by the project rubric.
- Jev raised [The Wrong Side of the Part](../stories/the-wrong-side-of-the-part/05-story.md) from Teen to Mature with confidence 0.20. Its existing notes describe bereavement and family conflict without graphic content; that disagreement is a review candidate, not a reason to relabel it automatically.
- Most differences sit on the General/Teen boundary (48 of 56). A prose and cover review is needed before changing any published label.

The complete per-story choices, probabilities, confidence values, source hashes, request IDs, and usage are in [the machine-readable results](jev-rating-comparison-2026-09-28.json). Their `existing_rating` values are the pre-adoption baseline, not the current ratings for the ten changed packages.

## Follow-up: apply ratings above 0.60 confidence

The user chose to use Jev's rating when its reported confidence is **strictly greater than 0.60**. Eleven disagreements met that threshold. Ten `ratings.md` files now use Jev's choice and record its confidence alongside content notes and a reason. This includes one canon package, [The Courtesy of Blades](../stories/the-courtesy-of-blades/ratings.md), under the user's approval for this rating project.

| Story | Prior | Current | Jev confidence |
|---|---|---|---:|
| [A Little Winter for Sale](../stories/a-little-winter-for-sale/ratings.md) | Teen | General | 0.65 |
| [All Accounts Due](../stories/all-accounts-due/ratings.md) | Teen | Mature | 0.79 |
| [Between the Colors](../stories/between-the-colors/ratings.md) | General | Teen | 0.62 |
| [The Astral Valkyrie](../stories/the-astral-valkyrie/ratings.md) | Teen | Mature | 0.67 |
| [The Chair at the Back](../stories/the-chair-at-the-back/ratings.md) | Teen | General | 0.63 |
| [The Count Was 131,072](../stories/the-count-was-131072/ratings.md) | Teen | General | 0.72 |
| [The Courtesy of Blades](../stories/the-courtesy-of-blades/ratings.md) | Teen | General | 0.68 |
| [The Lights Beyond](../stories/the-lights-beyond/ratings.md) | Teen | General | 0.80 |
| [The Name the Water Took](../stories/the-name-the-water-took/ratings.md) | General | Teen | 0.63 |
| [When the Eagle Bowed](../stories/when-the-eagle-bowed/ratings.md) | Teen | Mature | 0.65 |

The user explicitly kept [Nobody Spends Her Name](../stories/empire-within/ratings.md) at **Explicit** despite Jev's Mature choice at 0.77, because its graphic gunshot wounds meet the locked Explicit definition. [His Infernal Majesty Says No](../stories/his-infernal-majesty-says-no/ratings.md) and [The Friends I Built](../stories/the-friends-i-built/ratings.md) have confidence exactly 0.60 and do not meet the strict threshold. No prose, cover, or canon marker changed.

After the ten updates, **150/196** current ratings match Jev and **46** differ. Current distribution: **106 General, 77 Teen, 8 Mature, 5 Explicit**.
