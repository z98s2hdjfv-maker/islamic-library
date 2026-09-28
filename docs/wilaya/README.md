# Wilaya canon — the hidden hierarchy of saints (v18)

26 works from OpenITI on *wilāya* and the hidden order (quṭb/ghawth, awtād/ʿumud, abdāl/budalāʾ,
nujabāʾ, nuqabāʾ, afrād). They were chosen so that **both sides of the debate** are in the library:
theorists, the transmitters who carry the reports with isnāds, the ḥadīth critics and those who
answered them, theological critics, creed on karāmāt, and hagiography.

- List, strand and role per work: `catalogs/wilaya_canon.tsv` (chosen by Claude; scholar review pending)
- Exact versions: `catalogs/wilaya_canon_pins.json` (repo, commit, path, sha256; the build refuses mismatches)
- Corpus: `corpus/wilaya/<book>.jsonl.gz` (same record format as the madhhab canon; read with `gzip.open(p,'rt')`)
- Raw files: `sources/openiti/wilaya/`; search with `--author wilaya`
- Rebuild: `python3 pipeline/works/ingest_wilaya_canon.py --repo . --build`

Already in the repo and central to this topic (not duplicated): Futūḥāt ch. 73 (`corpus/ibnarabi/futuhat.arabiyya.jsonl`
r00768–770), ʿAnqāʾ mughrib, Jīlānī's Futūḥ al-ghayb, Ibn Taymiyya's Majmūʿ al-fatāwā (XI:432 abdāl treatise; XXVII:96),
Ḥilyat al-awliyāʾ, Qūt al-qulūb, Musnad Aḥmad 896, Ibn Abī Shayba 37223, Tahdhīb al-kamāl / Taqrīb (Shurayḥ b. ʿUbayd).

## Verified starting points (checked at import, record ids are `urn:openiti:<version>:pNNNNN`)
| Where | What |
|---|---|
| TarikhBaghdad p10763 | Abū Bakr al-Kattānī: nuqabāʾ 300 (Maghrib), nujabāʾ 70 (Egypt), budalāʾ 40 (Shām), akhyār 7 (wanderers), ʿumud 4 (corners of the earth), ghawth 1 (Mecca) |
| TarikhDimashq p01172 | the Musnad 896 abdāl report (Shurayḥ b. ʿUbayd from ʿAlī) with Ibn ʿAsākir's parallel chains (99 units mention abdāl) |
| HawiLiFatawi p00620 | al-Suyūṭī, *al-Khabar al-dāll ʿalā wujūd al-quṭb wa-l-awtād wa-l-nujabāʾ wa-l-abdāl* |
| NazmMutanathir p00925 | al-Kattānī reports al-Suyūṭī's answer to Ibn al-Jawzī: the abdāl report is sound, even *mutawātir maʿnawī* |
| NazmMutanathir p00018 | Aḥmad b. Ḥanbal: "if the people of ḥadīth are not the abdāl, I know of no abdāl" |
| ManarMunif p00499 | Ibn al-Qayyim: all reports of abdāl, aqṭāb, aghwāth, nuqabāʾ, nujabāʾ, awtād are false |
| FurqanBaynaAwliya p00081 | Ibn Taymiyya: no numbered report (4, 7, 12, 40, 70, 300, 313, one quṭb) is sound |
| Tarikh (Ibn Khaldūn) p00987 | Muqaddima: the quṭb/abdāl doctrine "as if imitating" the Rāfiḍī doctrine of the imām |
| AsrarMarfuca p00268 | al-Qārī: the routes from Anas are all weak (after Ibn al-Daybaʿ) |
| MaqasidHasana p00035 | al-Sakhāwī, entry "ḥadīth al-abdāl" |
| KhatmAwliya | al-Ḥakīm al-Tirmidhī's Seal of the Saints (the text says *khātam al-awliyāʾ*) |

## Caveats
- Uncorrected OCR: Masʾala fī waṣf al-mufarradīn, Laṭāʾif al-minan, al-Kibrīt al-aḥmar, Shifāʾ al-sāʾil,
  Rawḍ al-rayāḥīn, al-Tashawwuf, al-Kawākib al-durriyya. Check the page before quoting.
- Ṭabaqāt al-Shaʿrānī uses the Shamela version: OpenITI's JK "pri" file has no paragraphing (7 units).
- Different subject, left out: Ibn ʿAsākir's and al-Dimyāṭī's *al-Arbaʿūn al-abdāl* use *abdāl* in the
  ḥadīth-technical sense (a substitute route in an isnād).
- Not in OpenITI, still missing: Hujwīrī's Kashf al-maḥjūb (Persian), Ibn ʿArabī's Ḥilyat al-abdāl and Rūḥ al-quds,
  al-Shaʿrānī's al-Yawāqīt wa-l-jawāhir, al-Sakhāwī's Naẓm al-laʾāl fī al-kalām ʿalā al-abdāl, Ibn ʿĀbidīn's Ijābat al-ghawth.
