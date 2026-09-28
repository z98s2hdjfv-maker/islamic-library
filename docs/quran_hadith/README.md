# v15: Quran, ḥadīth and tafsīr

26 works from OpenITI, pinned to exact commits and SHA-256 (`catalogs/quran_hadith_canon_pins.json`), built by `pipeline/works/ingest_quran_hadith.py`. List drafted by Claude; a scholar should review it.

## Quran

- `corpus/quran/0001Quran.Mushaf.jsonl.gz`: one record per verse (6,236), id `urn:quran:<sura>:<aya>`, the reference spine every other text can point to.
- `text`: Tanzil Simple Clean v1.1 (via OpenITI). OpenITI adds the basmala to verse 1 of suras 2–114 (except 9); it is removed so the text matches Tanzil verbatim.
- `text_uthmani` (with diacritics) is added when the workflow can download it from tanzil.net; see `catalogs/quran_tanzil_uthmani.json`.
- Tanzil text: © Tanzil Project, CC BY 3.0, https://tanzil.net. Changing the text is not allowed; the full notice is kept in the source file.

## Ḥadīth

- al-Bukhārī, `0256Bukhari.Sahih` (ṣaḥīḥ; JK000110-ara1)
- Muslim, `0261Muslim.Sahih` (ṣaḥīḥ; Shamela0001727-ara1)
- Abū Dāwūd, `0275AbuDawudSijistani.Sunan` (sunan; JK000142-ara1)
- al-Tirmidhī, `0279Tirmidhi.Sunan` (sunan (jāmiʿ); JK000140-ara1) — al-Tirmidhī grades hadiths in the text itself
- al-Nasāʾī, `0303Nasai.SunanSughra` (sunan (al-Mujtabā); JK000130-ara1)
- al-Nasāʾī, `0303Nasai.SunanKubra` (sunan; JK000475-ara1)
- Ibn Māja, `0273IbnMaja.Sunan` (sunan; JK000141-ara1)
- Aḥmad ibn Ḥanbal, `0241IbnHanbal.Musnad` (musnad; Shamela0025794-ara1) — arranged by Companion: the largest source for each Companion's own narrations
- al-Dārimī, `0255CabdAllahDarimi.Sunan` (sunan; JK000842-ara1)
- al-Dāraquṭnī, `0385Daraqutni.Sunan` (sunan; JK000477-ara1) — with his isnād criticism
- Ibn Khuzayma, `0311IbnKhuzaymaNaysaburi.Sahih` (ṣaḥīḥ; JK000132-ara1)
- al-Ḥākim, `0405HakimNaysaburi.Mustadrak` (mustadrak; JK000467-ara1) — al-Ḥākim's grades are lenient; al-Dhahabī's notes where present
- al-Ṭabarānī, `0360Tabarani.MucjamKabir` (muʿjam by Companion; JK000474-ara1) — arranged by Companion
- al-Baghawī, `0510IbnMascudBaghawi.SharhSunna` (ḥadīth with commentary; JK009152-ara1)
- al-Nawawī, `0676Nawawi.RiyadSalihin` (selection (ethics); Shamela0012014-ara1)
- al-Nawawī, `0676Nawawi.ArbacunaNawawiyya` (forty hadith; Shamela0012836-ara1)

## Tafsīr

- al-Ṭabarī, `0310Tabari.JamicBayan` (tafsīr bi-l-maʾthūr; Shamela0007798-ara1) — preserves Companion and Successor tafsīr with isnāds
- Ibn Abī Ḥātim, `0327IbnAbiHatimRazi.Tafsir` (tafsīr bi-l-maʾthūr; JK006474-ara1)
- al-Suyūṭī, `0911Suyuti.DurrManthur` (tafsīr bi-l-maʾthūr; Shamela0012884-ara1) — collects reports from the Companions verse by verse
- Ibn Kathīr, `0774IbnKathir.TafsirQuran` (tafsīr; Shamela0008473-ara1)
- al-Baghawī, `0510IbnMascudBaghawi.Tafsir` (tafsīr; Shamela0000041-ara1)
- Fakhr al-Dīn al-Rāzī, `0606FakhrDinRazi.MafatihGhayb` (theological tafsīr; JK006478-ara1)
- al-Zamakhsharī, `0538JarAllahZamakhshari.Kashshaf` (linguistic tafsīr; JK001496-ara1) — Muʿtazilī author; read with that in mind
- al-Bayḍāwī, `0685NasirDinBaydawi.AnwarTanzil` (tafsīr; Tafsir01006-ara1)
- al-Maḥallī and al-Suyūṭī, `0911Suyuti.TafsirJalalayn` (concise tafsīr; JK000818-ara1)

## Already elsewhere in the library

- Mālik, *al-Muwaṭṭaʾ*: `corpus/maliki/`
- al-Qurṭubī, legal tafsīr, and the *Aḥkām al-Qurʾān* works: v14 `corpus/tafsir_ahkam/`
- Sufi tafsīr (al-Sulamī, al-Qushayrī, al-Tustarī): v14 `corpus/tafsir_sufi/`; Maybudī: `corpus/maybudi/`

## Not yet included

- Standard ḥadīth numbering and per-ḥadīth grades as structured fields. The texts carry their authors' own grades (al-Tirmidhī, al-Dāraquṭnī, al-Ḥākim) inline; a numbering and grading layer is the next step.
- Ṣaḥīḥ Ibn Ḥibbān: not in OpenITI.
- English translations: only public-domain ones (e.g. Pickthall 1930) can be added.
