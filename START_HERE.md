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
| **Is this saying authentic?** (start here for any quoted hadith or saying) | `python3 pipeline/hadith/authenticate.py "<saying>" "<another>"` (v43): loose-wording match in the 13 collections with grades, parallels and chain, then the classical critics oldest first, then modern grades apart. Several sayings in one pass, about 25 s. It gathers evidence and does not grade: read the passages. `docs/hadith_layer/AUTHENTICATE.md` |
| The later critics' verdict on a hadith, as data (v44) | shown by `authenticate.py` under each hadith; tables in `apparatus/hadith_grades/` (al-Busiri on Ibn Maja, al-Haythami on Ahmad and al-Tabarani, al-Dhahabi on al-Hakim), modern apart in `apparatus/hadith_grades_modern/` (al-Albani on al-Tirmidhi). **A verdict with scope = chain is about that chain, not the hadith; quote his words and cite `critic_record`.** Critics' numbered entries on current sayings: `apparatus/sayings/sayings.tsv.gz`. `docs/hadith_layer/CRITIC_GRADES.md` |
| A hadith and its grades | `zgrep` in `apparatus/hadith/*.jsonl.gz` (narrator, caliph, grades in the sources, parallels). **Cite the printed number** in `edition_numbers` where present (al-Tirmidhi: Shakir; al-Bukhari: Fath al-Bari), not the layer's own `number` |
| Hadith method, hidden defects, weak narrators, fabricated and current sayings (v45) | `corpus/mustalah/` (Ibn al-Salah, Nukhba, Tadrib ...), `corpus/cilal/` (al-Daraqutni, Ibn Abi Hatim, Ibn ʿAdi ...), `corpus/mawduat/` (Kashf al-khafaʾ, Tanzih al-shariʿa ...), more collections in `corpus/hadith_extra/` (al-Bazzar, Abu Yaʿla, al-Tabarani's Awsat, Ibn Hibban's Sahih, Shuʿab al-iman: text only, not in the hadith layer yet). All searched by `authenticate.py`. Cautions in `docs/hadith_layer/AUTHENTICATION_CANON.md` (the brackets in al-Mundhiri's Mukhtasar are the modern editor's) |
| Later classical critics | `apparatus/hadith_grades/` (al-Dhahabi on al-Hakim) and `corpus/grading/` (al-Haythami, Ibn Hajar, al-Zaylaʿi, al-Busiri, al-Sakhawi) |
| Soul, grave, afterlife | `corpus/afterlife/` (Ibn al-Qayyim's Ruh, al-Qurtubi's Tadhkira, al-Suyuti, Ibn Rajab, al-Bayhaqi, Ibn Kathir, al-Ghazali's Durra) and al-Alusi in `corpus/tafsir/` |
| Creed by school (Ashʿari, Maturidi, Athari) | `corpus/kalam/`: al-Sanusi, al-Iji with al-Jurjani, al-Bajuri on al-Laqqani, Abu al-Muʿin and Najm al-Din al-Nasafi (with al-Taftazani), al-Tahawi with Ibn Abi al-ʿIzz, Ibn Taymiyya, Ibn Qudama; creed terms via `--concept qada_qadar` etc. |
| The fitra (primordial nature) | `corpus/fitra/`: Ibn Taymiyya's Darʾ, Ibn ʿAbd al-Barr's al-Tamhid (vol. 18 p. 56ff), Ibn al-Qayyim's Shifaʾ al-ʿalil; `--concept fitra` |
| Grammar | `corpus/lugha/`: Sibawayh's Kitab with al-Sirafi's commentary |
| Modern works (cited, not classical) | `corpus/modern/`: al-Albani's two Silsilas and gradings, Ahmad Shakir |
| Any word or phrase | `python3 pipeline/search/textsearch.py "<phrase>" --folder kalam,lugha` (ignores punctuation, vowels and hamza forms; no index needed; `--best-reading` for OCR works). Never raw `zgrep` for Arabic phrases; the full root-aware index is the `search-index` release asset (1.1 GB; `docs/search/README.md`) |
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
- Give the record id (uid) and locator (vol/page or leaf/printed page), the author's death year, and for OCR
  texts the collation level. Say "best reading" when you quote a corrected reading.
- Keep layers apart: **classical grades** (in the texts, and al-Dhahabi's Talkhis) versus **modern grades**
  (al-Albani, Shakir: `category = modern`). Never merge a modern grade into a classical verdict.
- Attribution flags in works_index.tsv (doubtful, spurious) must be stated when quoting those works.
- If a claim is not in the repo, say so: "not in the library" is a finding, not a failure.

## 5. Record what the study found (the sijill)
End a study with a findings block for `sijill/entries/` (JSON lines; format and registries in docs/sijill/README.md):
the source_event examined (speaker, date), each inference tested, each voice's position on it (affirms / qualifies /
rejects) with the record ids you cited, a verdict per inference, and the open questions. Mark them `draft`. Cite record
ids exactly as the repo gives them: the validator rejects any that do not resolve. Check `sijill/views/` first: if a
voice's position is already recorded, link to it instead of repeating it.

## 6. Report the source mix
End study answers with the tracking table: share from the repo, from general knowledge, from the internet,
and token cost.
