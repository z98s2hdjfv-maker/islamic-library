# Verse index and one-command lookup (v29)

Goal: one question, one lookup, results already citable and graded, so that study sessions spend their tokens
on the texts, not on finding them.

## Files
| File | Role |
|---|---|
| `reports/index/verse_index.tsv.gz` | Every commentary passage tagged with the verse it explains, and every quotation of a verse in the Sufi collections: `sura, aya, work, record_id, how, hits`. |
| `reports/index/verse_coverage.tsv` | Per work: passages, passages placed on a verse, verses reached, share placed by a lemma or heading. |
| `reports/index/works_meta.tsv` | Per work: title, author's death year (AH), source type, number of witnesses, pages corroborated / checked, secondary references, page note (e.g. the Shams offset). |
| `pipeline/index/build_verse_index.py` | Builds the verse index (method in its header). |
| `pipeline/index/lookup.py` | `--verse 2:31` prints every work on that verse, oldest author first, each passage with its locator and, for OCR texts, its collation level. `--build-meta` rewrites works_meta.tsv. |

## The `how` column
- `heading`: the edition itself heads the passage with that verse ([2.31]); al-Tustarī, al-Bayḍāwī, al-Qurṭubī.
- `lemma`: the passage opens by quoting the verse (Ṭabarī's "the interpretation of His saying {…}").
- `continues`: the passage quotes nothing and follows the last verse placed; still about that verse.
- `cited`: the verse is quoted elsewhere in a passage, or in a non-commentary text (Futūḥāt, Fuṣūṣ, the nūr,
  wilāya and asmāʾ collections, al-Jīlānī, the Sufi manuals). These answer "who among the Sufis uses this verse".

## Method, briefly
The Qur'an's own words are the key: the Mushaf is cut into 4-word sequences, keeping those found in at most three
verses, and each passage is matched against them, reading every commentary in order. No reliance on each
edition's markup, so the same code serves Ṭabarī's braces, al-Sulamī's tags and unmarked quotations.

## Checks at build
- 2:31: 246 passages in 32 works, including al-Ṭabarī's three key reports (Ibn ʿAbbās p01741–42, his own
  preference p01751), al-Qurṭubī (40 heading passages), al-Bayḍāwī, Ibn Kathīr, al-Suyūṭī, al-Sulamī, al-Qushayrī,
  and the Sufi texts that quote it (Ibn Sabʿīn, al-Qayṣarī, al-Fanārī, Bursevi, the Futūḥāt).
- 24:35: 380 passages in 47 works, from al-Tustarī (d. 283) to the Sufi collections, in about 6 seconds.

## Limits
Very short verses (under 4 words) can only be placed by headings or by following a longer neighbour; works with
very long units (al-Qushayrī's *Laṭāʾif*, 440 units) are placed coarsely: read the whole unit. `continues` rows
inherit their verse and can overrun into the next verse when that verse is not quoted; check the passage.

## Next (from the plan)
The citation fields here are joined at lookup time. Merging them into the search index itself, and a concept
index for terms like *quṭb*, *nūr muḥammadī*, *kawn jāmiʿ*, are the next steps; then a dossier per topic.
