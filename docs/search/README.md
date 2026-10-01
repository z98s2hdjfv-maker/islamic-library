# Search layer

One SQLite file indexes every corpus unit (couplet, paragraph or page): 154 works and about
500,000 units, in Arabic and Persian. You can search it by surface form or by Arabic root.
It is the base for cross-connecting the figures before the juristic layer is built.

## Get the index
The index is about 1.1 GB compressed, so it is not committed. Instead:
- **Download** the release asset `library_search_index.sqlite.gz` (release tag `search-index`),
  then gunzip it to `search/library.sqlite`.
- **Or rebuild** it in about 4 minutes:
  `pip install camel-tools && camel_data -i morphology-db-msa-r13 && python3 pipeline/search/build_index.py --repo . --out search/library.sqlite`

The GitHub Action `build-search-index` rebuilds the index and republishes the asset. Run it
from the Actions tab after the corpus changes.

## Query
```
python3 pipeline/search/search.py "التوكل"                      # surface form
python3 pipeline/search/search.py --root وكل --by-author         # root w-k-l, hits per figure/work
python3 pipeline/search/search.py "توکل" --author rumi            # Persian works normalise ک/ی too
python3 pipeline/search/search.py --root علم --root ذوق --near 5  # two roots within 5 words
python3 pipeline/search/search.py --root جهد --lang ar --attribution secure --json
```
Every hit carries its corpus `uid` (cite this), the figure, the attribution, and a warning when
the text is OCR or a cleaned PDF text layer.

## How it works
- **Normalisation** (`textnorm.py`, the same for index and query): harakat, tatweel and
  Quranic marks are stripped. Alif variants become ا, and ى/ی become ي. ک becomes ك, ة
  becomes ه, and ؤ/ئ become و/ي. The Persian half-space is joined.
- **Roots:** each distinct word type (about 590,000) is analysed once with CAMeL Tools
  `morphology-db-msa-r13`, with no backoff. The union of roots over all analyses is stored, so
  the search favours recall over precision. In CAMeL, a weak radical is written `#`; the index
  stores it as `ـ`, and `--root وكل` also matches `ـكل`. A word CAMeL cannot analyse has no
  root (for example المتوكلين). Surface search still finds it.
- **Persian:** Persian works are root-analysed too. This finds Arabic loanwords such as توکل and
  علم in Rumi, but Persian words can pick up spurious Arabic roots. Use `--lang ar` to exclude
  Persian.
- **Duplicates:** OpenITI holds several versions of some works. Only each work's primary version
  (from `catalogs/openiti_catalog.json`) is searched unless you pass `--all-versions`. The
  Mathnawī is indexed once, from `corpus/mathnawi/book*.tsv` with the Nicholson IDs.
- **Tables:** `units`, `fts` (FTS5: `norm`, `roots`), `works`, `vocab` (word, roots,
  frequency), and `meta` (repo commit, CAMeL version, build time).

## Limits
- Root analysis uses a Modern Standard Arabic database. Classical forms and proper names are
  sometimes missed or over-analysed.
- The results do not disambiguate: a hit for root علم includes عَلَم (flag) as well as عِلْم.
- OCR witnesses (Futūḥāt Manṣūb, Fuṣūṣ OCR, Maqālāt-i Shams, Aflākī) have noisy text, so
  expect misses there.

## Hadith filters (v17)
See docs/hadith_links/README.md: --hadith-only, --caliph, --narrator, --graded, --agreed, --max-weakest-rank, --parallels.

## Citation layer (v32)
The index now carries the citation data that `pipeline/index/lookup.py` used to join by hand, so one query
returns hits that are already citable and graded:
- every hit shows the author's **death year**, its **locator** as in the corpus record (`vol=… page_before=…`,
  `leaf=… printed_page=…`, `poem_number=…`), its **heading**, and for OCR pages the **collation level**
  (verified > corroborated > partial > divergent > unmatched; `no_witness` = nothing to compare against;
  `unchecked` = not collated). `--json` adds `death_ah`, `title`, `ocr_level`, `loc`, `heading`, `page_note`.
```
python3 pipeline/search/search.py --verse 2:31 --chrono                  # the verse, then every passage on or quoting it, oldest first
python3 pipeline/search/search.py --root نور --verse 24:35 --how lemma    # root hits inside commentary lemmas on the Light verse
python3 pipeline/search/search.py --concept qutb --before 700 --min-level corroborated
python3 pipeline/search/search.py --root سمو --by-author --chrono         # per-figure counts with death years, in order
```
- `--verse S:A` (with `--how verse,lemma,heading,continues,cited`) and `--concept NAME` need no query.
  An unknown concept name prints the list of known ones.
- `--min-level L` keeps typed texts and drops OCR pages below L (and unchecked OCR pages).
- `--before AH` / `--after AH` filter by the author's death year; `--chrono` orders by it (the Qurʾān first).
- **Caution:** the concept index matches words, not senses. `qutb` also finds the pole of a millstone or of the
  heavens in the tafsīrs. Read the heading and the passage before citing a hit as a use of the technical term.

Tables (joined to `units` by `unit` = `units.rowid`): `work_meta`, `unit_conf`, `verse_refs`, `concept_refs`,
`concepts`, `unit_loc` + `heads`; `works` gains title, death_ah, witnesses, corroborated, checked, refs, page_note.
Sources: `reports/index/works_meta.tsv`, `verse_index.tsv.gz`, `concept_index.tsv.gz`, `concept_summary.tsv`,
`reports/collation/confidence.tsv.gz`. The layer adds roughly 100 MB before compression, a few percent of the index.

**Safety:** the layer is built inside a savepoint. If a citation file is malformed, the build prints a warning,
records `citations = failed: …` in `meta`, and publishes the index without the layer; the corpus is never touched.
An index built before v32 still works with the new `search.py` (the new flags then say the layer is missing).

**Maintenance:**
```
python3 pipeline/search/build_index.py --repo . --out search/library.sqlite --add-citations   # upgrade a downloaded index in place
python3 pipeline/search/build_index.py --repo . --out /tmp/sample.sqlite --only 0001Quran,TafsirJalalayn,fusus   # sample build
python3 pipeline/search/test_search.py --db search/library.sqlite                              # smoke test
```

## Best readings in the index (v33)
OCR pages that have a best reading (docs/best_reading/README.md) are searched by that reading, so a word the
OCR misread is still found. The hit shows the reading, marked `best reading (N corrections)`; `--ocr` shows
the raw OCR instead, and `--json` says `text_is: best_reading | corpus`. `units.text` is always the corpus
text; the reading lives in `unit_reading`. (`--add-citations` does not add readings: rebuild the index.)

## Phrase search without the index (v37)
`pipeline/search/textsearch.py` searches the corpus files directly, so it works in a sparse clone. Text and query
are normalised alike (textnorm, then punctuation, digits and page markers become spaces), so "فالكلم: اسم، وفعل"
is found by "فالكلم اسم وفعل", and vowelled or hamzated queries find unvowelled text. Each word may carry a
proclitic (و ف ب ل ك) unless --exact. `--folder`, `--work`, `--count`, `--json`, `--best-reading` (OCR works).
It matches words, not roots; for roots use the index (`search.py --root`). The index's hadith hits now show
the printed edition number: "↳ urn:hadith:0279Tirmidhi.Sunan:2105 (printed no. 2139 (Shakir / ʿAbd al-Baqi numbering))".

## v39: textsearch.py fixes
- It no longer crashes on the full Mathnawī records (corpus/mathnawi/full), whose `text` is a structured object
  (the Persian hemistichs inside it); any other odd record is skipped and reported, never fatal.
- A pre-check on the raw line skips non-matching records before decoding: the whole corpus in about 85 s instead of
  4 minutes. It allows the spelling variants the normaliser unifies (Arabic and Persian ya/ha/kaf, hamza forms) and
  vowel marks between letters; `--no-prefilter` turns it off, and our test queries gave identical results.
- Piping into `head` ends quietly. Use `--folder` to narrow a search: seconds instead of a minute.

## v42: exact pages
OpenITI marks page boundaries with `PageV18P056` (or `PageEndV18P494`); both mark the END of that page. Checked against
the Shamela Futuhat, which carries printed pages: the printed page was the marker's page + 1 in 116 of 119 passages.
So a record starts on `page_before + 1`, and a passage inside a long record is on 1 + the last marker before it.
lookup.py, search.py and textsearch.py now print the true `page`; `pipeline/search/cite.py <record_id> "<phrase>"`
gives the exact page of any phrase. Record ids are unchanged, so nothing that cites them breaks. Citations made
before v42 from `page_before` are one page early (more inside long records); the dossiers and the sijill are corrected.
