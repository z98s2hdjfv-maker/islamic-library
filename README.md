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

Verse IDs follow `urn:sufi:rumi.mathnawi:<book>.b<nicholson>` (anchored) or
`...g<ganjoor_seq>` (Ganjoor-based). See `docs/mathnawi/README.md`.

**Search:** a root-aware full-text index over the whole corpus is published as a release asset; see `docs/search/README.md`.

Large binaries (scans, page-image packs) are **not** committed. They are
published as GitHub Release assets; see `release_assets.txt`.

`MANIFEST.tsv` lists every file with SHA-256 and original filename.
Built 2026-09-26.
