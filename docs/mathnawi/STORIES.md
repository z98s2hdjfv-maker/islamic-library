# The Mathnawi by story (v54)

Rumi teaches by stories inside stories. A couplet quoted without its story can carry the opposite of his meaning: the
parrot's question at 1:261 is the mistake the tale is about, and Rumi's own moral comes two couplets later (1:263).
From v54 the library can give every couplet its place.

## What was added
| File | What it holds | Status |
|---|---|---|
| `apparatus/mathnawi/sections.tsv` | all 972 sections of the six books: Rumi's own prose heading (Persian), the couplet range, and a `kind` | headings exact, from the pinned Ganjoor commit (`catalogs/mathnawi_sections_pins.json`); `kind` derived from the heading's first words, a guide only |
| `apparatus/mathnawi/stories_book1.tsv` | the 20 stories of Book 1: English title, sections, couplet range, inset tales | Claude's reading of the headings; unverified |
| `pipeline/mathnawi/build_sections.py` | rebuilds sections.tsv from the pinned source | fetches 972 small files |
| `pipeline/mathnawi/story.py` | a couplet with its heading, story and recorded readings; `--stories`, `--headings` | |
| `sijill/registry/layers.tsv`, types `passage` and `reading` | several readings of one passage, each with its layer and its reader | validated |

`kind`: `tale` (the heading opens a tale: حکایت، داستان، قصه، مثل), `return` (رجوع، بقیه: back to a tale left off),
`exposition` (بیان، تفسیر: Rumi comments), `step` (a step in the telling). 165 tales, 57 returns, 161 expositions, 589 steps.
Ganjoor's machine-written summaries of poems and couplets are not imported.

## Voice and layer
- **Voice in the text** is recorded on each `passage` entry (`data.voice_in_text`): the narrator, a character, or Rumi
  in his own voice. The corpus records have `frame` and `speaker` fields, still empty; they are filled story by story
  as stories are read, not by a rule.
- **Layer of a reading** (`sijill/registry/layers.tsv`): `plain_sense`, `author_moral` (he says it himself; the couplet
  is cited), `commentator`, `reader`, `claude`. The view `sijill/views/readings.md` sets them side by side.

## What is not done
- Story maps for Books 2 to 6 (the headings are there; grouping them into stories is reading, and is not automated).
- The speaker of each couplet across the whole poem.
- A classical commentary on the Mathnawi. Until one is in the library, the only authoritative layer is Rumi's own
  stated meaning; everything else is a reader's or Claude's.
- An English translation is not stored: Claude translates what it quotes and says so.
