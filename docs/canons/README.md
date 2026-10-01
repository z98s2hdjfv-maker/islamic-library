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

## creed: the Sunni schools of creed, and grammar (v36; corpus/kalam, corpus/lugha)
Each school's position can now be quoted from its own texts, each primer with its standard commentary:
- **Ashʿari:** al-Sanusi's Umm al-barahin (the scheme of necessary, impossible and possible attributes behind
  the thirteen taught today), his three creeds and his commentary on the Muqaddimat; al-Ashʿari's Lumaʿ and
  Risala ila ahl al-thaghr; al-Razi's Arbaʿin fi usul al-din; al-Iji's Mawaqif with al-Jurjani's commentary;
  al-Bajuri's Tuhfat al-murid on al-Laqqani's Jawharat al-tawhid (archive.org OCR).
- **Maturidi:** Abu al-Muʿin al-Nasafi's Tamhid and Bahr al-kalam; al-Taftazani's commentary on Najm al-Din
  al-Nasafi's ʿAqaʾid (archive.org OCR, fair; a second scan can serve as a collation witness).
- **Athari:** al-Tahawi's creed (read by all three schools) with Ibn Abi al-ʿIzz's Athari commentary; Ibn
  Taymiyya's Wasitiyya; Ibn Qudama's Lumʿat al-iʿtiqad.
- Already in corpus/kalam since v14: al-Ashʿari's Ibana and Maqalat, al-Maturidi's Tawhid, al-Taftazani's
  Sharh al-Maqasid; al-Ghazali's Iqtisad is in corpus/openiti.
- **Grammar (corpus/lugha):** Sibawayh's al-Kitab with al-Sirafi's commentary.
Seven of the new texts are OCR (five are OpenITI's own Kraken OCR, the only versions it has): check the
source_type in works_index.tsv before quoting. Creed terms are in the concept index (area = creed); they match
words, not senses (al-qadar is also "measure"), so read the passage.

## fitra: the primordial nature (v40; corpus/fitra)
The three classical works that treat "every child is born on the fitra" (al-Bukhari, Muslim) and Q30:30 at length:
- **Ibn Taymiyya, Darʾ taʿarud al-ʿaql wa-l-naql** (typed): his longest treatment of the fitra as innate
  knowledge and love of God, which reason supports and messengers complete; 36 passages quote the hadith.
- **Ibn ʿAbd al-Barr, al-Tamhid** (typed): the classic survey of every reading of the hadith, vol. 18 p. 56ff
  (p01516), incl. the view that the child is born "on soundness (salama), with neither faith nor unbelief,
  neither knowledge nor denial", which he calls the most correct; earlier only reached through al-Qurtubi.
- **Ibn al-Qayyim, Shifaʾ al-ʿalil** (typed): a long chapter weighing the readings; also qadar and human acts.
Concept: `--concept fitra` (forms الفطرة, فطرة الله, على الفطرة; zakat al-fitr is a different word and not matched).
