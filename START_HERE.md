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
| A key term across the works | `python3 pipeline/index/lookup.py --repo . --concept qutb` (list: `reports/index/concept_summary.tsv`) |
| A hadith and its grades | `zgrep` in `apparatus/hadith/*.jsonl.gz` (narrator, caliph, grades in the sources, parallels). **Cite the printed number** in `edition_numbers` where present (al-Tirmidhi: Shakir; al-Bukhari: Fath al-Bari), not the layer's own `number` |
| Later classical critics | `apparatus/hadith_grades/` (al-Dhahabi on al-Hakim) and `corpus/grading/` (al-Haythami, Ibn Hajar, al-Zaylaʿi, al-Busiri, al-Sakhawi) |
| Soul, grave, afterlife | `corpus/afterlife/` (Ibn al-Qayyim's Ruh, al-Qurtubi's Tadhkira, al-Suyuti, Ibn Rajab, al-Bayhaqi, Ibn Kathir, al-Ghazali's Durra) and al-Alusi in `corpus/tafsir/` |
| Creed by school (Ashʿari, Maturidi, Athari) | `corpus/kalam/`: al-Sanusi, al-Iji with al-Jurjani, al-Bajuri on al-Laqqani, Abu al-Muʿin and Najm al-Din al-Nasafi (with al-Taftazani), al-Tahawi with Ibn Abi al-ʿIzz, Ibn Taymiyya, Ibn Qudama; creed terms via `--concept qada_qadar` etc. |
| Grammar | `corpus/lugha/`: Sibawayh's Kitab with al-Sirafi's commentary |
| Modern works (cited, not classical) | `corpus/modern/`: al-Albani's two Silsilas and gradings, Ahmad Shakir |
| Any word or phrase | `python3 pipeline/search/textsearch.py "<phrase>" --folder kalam,lugha` (ignores punctuation, vowels and hamza forms; no index needed; `--best-reading` for OCR works). Never raw `zgrep` for Arabic phrases; the full root-aware index is the `search-index` release asset (1.1 GB; `docs/search/README.md`) |
| An OCR page's reliability | `reports/collation/confidence.tsv.gz` (level; every OCR work has one: `no_witness` means nothing to check it against) and `apparatus/best_reading/` (corrected reading) |

## 3. Cite properly
- Give the record id (uid) and locator (vol/page or leaf/printed page), the author's death year, and for OCR
  texts the collation level. Say "best reading" when you quote a corrected reading.
- Keep layers apart: **classical grades** (in the texts, and al-Dhahabi's Talkhis) versus **modern grades**
  (al-Albani, Shakir: `category = modern`). Never merge a modern grade into a classical verdict.
- Attribution flags in works_index.tsv (doubtful, spurious) must be stated when quoting those works.
- If a claim is not in the repo, say so: "not in the library" is a finding, not a failure.

## 4. Report the source mix
End study answers with the tracking table: share from the repo, from general knowledge, from the internet,
and token cost.
