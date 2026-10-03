# v43: testing a saying (authenticate.py)

One command gathers what the library holds on a saying attributed to the Prophet, a Companion or a master:

    python3 pipeline/hadith/authenticate.py "اطلبوا العلم ولو بالصين"
    python3 pipeline/hadith/authenticate.py "كنت كنزا مخفيا فأحببت أن أعرف" "اختلاف أمتي رحمة" --limit 3 --context 30
    python3 pipeline/hadith/authenticate.py "..." --also sufi_manuals,tafsir     # who quotes it there
    python3 pipeline/hadith/authenticate.py "..." --json                         # data for a sijill entry

Several sayings are tested in ONE pass (about 20 to 30 seconds whatever their number), so batch them.
It needs only the repo: no search index.

## What it returns
1. **Found in the collections.** The hadith layer (13 collections, 113,509 hadith) matched by loose wording; for each
   hit the record id, narrator, the printed number where the layer has one, the grades found in the sources (the
   compiler's own, and al-Dhahabi on al-Hakim), the parallel group, and the narrators linked to Ibn Hajar's Taqrib.
   The best match of each collection comes first, oldest collection first.
2. **The classical critics, oldest first.** Every passage quoting the saying in the works of
   `catalogs/authentication_works.tsv`: fabrication collections (Ibn al-Jawzi, al-Dhahabi's Talkhis, al-Suyuti,
   al-Qari), grading works (al-Haythami, al-Busiri), takhrij (al-Zayla'i, al-'Iraqi, Ibn Hajar), narrator criticism
   (al-Dhahabi's Mizan), popular sayings (al-Sakhawi) and mass-transmitted hadith (al-Kattani). When the saying is a
   short entry heading, the paragraphs that follow (where the verdict is) are attached as `then:`.
3. **Modern grades**, kept apart (al-Albani). Never merge them into a classical verdict.

## Loose wording
The saying and the texts are normalised, the particles و ف ب ل ال and a final alif are stripped, and very common words
are dropped. A passage matches when a short stretch of it holds most of the saying's remaining words:
score = 0.7 x share of the words present + 0.3 x share of adjacent word pairs kept in order; threshold 0.7
(`--threshold`). So كنت كنزا مخفيا finds al-Sakhawi's كنت كنزا لا أعرف, which an exact phrase search misses.
A saying with fewer than three distinctive words is too short for this: use `textsearch.py`.

## Limits: what it does not do
- **It gathers evidence; it does not grade.** `verdict words nearby` are words found near the quote (موضوع، لا أصل
  له، ضعيف، صحيح ...). They can be about another report, a narrator, or a denial ("neither a sound nor a weak chain").
  Read the passage before citing it.
- The chain line lists only narrators that could be linked to the Taqrib. It ignores unlinked names, breaks in the
  chain, hidden defects and corroboration. It is not a grade of the hadith.
- "Not found" means not found in this library by this wording. Try a shorter or different wording before saying so,
  and say exactly that.
- Since v44 the verdicts of al-Busiri, al-Haythami and al-Dhahabi are joined to the hadith as data and shown under each
  hadith (`critic, on the chain: ...`), al-Albani on al-Tirmidhi as `MODERN (kept apart)`, with a note when the wording is
  also in the Sahih, and the critics' numbered entries on the saying are listed. See CRITIC_GRADES.md. A verdict on a
  chain is not a grade of the hadith.
- al-Maqasid al-hasana is searched once (the copy in `corpus/grading`), not twice.

## The list of works
`catalogs/authentication_works.tsv`: corpus_path, function (fabrication, grading, takhrij, narrator_criticism,
popular_sayings, mutawatir), layer (classical | modern), author, work, death_ah. A new critic is one new row.

## Test
`python3 pipeline/hadith/test_authenticate.py` checks three sayings of known standing (the hadith of intentions,
"seek knowledge even in China", the "hidden treasure"). It runs with each library update.

## Speed (v49)
The command had slowed as the library grew: four sayings took 60 seconds at v48 (18 at v43). v49 brings that to
about 21 seconds on two processors and 35 on one; a single saying takes about 15. The output is unchanged: twelve
test sayings gave byte-identical JSON before and after, in parallel and on one processor.
- The files are scanned side by side on the machine's processors and the results put back in file order
  (`AUTHENTICATE_JOBS=1` forces one after another).
- A line none of whose words can match is skipped before it is parsed.
- Text normalisation (`pipeline/search/textnorm.py`) gives the same result about five times faster; this also
  speeds the search index build. Each word is stemmed once.

## v53: brief mode, the sijill first, and al-Tirmidhi's missed hadith
- `--brief`: one short block per saying: the collections, whether it is in al-Bukhari or Muslim, the classical grades and critics (one line each, with the record id), the modern grades kept apart, and three ids to cite. No passages. Forty sayings fit in a few pages; then run the full mode on the few sayings whose passages must be read. Never record a standing from brief mode alone.
- The sijill is consulted first: a saying already entered is reported with the standing recorded for it (`ALREADY IN THE SIJILL` / `SIJILL:`), so it is linked and not entered twice. `--json` carries the same under `sijill`.
- A saying with no classical critic's verdict anywhere in the library (only a compiler's inclusion, a modern grade or nothing) is flagged in both modes, and as `classical_verdict_in_library` in `--json`.
- `ابن` and `بن` are matched as one word (the JK editions write "يا بن آدم").
- Al-Tirmidhi's layer gained 131 hadith that the v16 build had dropped (paragraphs that begin with the basmala, with the editor's mark, or with a report given before its chain): `pipeline/hadith/fix_tirmidhi_layer.py`. They carry ids of the form `urn:hadith:0279Tirmidhi.Sunan:p<paragraph>` and their printed (Shakir) numbers; no existing id changed. The critics' and modern tables (`apparatus/hadith_grades*`), the parallels and the chains were not rebuilt for them, so they show al-Tirmidhi's own grade only.
