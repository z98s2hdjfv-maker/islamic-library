# Concept index (v30)

`catalogs/concepts.tsv` lists 30 key terms of our study (the hidden hierarchy, the Muhammadan Light and Reality,
the Names, the address to God), each with its Arabic forms and a note on known ambiguities.
`pipeline/index/build_concept_index.py` finds every passage using them across the Sufi, nūr, wilāya and asmāʾ
collections, the commentaries, al-Ghazālī, Ibn Taymiyya and the ḥadīth: `reports/index/concept_index.tsv.gz`
(concept, work, record, occurrences) and `reports/index/concept_summary.tsv` (per concept: works, passages, top works).

    python3 pipeline/index/lookup.py --repo . --concept qutb --work wilaya,ibnarabi
    python3 pipeline/index/lookup.py --repo . --concept kawn_jami --work nur,ibnarabi --per-work 2

`--work` narrows to collections or work keys. The Futūḥāt is held in four versions, so it can appear up to four
times. works_meta.tsv now gives the right death year for commentaries kept in an author's folder (Jāmī 898,
al-Qāshānī 736, Pārsā 822). First dossier: `docs/dossiers/asma.md` (the Names).


## v38: sense filter and precision
Many concept terms have everyday senses: al-qadaʾ is also a judgeship and making up a missed fast, al-afrad also
al-Daraqutni's Afrad and logical "individuals", al-muʿallaq also a hadith with a suspended chain, al-wilaya also a
governorship, al-kasb also earning a living. concepts.tsv now has two columns, `cues` and `exclude`: a single-word
form counts only if a cue word is within about 25 words and no exclude word is; phrases always count.
`concept_summary.tsv` shows raw_passages, passages (kept) and kept_share for every concept.
Measured by hand on random samples (reports/index/concept_precision.tsv), before -> after:
qada_qadar 8/12 -> 10/12; afrad 0/8 -> 6/7; wilaya 5/8 -> 10/10; kasb 2/8 -> 10/10; abdal 7/8 -> 9/10 (exclusions
only, since cues cost recall); muallaq_mubram now phrases only (the bare words were ~97% other senses).
To audit a concept: `python3 pipeline/index/build_concept_index.py --repo . --audit qutb [--raw] --n 20`.
It is still word matching: read the passage before citing a hit as the technical term.
