# Mathnawi corpus (Ganjoor): what's in this folder

**Master copy:** `mathnawi_library_2026-09-25_v6.zip`, plus six image packs `konya_pages_part01…06_*.zip` (546 Konya pages: all of Book One and every page with a variant site in Books 2–6), saved on Housam's iPad. It holds everything below plus the full JSONL records, per-section reports, the collation witness text and SHA256SUMS. This folder holds the working files only.

**Source:** ganjoor-data, commit `a64968e78425b2e8c7904fbdf5289fba8251a757`, folder `poets/moulavi/masnavi/daftar1-6`.
**Status:** everything is imported and unverified unless marked otherwise. The verse text is byte-exact from the source. Nothing was retyped or normalised. A rebuild on 2026-09-25 reproduced these TSVs byte for byte.

## Full text: `mathnawi_book1.tsv` … `mathnawi_book6.tsv`
Each row is one couplet. Columns: `id, ganjoor_seq, section, line, nicholson_derived, hemistich_1, hemistich_2` (in Book 1 the fifth column is `nicholson` and is fully filled in).

| Book | Sections | Couplets |
|---|---|---|
| 1 | 172 | 4013 |
| 2 | 115 | 3819 |
| 3 | 228 | 4809 |
| 4 | 139 | 3851 |
| 5 | 178 | 4233 |
| 6 | 140 | 4912 |
| **Total** | **972** | **25,637** |

The full JSONL records (with frame, speaker, annotation and provenance) are too large for the project. They are in the master copy and can be rebuilt exactly with `ingest_full.py` from the pinned commit.

## How the numbering works
- `ganjoor_seq` is the running couplet number within each book, in Ganjoor order. It is exact.
- **Book 1 is fully numbered by Nicholson (2026-09-25).** Every couplet was aligned with masnavi.net's 4,003 Nicholson-numbered verses; they stay in order throughout. IDs are `…:1.b0001`–`b4003`. The 11 Ganjoor couplets Nicholson lacks carry a letter suffix (e.g. `1.b0083a`) and the status interpolation_candidate. Nicholson 1.2517 is missing from Ganjoor, and §12:8 comes one place earlier than Nicholson's 332. **Books 2–6 were numbered the same way on 2026-09-25.** Nicholson totals: 3,810, 4,810, 3,855, 4,238 and 4,916. Every book's IDs now follow Nicholson. Ganjoor-only couplets carry suffixes, and transposed couplets are marked.
- Ganjoor's counts don't match Nicholson's. Book 1 has 6 extra couplets before sh42, and the book totals differ too. So a plain running count is **not** a Nicholson number.
- IDs:
  - anchored couplets use `urn:sufi:rumi.mathnawi:<book>.b<nicholson>`;
  - all others use `…:<book>.g<ganjoor_seq>`, where the `g` marks a Ganjoor-based number.

## Frame and speaker annotations
- Book 1, sh42–76: the pilot frame map (`frames_lion_hare.json`).
- Book 1, sh77–83 and sh84–96: model-suggested maps (`frames_umar_envoy.json`, `frames_merchant_parrot.json`).
- All other sections: none yet (`annotation.method = none`).

## Pilot checks (2026-09-25)
- `collation_pilot.tsv`: each of the 490 pilot couplets compared with two witnesses: masnavi.net (Azar Yazdi's text, Nicholson numbering) and the Konya manuscript of 677 AH (pages p0044–p0054, read from the images). Konya has all 490 couplets in the same order. Of the 69 couplets where the first two texts differ, Konya supports Ganjoor in 51, masnavi.net in 14, and 4 differ only in spelling. Konya differs from both at §53:4, §64:4 and §69:10. The Konya readings are model-read and still `unverified`; the page images are in the master copy.
- `pilot_hadith_check.json`: the pilot's 11 sayings, with collections, numbers and attributed gradings.

## Konya check, all of Book One (2026-09-25)
- `konya_book1_differences.tsv`: the 73 places where the Konya manuscript (677 AH; images from Ganjoor's scan of the 1993 Turkish facsimile, pages p0023–p0113) does not match Ganjoor. There are 63 word differences, 3 couplets missing from Konya (§4:7, §11:4, §11:5) and 7 additions in Konya's margins. The other 3,947 couplets match. The readings are model-read and still `unverified`. The full per-couplet table and all page images are in the master copy (v3).

## Three-witness result, Book One (2026-09-25)
- Ganjoor and the Nicholson text (masnavi.net) differ in wording at 588 couplets. Each was re-checked against Konya with both readings in view. Konya's main text supports Ganjoor in 302, the Nicholson text in 47, and neither in 8. The other 231 differ only in spelling.
- `book1_variants_konya_not_ganjoor.tsv`: the 55 couplets where Konya does not support Ganjoor, with Konya's reading and notes. The full tables (all 4,013 rows, with Nicholson's English translation) are in the master copy (v4).

## Books 2–6: Konya at the variant sites (2026-09-25)
- 1,211 places where Ganjoor and the Nicholson text differ were checked against Konya. For wording differences, Konya's main text supports Ganjoor at 459, Nicholson at 129 and neither at 9; 573 differ only in spelling. Of the 17 Nicholson-only couplets, Konya has 12 in its main text, 5 in the margin only, and 4 not at all. Of the 17 Ganjoor-only couplets, 15 are in the margin only, 1 is in the main text, and 1 is absent.
- `books2-6_konya_not_ganjoor.tsv`: the 166 rows where Konya does not support Ganjoor. The full table (`variant_sites_konya.tsv`) is in the master copy.
- Page p0336 is damaged in Ganjoor's scan, so Book 4, Nicholson 126 could not be checked.

## Known source issues
- 61 couplets in Book 1 (and more in the other books) have vowel marks written in a non-standard order: kasra, fatha, damma or tanwin after the shadda, or hamza written as a separate mark. They were kept as they are. Normalise only when searching.
- In Book 6 sh34 (VOrder 35), both hemistichs were entered in one field, joined by " / ". That couplet is kept as a single-line record and needs fixing by hand.

## Files
- `ingest_full.py`: builds all six books
- `ingest_mathnawi.py`: runs one range of sections
- `ingest_pilot.py`: the original pilot script
- `mathnawi_summary.json`, `mathnawi_warnings.json`: counts, warnings, and the source fields that were left out
- `pilot_report.json`, `batch02_report.json`, `batch03_report.json`: per-section counts and checksums for the first three story batches. The batch JSONL files were removed on 2026-09-25 to free space; they are identical to the full run and are in the master copy.
- `SPEC_STATUS.md`: where the spec and pilot stand

## Other works in the master copy (v6, 2026-09-25)
Imported by `ingest_works.py` from the same ganjoor-data commit. Only the text was kept; Ganjoor's machine summaries were dropped. All text is unverified. Counts are in `works_summary.json`.
- Dīwān-i Shams: 3,230 ghazals (34,603 couplets), 1,994 rubāʿīs, 44 tarjīʿāt, 2 mustadrakāt. IDs are rumi.diwan:gh/rb/tj/ms + the Ganjoor number (apparently Furūzānfar's numbering; to be verified).
- Fīhi mā fīhi: preface plus 70 discourses (rumi.fihi:d). Majālis-i sabʿa: 7 sermons in 16 parts (rumi.majalis:m).
- Bahāʾ Walad, Maʿārif: Part One only, 86 sections (bahawalad.maarif:j). Sulṭān Walad, Waladnāma: 8,861 couplets (sultanwalad.waladnama:s).
- The full files are too large for the project (the Dīwān alone is about 19 MB), so they live in the master copy only.
- Not on Ganjoor, still missing: Rumi's Maktūbāt; Shams's Maqālāt; Aflākī's Manāqib; Sipahsālār's Risāla; Burhān al-Dīn's Maʿārif; the rest of Bahāʾ Walad's Maʿārif; and Sulṭān Walad's other works.
