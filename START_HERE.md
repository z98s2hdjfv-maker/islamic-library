# Start here: how to study with this library

This repo is the evidence. The Project's dossiers are maps of where to look, never the answer. For any study
question, **query the repo first and answer from the files**; use general knowledge only for what the files
don't cover, and say which is which.

## 1. Get the repo (one command, about 2.5 GB)
    git clone --depth 1 https://github.com/z98s2hdjfv-maker/islamic-library.git lib && cd lib

## 2. Find the evidence
| Question | Command or file |
|---|---|
| What does the library hold? | `catalogs/works_index.tsv`: key, author, work, attribution, category, source_type |
| Every commentary on a verse, oldest first | `python3 pipeline/index/lookup.py --repo . --verse 7:172` |
| A key term across the works | `python3 pipeline/index/lookup.py --repo . --concept qutb` (list and precision: `reports/index/concept_summary.tsv`, `concept_precision.tsv`; ambiguous terms are sense-filtered, still read the passage) |
| **Is this saying authentic?** (start here for any quoted hadith or saying) | `python3 pipeline/hadith/authenticate.py "<saying>" "<another>"` (v43): loose-wording match in the 21 collections with grades, parallels and chain, then the classical critics oldest first, then modern grades apart. Several sayings in one pass, about 25 s. It gathers evidence and does not grade: read the passages. `docs/hadith_layer/AUTHENTICATE.md` |
| The later critics' verdict on a hadith, as data (v44) | shown by `authenticate.py` under each hadith; tables in `apparatus/hadith_grades/` (al-Busiri on Ibn Maja, al-Haythami on Ahmad and al-Tabarani, al-Dhahabi on al-Hakim), modern apart in `apparatus/hadith_grades_modern/` (al-Albani on al-Tirmidhi). **A verdict with scope = chain is about that chain, not the hadith; quote his words and cite `critic_record`.** Critics' numbered entries on current sayings: `apparatus/sayings/sayings.tsv.gz`. `docs/hadith_layer/CRITIC_GRADES.md` |
| A hadith and its grades | `zgrep` in `apparatus/hadith/*.jsonl.gz` (narrator, caliph, grades in the sources, parallels). **Cite the printed number** in `edition_numbers` where present (al-Tirmidhi: Shakir; al-Bukhari: Fath al-Bari), not the layer's own `number` |
| More verdicts, the compilers' remarks, a modern column (v47) | also shown by `authenticate.py`. Classical, in `apparatus/hadith_grades/`: al-Mundhiri on Abu Dawud and in al-Targhib, al-Nawawi's Khulasa, Ibn Hajar's Bulugh, al-Busiri's Ithaf, and `compilers_remarks.tsv` (the compiler's own words; class uniqueness or defect_note is a remark, **not a grade**). Modern, apart, in `apparatus/hadith_grades_modern/`: al-Arnaʾut on Ahmad, Husayn Asad on Abu Yaʿla and al-Darimi, al-Albani on Abu Dawud and the Jamiʿ. **Cite a modern verdict as modern, never beside the classical as its equal.** `in_sahih.tsv.gz` now says whether the Companion is the same; `apparatus/hadith_links/weak_links.tsv.gz` lists Ibn Hajar's weak narrators in ungraded chains (evidence, not a grade). `docs/hadith_layer/GRADE_GAP_V47.md` |
| Hadith method, hidden defects, weak narrators, fabricated and current sayings (v45) | `corpus/mustalah/` (Ibn al-Salah, Nukhba, Tadrib ...), `corpus/cilal/` (al-Daraqutni, Ibn Abi Hatim, Ibn ʿAdi ...), `corpus/mawduat/` (Kashf al-khafaʾ, Tanzih al-shariʿa ...), eight more collections in `corpus/hadith_extra/` (al-Bazzar, Abu Yaʿla, al-Tabarani's Awsat and Saghir, Ibn Hibban's Sahih, Shuʿab al-iman, al-Tayalisi, al-Humaydi), in the hadith layer since v46 (21 collections; `docs/hadith_layer/LAYER_V46.md`). All searched by `authenticate.py`. Cautions in `docs/hadith_layer/AUTHENTICATION_CANON.md` (the brackets in al-Mundhiri's Mukhtasar are the modern editor's) |
| Later classical critics | `apparatus/hadith_grades/` (al-Dhahabi on al-Hakim) and `corpus/grading/` (al-Haythami, Ibn Hajar, al-Zaylaʿi, al-Busiri, al-Sakhawi) |
| Soul, grave, afterlife | `corpus/afterlife/` (Ibn al-Qayyim's Ruh, al-Qurtubi's Tadhkira, al-Suyuti, Ibn Rajab, al-Bayhaqi, Ibn Kathir, al-Ghazali's Durra) and al-Alusi in `corpus/tafsir/` |
| Creed by school (Ashʿari, Maturidi, Athari) | `corpus/kalam/`: al-Sanusi, al-Iji with al-Jurjani, al-Bajuri on al-Laqqani, Abu al-Muʿin and Najm al-Din al-Nasafi (with al-Taftazani), al-Tahawi with Ibn Abi al-ʿIzz, Ibn Taymiyya, Ibn Qudama; creed terms via `--concept qada_qadar` etc. |
| The fitra (primordial nature) | `corpus/fitra/`: Ibn Taymiyya's Darʾ, Ibn ʿAbd al-Barr's al-Tamhid (vol. 18 p. 56ff), Ibn al-Qayyim's Shifaʾ al-ʿalil; `--concept fitra` |
| Grammar | `corpus/lugha/`: Sibawayh's Kitab with al-Sirafi's commentary |
| Modern works (cited, not classical) | `corpus/modern/`: al-Albani's two Silsilas and gradings, Ahmad Shakir |
| Any word or phrase | `python3 pipeline/search/textsearch.py "<phrase>" --folder kalam,lugha` (ignores punctuation, vowels and hamza forms; no index needed; `--best-reading` for OCR works). Never raw `zgrep` for Arabic phrases; the full root-aware index is the `search-index` release asset (1.1 GB; `docs/search/README.md`) |
| Rumi, in his own words (v53) | He writes in Persian with his own vocabulary: `corpus/mathnawi/full/` (25,637 couplets, Nicholson numbering), `corpus/rumi/` (Divan-i Shams, Fihi ma fihi, Majalis-i sabʿa). `textsearch.py "مرآة القلب" --folder rumi,mathnawi` now also searches his Persian words for an Arabic term (`catalogs/term_bridge.tsv`); `lookup.py --concept malakut --work rumi,mathnawi` lists his couplets on a concept; the map is `docs/dossiers/rumi.md`. Translate each passage you quote and mark the translation as yours |
| Al-Jilani: his own voice, and the books about him (v55) | `docs/dossiers/jilani.md`. His works (al-Fath al-rabbani, Futuh al-ghayb, al-Ghunya) are one layer; the hagiographies (al-Shattanawfi's Bahja, al-Tadifi's Qalaʾid) are reports about him, generations later: say which you quote. `textsearch.py --work` takes several names since v55 (`--work MajmucFatawa,FurqanBaynaAwliya`) |
| A couplet of the Mathnawi with its story (v54) | `python3 pipeline/mathnawi/story.py 1:263`: Rumi's heading, the story, who speaks, the recorded readings. See section 4c |
| Many sayings at once (v53) | `python3 pipeline/hadith/authenticate.py --brief "<saying>" "<another>" ...`: one short block per saying (collections, grades, critics, and the standing an earlier study already recorded in the sijill). Then run without `--brief` on the few you must read |
| An OCR page's reliability | `reports/collation/confidence.tsv.gz` (level; every OCR work has one: `no_witness` means nothing to check it against) and `apparatus/best_reading/` (corrected reading) |

## 3. Work economically (every tool step re-reads the whole chat, so steps and long outputs cost most)
- **Batch:** put several phrases in one search, one step: `textsearch.py "الفطرة" "لا تبديل" "عالم الذر" --folder fitra,tafsir --count`.
- **Count first, then read a few:** `--count` shows where the hits are; then fetch only what you need with
  `--limit 3 --context 80`. Never print whole files or long passages "to see".
- **Narrow:** `--folder` and `--work` keep searches fast and outputs short. A sparse clone of the folders you need is enough.
- **Start from what exists:** the dossiers, `sijill/views/` (earlier findings) and the indexes before new searches.

## 4. Cite properly
- **Pages (v42):** OpenITI page markers mark the END of a page, so a record starts on `page_before + 1`; lookup,
  search and textsearch now print the true `page`. For a sentence inside a long record, get its exact page with
  `python3 pipeline/search/cite.py <record_id> "<phrase>"` (al-Tamhid's whole fitra chapter, 18:57-97, is one record).
  Several ids in one step (v53): `cite.py --many <id> <id> ...`; hadith-layer ids and Mathnawi couplets resolve too.
- Give the record id (uid) and locator (vol/page or leaf/printed page), the author's death year, and for OCR
  texts the collation level. Say "best reading" when you quote a corrected reading.
- Keep layers apart: **classical grades** (in the texts, and al-Dhahabi's Talkhis) versus **modern grades**
  (al-Albani, Shakir: `category = modern`). Never merge a modern grade into a classical verdict.
- Attribution flags in works_index.tsv (doubtful, spurious) must be stated when quoting those works.
- If a claim is not in the repo, say so: "not in the library" is a finding, not a failure.

## 4b. Never record a master as silent before searching his own language (v53)
A seat of the council is reported silent only after its own language and vocabulary have been searched. For Rumi that
means Persian: the Arabic word is often absent where the teaching is present (the Malakut is عالم امر, لامکان, جهان جان;
the mirror of the heart is آینه دل). In the ether case he was reported silent on the Malakut after an Arabic search; a
Persian search found him at Mathnawi 4:3692-3693. Use the term bridge, then say which words were searched. If a term is
missing from `catalogs/term_bridge.tsv`, add a row. The same holds for any master who uses his own terms (Ibn ʿArabi's
habaʾ for prime matter).

## 4c. A story is quoted with its voice and its layer (v54)
The masters teach by stories, and a couplet lifted from a story can say the opposite of what the master means (the
parrot's analogy at Mathnawi 1:261 is the mistake the story is about). So for every quotation from a story:
- **Get its place:** `python3 pipeline/mathnawi/story.py 1:263 --show 2` prints Rumi's own heading for the section, the
  story it belongs to, and the readings already recorded. `--stories 1` lists the stories of Book 1; `--headings 3` lists
  Rumi's headings for any book (`apparatus/mathnawi/sections.tsv`, all 972 sections).
- **Say who speaks:** the narrator, a character (name him), or the master in his own voice.
- **Say whose reading it is,** by layer (`sijill/registry/layers.tsv`): the plain sense; the author's own stated meaning
  (cite the couplet where he says it); a commentator's; a reader's (Housam's, in his words); Claude's analysis. Never
  give one reading as "the meaning". Several readings of the same passage stand side by side in the sijill
  (types `passage` and `reading`; view: `sijill/views/readings.md`).
- **The text decides:** keep a reading where couplets support it and name them; say where a reading goes beyond the text.

## 5. Record what the study found (the sijill)
End a study with a findings block for `sijill/entries/` (JSON lines; format and registries in docs/sijill/README.md):
the source_event examined (speaker, date), each inference tested, each voice's position on it (affirms / qualifies /
rejects) with the record ids you cited, a verdict per inference, and the open questions. Mark them `draft`. Cite record
ids exactly as the repo gives them: the validator rejects any that do not resolve. Check `sijill/views/` first: if a
voice's position is already recorded, link to it instead of repeating it.

## 6. Feed the stress test
When a study shows something the tools did well or could not do, add a row to `docs/jalasa/STRESS_TEST.md`
(`must` for what worked, `goal` for what did not). It is how the repo learns from each study.

## 7. Report the source mix
End study answers with the tracking table: share from the repo, from general knowledge, from the internet,
and token cost.
