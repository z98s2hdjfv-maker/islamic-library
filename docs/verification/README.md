# Verification: checking poor-quality OCR against printed editions (v21)

21 works in the library are uncorrected OCR of scanned books (`source_type = ocr_uncorrected` in
`catalogs/works_index.tsv`). This layer records which passages have been checked, against what, and
what the correct reading is, without ever editing the corpus itself.

## The three parts
| File | Role |
|---|---|
| `catalogs/secondary_literature.tsv` | Modern editions, translations and studies usable as references, with the corpus works each covers and what it can validate: `text` (Arabic wording, only for editions with the Arabic), `locators` (chapter/page), `sense` (meaning). `access` is yours to fill: owned / library / none. |
| `catalogs/verification_log.tsv` | One row per checked record: `record_id`, `work_key`, `status` (verified, corrected, disputed, illegible), `ref_id` (a secondary_literature id, or `scan` for the archive.org page image), `ref_locator`, `corrected_text`, `checked_by`, `date`, `note`. |
| `reports/ocr_quality_works.tsv`, `reports/ocr_quality_worst.tsv` | Built by `pipeline/verify/ocr_quality.py` (first run at v21; each later update zip that adds OCR works re-runs it): each OCR work's triage score and its 25 worst pages, so checking starts where the text is most damaged. |

`pipeline/verify/check_verifications.py` validates the log and writes `reports/verification_summary.tsv`.
Update zips that add log rows run it first, so a malformed row stops that update and nothing half-checked is published.

## Rules
1. **The corpus is never edited.** The OCR stays exactly as imported; corrections live in the log. This keeps
   provenance intact and lets anyone see what was changed and on whose authority.
2. **Copy only the premodern author's words.** `corrected_text` holds the classical Arabic or Persian of the
   passage, as short as needed. Never copy a modern editor's translation, commentary, footnotes or apparatus
   into the repo: those are copyrighted. Cite them by `ref_id` and `ref_locator` instead.
3. **Match the reference to the question.** Only an edition with the Arabic text (`validates` includes `text`)
   can settle wording. A translation or study can confirm a chapter number or the sense, not a letter.
4. **The scan comes first.** If the archive.org page image is legible, check against it (`ref_id = scan`);
   use a printed edition where the scan itself is damaged, or to resolve a disputed reading.
5. **Say who checked.** `checked_by` names the person or tool. A check by Claude from the scan image is
   recorded as such, so a human reviewer can confirm it.

## First entry
al-Qayṣarī, Sharḥ Fuṣūṣ al-ḥikam, leaf 5 (contents page), checked against the scan: every chapter title of
the Muqaddima is correct in the OCR, but every page number was garbled. Chapter 9, "on the vicegerency of the
Muhammadan reality, and that it is the Pole of Poles," begins on p. 145. Mukhtar Ali's *Horizons of Being*
(`ali2020_horizons`) is the reference for the Muqaddima's wording.

## Triage at v21 (mean score, % of pages below 60)
Worst first: Aflākī's Manāqib (73.3, 11%), the Fuṣūṣ OCR (82.3, 6%), Shams's Maqālāt (83.5, 3%),
the Manṣūb Futūḥāt (90.0, 6%). The v20 archive.org works score 90-97. The score counts clean-looking words;
it cannot see a misplaced dot, so a high score means "probably readable", never "verified".
