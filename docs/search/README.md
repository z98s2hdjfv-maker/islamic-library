# Search layer

One SQLite file indexes every corpus unit (couplet, paragraph or page): 154 works and about
500,000 units, in Arabic and Persian. You can search it by surface form or by Arabic root.
It is the base for cross-connecting the figures before the juristic layer is built.

## Get the index
The index is about 590 MB, so it is not committed. Instead:
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
