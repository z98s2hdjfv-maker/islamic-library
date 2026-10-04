# Dossier: al-Jilani's voice (ʿAbd al-Qadir al-Jilani, d. 561 AH)

> **A map, not an answer.** This dossier says where al-Jilani speaks in the library and where others speak about him. Before answering, query the repo itself (see `START_HERE.md`), open the records and read around them. Cite from the files, not from this page.

*Why this dossier exists.* The fifth case (a video on his wonders, 2026-10-03) showed that he must be read in two layers that are easily mixed: what he says in his own works, and what later books say about him. Repo state: v55. First dossier of do list item 14.

## 1. What the library holds

**By him**

| Work | Where | Attribution | Note |
|---|---|---|---|
| al-Fath al-rabbani | `corpus/jilani/fathrabbani.jsonl` | secure | sermons taken down by his hearers; Shamela pages follow the print |
| Futuh al-ghayb | `corpus/jilani/futuhghayb.darwish.jsonl`, `.azqul`, `.ilmiyya` | secure | discourses; three editions, the Darwish text is the one cited in the sijill; its closing section has his last illness and death, from his sons |
| al-Ghunya | `corpus/asma/` (`asma.0561CabdQadirJilani.Ghunya`) | secure | manual of law, creed and practice; typed |
| Jalaʾ al-khatir | `corpus/asma/` (`asma.0561CabdQadirJilani.JalaKhatir`) | secure | discourses; uncorrected OCR |
| Sirr al-asrar | `corpus/jilani/sirrasrar.jsonl` | **doubtful** | state the flag when quoting; the seven stages of the soul are found only here |
| Diwan (Arabic), Divan (Persian) | `corpus/jilani/diwan.jsonl`, `diwan.gh.jsonl` | **doubtful** | two different collections |

Seven OpenITI texts of his works are under `corpus/openiti/` (see `catalogs/openiti_catalog.json`).

**About him**

| Work | Where | Note |
|---|---|---|
| al-Shattanawfi (d. 713), Bahjat al-asrar | `corpus/jilani/0713Shattanawfi.BahjatAsrar.jsonl.gz` | the earliest large collection of his wonders; uncorrected OCR with two witness scans: use `--best-reading` |
| al-Tadifi (d. 963), Qalaʾid al-jawahir | `corpus/jilani/qalaid.jsonl` | late; typed; most of the famous stories are easiest to find here |
| al-Sayf al-rabbani | `corpus/jilani/sayf.jsonl` | a later defence of him |
| al-Dhahabi (d. 748), Siyar aʿlam al-nubalaʾ | `corpus/sahaba/0748Dhahabi.SiyarAclamNubala.jsonl.gz`, vol. 20, from `...:p125974` (pages 20:442 to 20:447 are the ones cited here) | the sober biography: Ibn al-Jawzi, Ibn Qudama, Ibn ʿAbd al-Salam, and al-Dhahabi's own verdict |
| Ibn Taymiyya (d. 728) | `corpus/critics/0728IbnTaymiyya.MajmucFatawa.jsonl.gz`; al-Furqan in `corpus/wilaya/` | quotes him often and with respect |

## 2. How to reach him
```
python3 pipeline/search/textsearch.py "صدأ القلوب" "تؤلمني" --folder jilani --count
python3 pipeline/search/textsearch.py "عبد القادر" --work MajmucFatawa,FurqanBaynaAwliya --count      # the critic on him (several works: v55)
python3 pipeline/search/textsearch.py "الدجاجة" --work qalaid,BahjatAsrar --best-reading --limit 3     # a story, in both hagiographies
python3 pipeline/index/lookup.py --repo . --concept abdal --work jilani
```

## 3. Where he speaks, by subject (a first selection)

| Subject | Record | What is there |
|---|---|---|
| Surrender: the slave has no choice beside his master | `urn:shamela:jilani.fathrabbani:r00258` (p. 258) | the story of the bought slave who answers "whatever you give me" |
| Do not always wish your state changed | `urn:shamela:jilani.fathrabbani:r00019` (p. 20) | the sick man and health |
| Ask Him alone | `urn:shamela:jilani.futuhghayb.darwish:r00187` (p. 182) | "you ask Him and you ask no one else" |
| The rust of hearts | al-Fath al-rabbani, sermon 23 (`...fathrabbani:r00106`) | the heart blackens through its distance from the light (heart case) |
| The abdal: one whose will is exchanged for God's | Futuh al-ghayb, discourse 6 (`...futuhghayb.darwish:r00079`) | see the wilaya dossier, section 3 |
| His death | `urn:shamela:jilani.futuhghayb.darwish:r00034` (p. 30) | "all my limbs pain me except my heart"; last words the shahada |
| The soul that blames | `urn:shamela:jilani.fathrabbani:r00349` | only the Qur'anic lawwama; no seven stages |

## 4. What others say of him

| Voice | Record | Standing |
|---|---|---|
| Ibn Taymiyya: the light that said "I am your Lord"; seventy were misled by the like of it; he knew the devil because the law is not abrogated | `urn:openiti:0728IbnTaymiyya.MajmucFatawa.JK000381-ara1:p00597` (1:172), `:p17418` (11:289); al-Furqan `...FurqanBaynaAwliya.Shamela0021499-ara1:p01000` | told as true, as a rule for testing wonders; no chain given |
| Ibn Qudama: "I never heard of anyone of whom more karamat are told" | Siyar `...:p125992` (20:442) | an eyewitness of his last days |
| Ibn ʿAbd al-Salam: no one's karamat reached us by mass transmission but his | Siyar `...:p126014` (20:443) | |
| Ibn al-Jawzi: he took over al-Mukharrimi's school and taught and preached there until he died | Siyar `...:p125990` | a contemporary |
| al-Dhahabi: "great in rank, with objections to some of his sayings and claims... and some of that is falsely ascribed to him" | Siyar `...:p126086` (vol. 20) | honours the man, does not accept every report |
| Dates: born 471, lived ninety years, died 10 Rabiʿ II 561 | Siyar `...:p125974`, `:p126083` | |

## 5. The famous stories and where they stand

Found in the hagiographies (Qalaʾid record; also in the Bahja): the infant who would not nurse in Ramadan (`qalaid:r00005`, `r00006`); the ox on the day of ʿArafa and the forty dinars (`r00014`); twenty-five years in the wilds (`r00029`, `r00017`); Khidr's seven years (`r00006`); the chicken's bones (`r00058`); the jinn and the abducted girl (`r00049`). Seventy thousand at his gathering is in al-Dhahabi (`:p126058`, 20:447).

Not found by the wordings searched in the fifth case: the dead man raised for the Christian, the locksmith's other life, iftar in many houses at once, the drunk man's three questions, Hizb al-Nasr, the robe left for Naqshband, the move from the Shafiʿi school after a dream. "Not found" is a finding about the search, not about the story: the Bahja is OCR.

Full table: `docs/jalasa/cases/2026-10-03-jilani-karamat.md`. Sijill: `study:2026-10-03-jilani-karamat` and the entries `jk-...`.

## 6. Cautions

- **Two layers.** A sentence from al-Fath al-rabbani or Futuh al-ghayb is his voice. A story from the Bahja or the Qalaʾid is a report about him, generations later; say which.
- **A name that misleads.** "Bahjat al-asrar" in al-Dhahabi's Siyar (`:p110267`) and Mizan is the book of Ibn Jahdam ("he was weak"), not al-Shattanawfi's.
- **Doubtful works.** Sirr al-asrar and both diwans carry the doubtful flag.
- **His school.** He was Hanbali in law, taught by al-Mukharrimi; Ibn Taymiyya quotes him with respect.

## 7. Gaps and open questions

- Missing: Ibn Rajab's Dhayl Tabaqat al-Hanabila (the critical Hanbali biography and its verdict on the Bahja; do list 66); Sirhindi's letters (67); the litanies ascribed to him (68).
- Open (sijill `open_question:jk-...`): the stories in the Bahja itself with their chains; calling on a saint after his death; the seven stages of the soul; a prophet's miracle as a saint's karama.
- The selection in section 3 is Claude's and small. It has not been reviewed by a scholar.
