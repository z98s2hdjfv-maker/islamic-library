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
