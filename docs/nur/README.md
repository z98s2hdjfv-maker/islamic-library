# Nur canon — the Muhammadan Light and Reality (v19 + v20)

17 works from OpenITI on *al-nūr al-muḥammadī* / *al-ḥaqīqa al-muḥammadiyya*, and on the philosophy of
light, intellect and prime matter that Ibn ʿArabī engages in Futūḥāt ch. 6 (I:118–19), where the
Muhammadan reality, "called the Intellect," is the first receiver of God's light in the *habāʾ*, which
"the people of thought call the universal hyle."

- List, strand and role per work: `catalogs/nur_canon.tsv` (chosen by Claude; scholar review pending)
- Exact versions: `catalogs/nur_canon_pins.json` (repo, commit, path, sha256; the build refuses mismatches)
- Corpus: `corpus/nur/<book>.jsonl.gz`; raw files: `sources/openiti/nur/`; search with `--author nur`
- Rebuild: `python3 pipeline/works/ingest_nur_canon.py --repo . --build` (v19, OpenITI) and
  `python3 pipeline/works/ingest_nur_archive.py --repo . --build` (v20, archive.org)

| Strand | Works |
|---|---|
| theory | Ibn Sabʿīn, *Anwār al-Nabī*; al-Qūnawī, *Miftāḥ al-ghayb* and *al-Nuṣūṣ*; al-Fanārī, *Miṣbāḥ al-uns*; al-Jīlī, *al-Kamālāt al-ilāhiyya fī al-ṣifāt al-Muḥammadiyya*; al-Ghazālī, *Mishkāt al-anwār*; Bursevi, *Rūḥ al-bayān* |
| poetry | Ibn al-Fāriḍ, *Dīwān* (incl. the Tāʾiyya); al-Būṣīrī, *Dīwān* (incl. the Burda) |
| sira | al-Qasṭallānī, *al-Mawāhib al-laduniyya*; al-Zurqānī, *Sharḥ al-Mawāhib*; al-Suyūṭī, *al-Khaṣāʾiṣ al-kubrā*; Abū Nuʿaym, *Dalāʾil al-nubuwwa* |
| philosophy | Ikhwān al-Ṣafāʾ, *Rasāʾil*; Ibn Sīnā, *al-Shifāʾ: Ilāhiyyāt* and *Ṭabīʿiyyāt*; al-Ghazālī, *Tahāfut al-falāsifa* |

Already in the repo and central here (not duplicated): Futūḥāt ch. 6 (`futuhat.arabiyya` r00119–120),
Fuṣūṣ, Sahl al-Tustarī's Tafsīr, Qāḍī ʿIyāḍ's Shifāʾ, al-Bayhaqī's Dalāʾil, al-Suyūṭī's Ḥāwī (the "Pen" report, I:343).

## Verified starting points (checked at import)
| Where | What |
|---|---|
| MawahibLaduniyya p00138 (I:47) | the Jābir report ("the first thing God created was the light of your Prophet"), attributed to ʿAbd al-Razzāq *bi-sanadih*, with no chain given |
| SharhCalaMawahib p00282–289 (I:88–91) | the same report, then "it is disputed whether the Pen is the first creation after the Muhammadan light" |
| KhasaisKubra | "while Adam was between spirit and body" with its routes (5 units) |
| MisbahUns, KamalatIlahiyya | *al-ḥaqīqa al-muḥammadiyya* (6 units each) |
| ShifaIlahiyyat | *al-ʿaql al-awwal* (the First Intellect) |
| Rasail (Ikhwān) | *al-hayūlā al-ūlā* (31 units) |

## Caveats
- The Jābir report is in no ḥadīth collection in the repo; do not cite it as ḥadīth without its critics.
- The OpenITI Zurqānī (Shamela0026568, 12 vols, ~2.2M chars) appears to carry mainly the Mawāhib text;
  his commentary may be partly missing. Check before relying on it for his verdicts.
- Uncorrected OCR: al-Qūnawī's *al-Nuṣūṣ*, al-Jīlī's *Kamālāt*.
- v20 added from archive.org OCR (see below). Still missing: al-Qūnawī's *al-Fukūk* and *Iʿjāz al-bayān*,
  al-Jandī's Fuṣūṣ commentary, Mullā Ṣadrā's *Asfār*, and the ḥadīth critics' treatments of the Jābir report.

## v20: archive.org scans (`catalogs/nur_archive.tsv`)
Not in OpenITI, so the text is archive.org's own tesseract OCR of a scanned edition, one row per leaf
with the printed page archive.org detected. `source_type = ocr_uncorrected`: always check the scan
(item id is in each row's provenance) before quoting. Each file is pinned by md5.

| Work | Leaves | archive.org item |
|---|---|---|
| al-Jīlī, *al-Insān al-kāmil* | 296 | AlInsanAlKamilByAbdulKarimAlJiliArabic |
| al-Qayṣarī, *Sharḥ Fuṣūṣ al-ḥikam* (with his Muqaddima) | 1418 | 20240130_20240130_1102 |
| al-Qāshānī, *Sharḥ Fuṣūṣ al-ḥikam* | 350 | 20260328_20260328_0603 |
| al-Farghānī, *Muntahā al-madārik* (Tāʾiyya) | 834 | baha-2026-06 (typeset scan of four) |
| al-Qayṣarī, *Sharḥ al-Tāʾiyya* | 223 | 1989_20210820_202108 |
| al-Qāshānī, *Kashf al-wujūh al-ghurr* (Tāʾiyya) | 279 | 20240214_20240214_2020 |
| al-Suhrawardī, *Ḥikmat al-ishrāq* | 249 | Hekmataleshraq |

Verified starting points: al-Qayṣarī's Muqaddima ch. 9, "on the vicegerency of the Muhammadan reality
and that it is the Pole of Poles" (contents, leaf 5); al-Jīlī on the Muhammadan spirit, called the
Supreme Pen and the First Intellect (leaf 151); al-Qāshānī (Tāʾiyya, leaf 18): the Supreme Spirit is
"the First Intellect, the Muhammadan reality, the single soul"; al-Qayṣarī (Tāʾiyya, p. 100): the first
of the fixed entities is "the Pole of Poles, the Muhammadan reality"; Suhrawardī, *Nūr al-anwār* (45 leaves).
