# Arabic sources for Ibn 'Arabi, al-Jilani and al-Ghazali (updated 2026-09-26)

## v10 import (2026-09-26): typed uploads, the Ihya' with al-'Iraqi, and the critical editions (OCR)
- ingest_misc.py:
  - Checks each archive.org file against its md5 and copies it byte-exact.
  - txt: one row per line. docx: one row per paragraph. OCR: one row per scanned leaf, with the printed page number archive.org detected.
  - Catalogue: works/misc_catalog_v10.json. Zip: library_v10_arabic_more_2026-09-26.zip.
- Typed Ibn 'Arabi. These come from archive.org uploader almussafer1@gmail.com, who posts .docx/.txt files with PDFs of Ibn 'Arabi and Akbarian texts; the edition is not always stated:
  - Insha' al-dawa'ir + 'Uqlat al-mustawfiz + al-Tadbirat al-ilahiyya
  - 'Anqa' mughrib (ed. Bahnasawi)
  - Taj al-tarajim
  - Kitab al-Tajalliyat with Ibn Sawdakin's notes
  - al-Tanazzulat al-Mawsiliyya
  - Muhadarat al-abrar, 2 volumes, flagged doubtful
  - Manzil al-manazil al-fahwaniyya
- Shamela .bok:
  - Ihya' with al-'Iraqi's takhrij (archive.org item Bok00118). This gives hadith gradings for the Ihya'.
  - Khwaja Muhammad Parsa's Sharh Fusus al-hikam, a Persian commentary (ed. Misgarnizhad, Tehran 1987).
- Critical editions. Archive.org item Futuhat-Fusus-Critical-editions has the publisher PDFs:
  - al-Futuhat al-Makkiyya, ed. Sultan al-Mansub (Yemen 2010, Konya autograph), 234 MB.
  - Fusus al-hikam, ed. Sayyid Nizam al-Din Ahmad (Cairo 2015).

  Their embedded text layer is scrambled (DecoType fonts: glyph order and vowel marks broken), so only archive.org's OCR was imported: 8,242 leaves and 520 leaves, source_type ocr_uncorrected. The OCR is readable but has frequent errors in the vocalised text. The PDFs themselves must be downloaded from archive.org directly: too big for chat, and they serve as the reference scans.
- Rejected:
  - 'Ayyuha al-walad' docx (it is an English translation).
  - Word-generated PDFs of Kitab al-Mim wa-l-waw wa-l-nun, al-I'lam bi-isharat and Ayyam al-sha'n. pdftotext breaks lam-alif. These three are already in the 'Uthmaniyya Rasa'il.
  - Scanned "Text PDFs" of the Tarjuman and the Fusus (Acrobat OCR).
- Other useful uploads by the same uploader, not imported:
  - Akbarian commentaries: Jili, Qunawi, Qashani, Muhayimi's Mashra' al-khusus.
  - Arabic translations of the Mathnawi by Ibrahim al-Dasuqi and Muhammad al-Kafafi, which could serve as an Arabic layer for the Rumi corpus.

## v9 import (2026-09-26): typed Shamela books from archive.org
- "للشاملة" items on archive.org carry the original Shamela .bok (MS Access) in a small RAR: typed, with page numbers matching the print. The _djvu.txt / EPUB files on the same items are OCR of the scans; do not use them.
- ingest_shamela.py checks the md5, unpacks (unar, or bsdtar for RAR5), copies the .bok byte-exact and exports JSONL rows with part/page and headings. Manifest: works/shamela_manifest.json.
- al-Jilani:
  - al-Fath al-rabbani.
  - Futuh al-ghayb in 3 editions (al-Darwish, 'Azqul, 'Ilmiyya).
  - Sirr al-asrar and the Diwan: doubtful.
  - Qala'id al-jawahir and al-Sayf al-rabbani: "about" (not by him).
- Ibn 'Arabi:
  - Futuhat, Cairo print (Dar al-Kutub al-'Arabiyya al-Kubra, 4 volumes).
  - Rasa'il: Hyderabad 'Uthmaniyya (29 treatises) and its Ihya' al-Turath reprint.
  - Majmu'at rasa'il (Mahajja, about 26 items), and the Rasa'il ed. 'Abbas and 'Ajil.
  - Khalwa and Mubashshirat (both ed. 'Abduh).
  - The 'Tafsir' (al-Qashani): spurious.
  - Rahma min al-Rahman: modern compilation.
  - Jami's Sharh al-Fusus and Naqd al-nusus: commentaries.
- al-Ghazali: al-Arba'in fi usul al-din; Mukashafat al-qulub (spurious).

## v8 import (2026-09-25): OpenITI
- 41 works from OpenITI GitHub at pinned commits (0525AH 6290621b, 0575AH 298735a1, 0650AH 287c0cc3). See works/openiti_catalog.json.
- Primary versions: Ghazali 25 typed + 2 OCR; Jilani 1 typed + 5 OCR + 1 scraped; Ibn 'Arabi 3 typed + 4 OCR.

## Still missing or weak
- Ibn 'Arabi:
  - A typed Fusus on its own. The best text now is inside Jami's and Parsa's commentaries, plus the uncorrected OCR of the critical edition.
  - Tarjuman al-ashwaq in typed form (OpenITI's Diwan may partly cover it).
  - Mawaqi' al-nujum and Ruh al-quds exist only inside the Mahajja collection.
- al-Ghazali: the Dar al-Minhaj critical Ihya'; an Arabic Ayyuha al-walad.
- al-Jilani: Jala' al-khatir, OCR only.
- Possible next step: correct the OCR of the critical Fusus, which is short at 520 pages, by checking it against the typed Fusus text inside Jami's commentary.
