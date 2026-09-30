# Dossier: the Muhammadan Light and Reality (al-nūr al-muḥammadī, al-ḥaqīqa al-muḥammadiyya)
*How the tradition describes the Prophet's ﷺ light as the first receiver of God's light, carried through Adam and the
prophets, and continuing after him in the saints.* Repo state: v31. Load into the Claude Project. Record ids are the
last part of each corpus `id`; reproduce any line with `pipeline/index/lookup.py`.

## 1. Start here
```
python3 pipeline/index/lookup.py --repo . --verse 24:35      # the Light verse: 610 passages, 47 works
python3 pipeline/index/lookup.py --repo . --verse 7:172      # the covenant (Tustari's column of light): 485 / 46
python3 pipeline/index/lookup.py --repo . --verse 33:46      # "a light-giving lamp": 66 / 26
python3 pipeline/index/lookup.py --repo . --verse 3:81       # the prophets' covenant to support him: 285 / 27
python3 pipeline/index/lookup.py --repo . --concept haqiqa_muhammadiyya --work nur,ibnarabi   # 126 passages
python3 pipeline/index/lookup.py --repo . --concept nur_muhammadi                              # 75 passages
```
Related concepts: `insan_kamil` (894), `aql_awwal` (452), `haba` (310), `ruh_muhammadi` (35), `kawn_jami` (44).
Index limit: 26:219 ("your movement among those who prostrate") is too short (3 words) for the verse index; read
it in al-Qasṭallānī directly (below).

## 2. The stages, oldest witness first
| Stage | Text | Where | Status |
|---|---|---|---|
| Light from His light prostrates; a column of light "whose inside and outside is the very essence of Muhammad" stands a million years before creation | Sahl al-Tustarī (d. 283) on 7:172 | `tafsir_sufi/0283SahlTustari.Tafsir` p00715 | typed (compiled by his students) |
| Adam "created from light"; the Prophet's body from Adam's clay; seekers from Adam's light, the sought from Muhammad's | same | p00719–p00721 | typed |
| God discloses His light to the *habāʾ* (prime matter); each thing receives "as the corners of a house receive the lamp"; nearest is the Muhammadan reality, "called the Intellect" | Ibn ʿArabī, Futūḥāt ch. 6, I:118–19 | `ibnarabi/futuhat.arabiyya` r00119–r00120 | typed |
| "From prophet to prophet, until I brought you forth as a prophet" (Ibn ʿAbbās on 26:219, via al-Bazzār) | al-Qasṭallānī, Mawāhib I:56 | `nur/0923…MawahibLaduniyya` p00208 | typed; chain not yet graded |
| The Poles of every nation, Adam to Muhammad, named in Cordoba; "the single Pole is the spirit of Muhammad," supplying all prophets and Poles to the Resurrection | Futūḥāt ch. 14, I:150–52 | r00151–r00153 | typed |
| The Muhammadan reality is "the form of the all-comprehensive name"; after prophecy is sealed, polehood passes to the saints, one always in the station, until the Seal; then the Hour | al-Qayṣarī, Muqaddima ch. 9 | `nur/0751…Qaysari.SharhFusus` leaves 145, 149 | OCR, no witness; check Ali 2020 |
| "One from when existence began to eternity, varying in garments"; appears in each age in its most perfect; "not transmigration, God forbid" | al-Jīlī, al-Insān al-kāmil | `nur/0805…InsanKamil` leaves 215–216 | OCR, corroborated (0.89–0.93) |

## 3. The Light verse (24:35): three early readings of "His light"
- **The believer:** Ubayy b. Kaʿb, Saʿīd b. Jubayr, al-Ḍaḥḥāk (al-Ṭabarī XVII:296–98).
- **Muhammad ﷺ:** Kaʿb al-Aḥbār to Ibn ʿAbbās (his own view, not a ḥadīth); al-Tustarī likewise.
- **Sufi unfolding** (al-Sulamī, Ḥaqāʾiq): al-Kharrāz: niche = the Prophet's inner being, glass = his heart, lamp = the
  light placed in him, blessed tree = Ibrāhīm (the line of prophets). Al-Ghazālī, *Mishkāt*: "all the prophets are
  lamps, and so are the scholars, but the difference between them cannot be counted" (`nur/0505…MishkatAnwar`).
- **24:36–37** names who carries the light: "men whom neither trade nor selling distracts from the remembrance of God."

## 4. The proof-texts and their status
| Report | Status in the repo |
|---|---|
| "I was a prophet while Adam was between spirit and body" | sound: al-Tirmidhī 3609 (*ḥasan ṣaḥīḥ gharīb*); al-Suyūṭī, *Khaṣāʾiṣ* gives its routes |
| "…between water and clay" (Futūḥāt ch. 14's wording) | al-Sakhāwī, *Maqāṣid* 842: not found in that wording |
| "The first thing God created was the light of your Prophet, O Jābir" | in no ḥadīth collection in the repo; al-Qasṭallānī (p00138, I:47) attributes it to ʿAbd al-Razzāq "with his chain" but gives none; al-Zurqānī (p00282–289) notes the dispute whether the Pen came first |
| "The first thing God created was the Pen" | sound per al-Suyūṭī, *al-Ḥāwī* I:343 |
| "The scholars of my community are like the prophets of Israel" (cited before Futūḥāt ch. 14) | al-Sakhāwī, *Maqāṣid* 702: no basis (Ibn Ḥajar, al-Damīrī, al-Zarkashī) |

## 5. The other voices
- The Prophet's precedence ("between spirit and body") is sound and widely held. The light as a created substance,
  the million years and the appearances in "garments" rest on unveiling (*kashf*) and weak or unsourced reports.
- Ibn Taymiyya and the ḥadīth critics (see the wilāya dossier) reject those parts while affirming the Prophet's rank.
- Philosophy behind the vocabulary: Ibn Sīnā's First Intellect (`nur/0428IbnSina.ShifaIlahiyyat`), the Ikhwān's
  prime matter (`nur/0375IkhwanSafa.Rasail`), al-Ghazālī's *Tahāfut*; Ibn ʿArabī names the *habāʾ* as their hyle.
- Science (from our discussion, not the repo): no test of a pre-cosmic light is possible; the parallels (one source
  received by capacity, stars seeding stars) are analogies, not proofs.

## 6. Confidence and gaps
- Typed: al-Tustarī, al-Ṭabarī, the Futūḥāt (Shamela), al-Qasṭallānī, al-Sulamī, al-Ghazālī.
- OCR: al-Qayṣarī (no witness), al-Jīlī (corroborated), al-Farghānī, the Tāʾiyya commentaries.
- Zurqānī's OpenITI text seems to carry mainly the Mawāhib; his own verdicts may be missing.
- Missing: al-Jandī's Fuṣūṣ commentary (free scan without text: needs OCR), al-Qūnawī's *al-Fukūk*.

## 7. Open questions
1. Grade the al-Bazzār chain for 26:219 in the ḥadīth layer.
2. Tustarī's triad (Muhammad, Adam, progeny) against Ibn ʿArabī's *habāʾ*: same structure, different language?
3. al-Qayṣarī ch. 9 against Mukhtar Ali's edition (the first human check to log in `verification_log.tsv`).
