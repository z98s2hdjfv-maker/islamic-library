# Dossier: sainthood and the hidden hierarchy (wilāya; quṭb, awtād, abdāl, afrād)

> **A map, not an answer.** This dossier says where the library's evidence is. Before answering a study question, query the repo itself (see `START_HERE.md`): run the verse or concept lookup, open the cited records, and search the hadith layer and the grading works. Cite from the files, not from this page.

*Who keeps "the tent upright": the Friends of God, the ranks the Sufis describe, the reports behind them and the
critics.* Repo state: v42 (pages corrected). Load into the Claude Project. Record ids are the last part of each corpus `id`.

## 1. Start here
```
python3 pipeline/index/lookup.py --repo . --verse 10:62      # "the Friends of God: no fear on them": 210 passages, 40 works
python3 pipeline/index/lookup.py --repo . --verse 13:7       # "for every people a guide": 110 / 15
python3 pipeline/index/lookup.py --repo . --verse 18:65      # Khiḍr, "knowledge from Our presence": 130 / 30
python3 pipeline/index/lookup.py --repo . --concept abdal --work wilaya,ibnarabi,critics
python3 pipeline/index/lookup.py --repo . --concept qutb --work wilaya,ibnarabi,nur
```
Concepts (v38, sense-filtered; current counts in `reports/index/concept_summary.tsv`): `qutb` 505 passages / 72 works, `abdal` 1,233 / 146, `afrad` 121, `khatm_awliya` 351, `ghawth` 152, `nuqaba` 67, `nujaba` 79, `rijal_ghayb` 61, `awtad` 200. The filter drops the ordinary senses (the celestial
pole, the Qur'an's "mountains as pegs", al-Daraqutni's *Afrad*); `--audit <concept> --raw` shows the unfiltered hits.

## 2. Ibn ʿArabī's map (Futūḥāt ch. 73, II:5–7; `ibnarabi/futuhat.arabiyya` r00768–r00770; typed)
- Four prophets remain bodily alive: Idrīs, Ilyās, ʿĪsā, al-Khiḍr. "All of them are the *awtād*; two of them are the
  two *imāms*; one of them is the *quṭb*" (the Black Stone corner). Nested, not stacked.
- The saints who hold these offices are their deputies (*nuwwāb*) and know it once they attain the office.
- *Abdāl* (technical sense): 7, one per clime, each able to leave a spiritual double; "the forty" are another group.
- Qualification: hunger, vigil, silence, seclusion, after Abū Ṭālib al-Makkī, who has them from Sahl al-Tustarī
  (`sufi_manuals/0386…QutQulub` p00114).
- He met a *watad* in Fez, a man who sifted henna for wages; women can hold every rank.
- Futūḥāt I:185: the Seal of general sainthood is ʿĪsā, as al-Tirmidhī's *Khatm al-awliyāʾ* pointed to
  (`wilaya/0320HakimTirmidhi.KhatmAwliya`); Abū Madyan was one of the two imāms.

## 3. Three meanings of *abdāl*
| Meaning | Source |
|---|---|
| When one dies, God puts another in his place | the ḥadīth (Musnad Aḥmad 896) |
| One who can leave a spiritual double | Ibn ʿArabī, ch. 73 |
| One whose will has been exchanged for God's | al-Jīlānī, *Futūḥ al-ghayb*, discourse 6 (`jilani/futuhghayb.darwish` r00079) |

## 4. The reports and their critics
- **Musnad 896** (forty in Shām, via Shurayḥ b. ʿUbayd from ʿAlī): Shurayḥ is *thiqa* but sends much (*irsāl*;
  Taqrīb 2775); Muḥammad b. ʿAwf of Ḥimṣ doubted he heard from any Companion (Tahdhīb al-kamāl XII:445†). Broken chain.
- **Not in al-Bukhārī or Muslim** at all.
- **Abū Bakr al-Kattānī's ranks**: 300 nuqabāʾ (Maghrib), 70 nujabāʾ (Egypt), 40 budalāʾ (Shām), 7 akhyār,
  4 ʿumud, 1 ghawth (Mecca): `wilaya/0463…TarikhBaghdad` p10763. The rank names vary between sources.
- **Ibn ʿAsākir** gathers the Shām reports with parallel chains (`wilaya/0571…TarikhDimashq` p01172).
- **Against:** Ibn al-Jawzī (*Mawḍūʿāt*: fabricated); Ibn al-Qayyim (`…ManarMunif` p00499: all such reports false);
  Ibn Taymiyya: a Shāmī report with a broken chain; early Mecca had fewer than seven believers, so fixed numbers
  cannot hold in every age (Majmūʿ XI:432†); the "cascade" of help to a Ghawth competes with tawḥīd (XXVII:96†);
  no numbered report is sound (`…FurqanBaynaAwliya` p00081). Ibn Khaldūn: modelled on the Shīʿī imām (`…Tarikh` p00987).
- **For:** al-Suyūṭī, *al-Khabar al-dāll* (`…HawiLiFatawi` p00620); via al-Kattānī: sound, even *mutawātir* in meaning
  (`…NazmMutanathir` p00925). Aḥmad b. Ḥanbal: "if the people of ḥadīth are not the abdāl, I know of no abdāl" (p00018).
- **Graders:** al-Sakhāwī (`…MaqasidHasana` p00035), al-Qārī (`…AsrarMarfuca` p00268: the Anas routes are weak).

## 5. What the sound Sunnah does say
- "A group of my community will not cease upon the truth, *manifest*, until the Resurrection" (Muslim 156).
- "Are you helped and given provision except through your weak ones?" (al-Bukhārī, Jihād): the role the abdāl report
  gives to forty hidden men, the sound ḥadīth gives to the weak.
- Uways, unknown, from Yemen, "the best of the Followers"; ʿUmar told to seek his prayer (Muslim 2542).
- "Many a dishevelled one, turned away at doors, if he swore by God, God would fulfil it" (Muslim 2622).
- The Qur'an: the Friends are "those who believed and were mindful" (10:62–63): open to every believer.

## 6. Rumi and his circle
- Mathnawī 2:815–20: "in every age a saint arises… the lesser saint is his lamp… the Light has ranks."
- 2:1933–35: "lion-men… pillars for the world's breaches, physicians of hidden illnesses."
- 2:2144: visit the sick, he "may be a Pole." 1:678–81: ten lamps, one light, "no numbers in meanings."
- Aflākī: Rumi declined to lead prayer: "we are *abdāl* folk" (OCR). Shams on Ibn ʿArabī: "a mountain," yet "he lacked
  following" (Maqālāt, OCR, no witness; locate via `reports/concordance/chittick_movahhed.tsv`).

## 7. Confidence and gaps
- Typed: the Futūḥāt, the ḥadīth collections, rijāl, Ibn Taymiyya, al-Suyūṭī, the wilāya canon's OpenITI texts.
- OCR: al-Munāwī's *Kawākib* (7,448 of 12,046 pages corroborated), Aflākī, Shams (no witness), al-Tirmidhī's
  *Masʾala fī waṣf al-mufarradīn* (no witness).
- Manuscripts: `catalogs/manuscripts.tsv` (Shams in Sulṭān Walad's hand; Konya Mevlana Museum 2154).
- Missing: Hujwīrī's *Kashf al-maḥjūb*, Ibn ʿArabī's *Ḥilyat al-abdāl*, al-Sakhāwī's treatise on the abdāl.

## 8. Open questions
1. The 313 of the Mahdī (Ibn Abī Shayba 37223, "as the number of Badr") against the abdāl reports.
2. al-Qayṣarī ch. 9 (nūr dossier) as the bridge from the Muhammadan Reality to the Poles.
3. Ibn Taymiyya's positive reading of *wilāya* (al-Furqān) as a whole, not only his critique.

† Page read before v42 and not yet re-checked (no record id here): OpenITI page markers end a page, so it may be one page early. Confirm with `python3 pipeline/search/cite.py <record_id> "<phrase>"`.
