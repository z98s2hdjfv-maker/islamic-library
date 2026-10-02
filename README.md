# Islamic Library — working repository

Layered corpus for the *Understanding the Quran* project. Data flows one
way; no layer edits the one before it.

| Layer | Holds | Rule |
|---|---|---|
| `sources/` | raw downloads + checksums | never edited |
| `corpus/` | canonical texts (one couplet/verse per row) | byte-exact from source |
| `apparatus/` | variants, collations between witnesses | never alters corpus |
| `annotations/` | frames, hadith checks, scholarly perspectives | keyed to verse IDs |
| `catalogs/` | what works exist and where they came from | |
| `pipeline/` | scripts that regenerate the above | |
| `reports/` | outputs and warnings from pipeline runs | |
| `docs/` | README / spec status per corpus | |
| `sijill/` | what the studies concluded (the record of the Jalasa) | append-only; cites record ids |

**Hadith layer and authentication (v43 to v48).** `apparatus/hadith/` holds 21 collections (164,521 hadith) with
parallels and narrator links (`apparatus/hadith_links/`). The critics' verdicts are joined to the hadith as data:
classical in `apparatus/hadith_grades/`, modern kept apart in `apparatus/hadith_grades_modern/`. A classical grade
exists for 30% of the hadith; a class label is rule-made, so quote the verdict. See `docs/hadith_layer/`
(`AUTHENTICATE.md`, `CRITIC_GRADES.md`, `GRADE_GAP_V47.md`, `V48_FIXES.md`).

Verse IDs follow `urn:sufi:rumi.mathnawi:<book>.b<nicholson>` (anchored) or
`...g<ganjoor_seq>` (Ganjoor-based). See `docs/mathnawi/README.md`.

**Search:** a root-aware full-text index over the whole corpus is published as a release asset; see `docs/search/README.md`. Since v32 every hit carries its death year, locator, heading and OCR collation level, and the index can be queried by verse (`--verse 2:31`) or concept (`--concept qutb`).

Large binaries (scans, page-image packs) are **not** committed. They are
published as GitHub Release assets; see `release_assets.txt`.

`MANIFEST.tsv` lists every file with SHA-256 and original filename.
Built 2026-09-26; brought up to date in v49 (2026-10-02). Start with `START_HERE.md`; to test a saying, `python3 pipeline/hadith/authenticate.py "<saying>"`.

**The Jalasa stress test (v50).** `docs/jalasa/STRESS_TEST.md` is a document of test cases, one table row each, that
`pipeline/jalasa/stress_test.py` runs against the repo: what a digital Jalasa needs (verses, sayings, the masters,
the caliphs, the schools, citations, the sijill), marked `must` (works today) or `goal` (not yet). The scorecard is
`reports/jalasa/STRESS_REPORT.md`; `stress_history.tsv` keeps one line per run. Edit the document to change the test.

**Updates.** A `library-update-vNN.zip` is uploaded to the repo root and the "Library update and search index"
workflow applies it. Since v49 every update runs `pipeline/repo/after_update.sh` first (sijill validator, the
authentication tests, the Jalasa stress test, a check for stray archives, then the manifest): if a check fails, nothing is committed.
