# Nur canon — the Muhammadan Light and Reality (v19)

17 works from OpenITI on *al-nūr al-muḥammadī* / *al-ḥaqīqa al-muḥammadiyya*, and on the philosophy of
light, intellect and prime matter that Ibn ʿArabī engages in Futūḥāt ch. 6 (I:118–19), where the
Muhammadan reality, "called the Intellect," is the first receiver of God's light in the *habāʾ*, which
"the people of thought call the universal hyle."

- List, strand and role per work: `catalogs/nur_canon.tsv` (chosen by Claude; scholar review pending)
- Exact versions: `catalogs/nur_canon_pins.json` (repo, commit, path, sha256; the build refuses mismatches)
- Corpus: `corpus/nur/<book>.jsonl.gz`; raw files: `sources/openiti/nur/`; search with `--author nur`
- Rebuild: `python3 pipeline/works/ingest_nur_canon.py --repo . --build`

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
- Not in OpenITI, still missing: al-Jīlī's *al-Insān al-kāmil*, al-Qayṣarī's and al-Qāshānī's commentaries
  on the Fuṣūṣ, al-Farghānī's *Muntahā al-madārik*, Suhrawardī's *Ḥikmat al-ishrāq*, Mullā Ṣadrā's *Asfār*,
  and the ḥadīth critics' treatments of the Jābir report.
