# Canons added in v35

Built by `pipeline/works/ingest_canon.py` from `catalogs/<canon>_canon.tsv` (pinned in `<canon>_canon_pins.json`).

## grading: later classical critics (8 works, corpus/grading)
al-Hakim's Mustadrak **with al-Dhahabi's Talkhis inline** (Shamela edition), al-Haythami's Majmaʿ al-zawaʾid,
Ibn Hajar's al-Talkhis al-habir, al-Zaylaʿi's Nasb al-raya, al-Busiri's Ithaf al-khiyara and Misbah al-zujaja,
al-Sakhawi's al-Maqasid al-hasana, al-Dhahabi's abridgment of Ibn al-Jawzi's Mawduʿat.
al-Dhahabi's 5,711 verdicts are extracted to `apparatus/hadith_grades/dhahabi_talkhis_mustadrak.tsv`; 5,618 are
joined by text to the hadith layer and appear in the search index's grades as "al-Dhahabi (Talkhis): ...".
The other critics are searchable as texts; joining their gradings to the hadith layer is future work.

## afterlife: soul, grave and the next life (11 works in corpus/afterlife, plus al-Alusi in corpus/tafsir)
Ibn al-Qayyim's Kitab al-Ruh, al-Qurtubi's al-Tadhkira, al-Suyuti's Sharh al-sudur and al-Budur al-safira,
Ibn Rajab's Ahwal al-qubur, al-Bayhaqi's al-Baʿth wa-l-nushur, Ibn Kathir's al-Nihaya fi al-fitan, three works of
Ibn Abi al-Dunya, al-Ghazali's al-Durra al-fakhira (archive.org OCR: no witness yet), and al-Alusi's Ruh al-maʿani
(indexed as a commentary, so `--verse 7:172` returns it).

## modern: cited today, not classical (6 works, corpus/modern, category = modern)
al-Albani (d. 1420/1999): Silsilat al-ahadith al-sahiha and al-daʿifa (archive.org OCR, all volumes), his
gradings of al-Tirmidhi and of al-Adab al-mufrad; Ahmad Shakir (d. 1377/1958): al-Baʿith al-hathith.
**Rule:** modern works are a separate layer. Their gradings are never merged into the hadith layer's grades or
into the classical critics'. Cite them as "al-Albani grades it ..." alongside, never instead of, the classical
verdicts. al-Arnaʾut's gradings of the Musnad are not available in a free machine-readable form.
