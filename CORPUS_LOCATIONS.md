# Corpus locations — Islamic Library

**Repo (public):** https://github.com/z98s2hdjfv-maker/islamic-library
**Master copy:** mathnawi_library_2026-09-25_v6.zip + konya_pages_part01…06 zips on Housam's iPad.

## How a chat should fetch
- Single file (no auth): `curl -sLO https://raw.githubusercontent.com/z98s2hdjfv-maker/islamic-library/main/<path>`
- Whole repo: `git clone --depth 1 https://github.com/z98s2hdjfv-maker/islamic-library.git`
- Large scans: release `v1-assets` — see `release_assets.txt` for names, SHA-256 and URLs.
- Fetch to disk and query with code. Do not paste full corpus files into the conversation.
- Writing to the repo needs a fine-grained token (this repo only, Contents R/W). Housam supplies it per session; never store it in project files or memory.

## What lives where
| Path | Contents |
|---|---|
| corpus/mathnawi/book1–6.tsv | Mathnawi, one couplet per row, Nicholson-numbered IDs (Ganjoor pin a64968e7) |
| apparatus/mathnawi/ | collation pilot; konya/ Konya-vs-Ganjoor variants |
| annotations/mathnawi/ | story frames (lion_hare, merchant_parrot, umar_envoy), hadith check |
| catalogs/ | works summaries, OpenITI catalog, Shamela manifest, source surveys |
| pipeline/ | ingest scripts (mathnawi/, works/), repo builder (repo/) |
| reports/mathnawi/ | pilot/batch reports, summary, warnings |
| sources/fusus/ | raw text dump of Fusus (presentation-form glyphs; needs normalising) |
| docs/mathnawi/ | README, SPEC_STATUS |

## Release assets (v1-assets)
- **Fusus al-Ḥikam**, ed. Sayyid Niẓām al-Dīn Aḥmad — 520 pp, typeset; text layer has doubled glyphs (presentation form + base letter), removable deterministically.
- **al-Futūḥāt al-Makkiyya**, ed. ʿAbd al-ʿAzīz Sulṭān al-Manṣūb — 8,242 pp scan, ABBYY OCR with errors. Image witness only; take digital text from OpenITI.

## Not yet in the repo
- Full JSONL records (in master zip; rebuildable with pipeline/mathnawi/ingest_full.py).
- Konya page-image packs (candidates for release assets).
