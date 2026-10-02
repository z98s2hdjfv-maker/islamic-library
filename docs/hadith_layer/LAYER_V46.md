# v46: eight more collections in the hadith layer

The collections imported in v45 are now hadith-level records like the first thirteen (`apparatus/hadith/`), built by
`pipeline/hadith/build_hadith_layer_extra.py`. The layer holds 21 collections and 164,521 hadith.

| Collection | Hadith | Notes |
|---|---|---|
| al-Tayalisi, Musnad (d. 204) | 2,767 | |
| al-Humaydi, Musnad (d. 219) | 1,309 | |
| al-Bazzar, Musnad (d. 292) | 10,321 | his own remark after the hadith is in `comments` (5,146 hadith) |
| Abu Ya'la, Musnad (d. 307) | 7,553 | |
| Ibn Hibban, Sahih (d. 354), as al-Ihsan | 6,991 | grade: Ibn Hibban's own claim of soundness by inclusion; he is counted among the lenient |
| al-Tabarani, al-Awsat (d. 360) | 9,478 | his note on who alone narrates it is in `comments` (6,375 hadith) |
| al-Tabarani, al-Saghir | 1,195 | likewise (1,110) |
| al-Bayhaqi, Shu'ab al-iman (d. 458) | 11,398 | |

All 21 collections now share the parallels and the narrator links (`pipeline/hadith/build_hadith_links.py`, rerun):
17,695 groups of parallel hadith, 15,385 of them across collections. **The parallel group ids (P......) were
renumbered**; nothing else in the repo cites them.

## What this unlocked
al-Haythami's Majma' names six sources. With all six in the layer his joined verdicts rose from 6,955 to 11,436 rows
(10,996 hadith): al-Awsat 2,278 hadith, al-Bazzar 1,083, Abu Ya'la 811, al-Saghir 293, beside Ahmad and the Kabir.
See `catalogs/critic_grades_summary.json` (`coverage`) for the count per collection.

## Coverage, honestly
| | Hadith | No classical grade |
|---|---|---|
| The first 13 collections | 113,509 | 79,057 (69.6%) |
| All 21 collections | 164,521 | 118,613 (72.1%); 104,928 (63.8%) have not even the Sahih wording note |

The share did not fall, because the eight new collections are mostly ungraded themselves. What grew is reach: a saying
is now looked up in 21 collections, and 17,837 hadith carry a later critic's verdict (13,486 before).
Still without any hadith-by-hadith classical grade in the library: Abu Dawud, al-Nasa'i, al-Darimi, al-Daraqutni,
al-Tayalisi, al-Humaydi, Shu'ab al-iman, and most of Ahmad.

## Limits
- Ibn Hibban's text: the source prints some hadith twice; the repeat is skipped. The modern editor's footnotes are
  kept out, so no modern grading enters. A few hadith broken across pages may be cut short: check the corpus record.
- al-Bazzar gives several chains before one wording: the earlier chains appear as records with an empty matn.
- Shu'ab al-iman: about 45% of records could not be split into chain and text (reports of the Followers and sayings
  of the pious, with no mention of the Prophet); the whole text is in `matn`.
- Checked by Claude, not a scholar: 24 random new joins of al-Haythami read, all the right hadith.
