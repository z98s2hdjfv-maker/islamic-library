# Jalasa stress test: scorecard

Run 2026-10-03 on `a9bb540 Apply library-update-v51.zip` in 177 seconds. Cases come from `docs/jalasa/STRESS_TEST.md`; edit that document to change them.

**Must: 57 of 57 pass.** These are things the repo already does; a failure is a regression.
**Goal: 0 of 19 met.** These are things the Jalasa needs that the repo does not do yet.

| Capability | Must | Goal met |
|---|---|---|
| A. The Qur'an and its commentators | 6 of 6 | 0 of 2 |
| B. The Sunna: testing a saying | 10 of 10 | 0 of 7 |
| C. The masters of the council | 10 of 10 | 0 of 1 |
| D. The caliphs and the Companions | 7 of 7 | 0 of 1 |
| E. The schools of law: showing a disagreement | 2 of 2 | 0 of 2 |
| F. Citing: every claim traceable | 2 of 2 | 0 of 1 |
| G. Classical and modern kept apart | 2 of 2 | 0 of 0 |
| H. The sijill: recording what the council found | 5 of 5 | 0 of 1 |
| I. Odd input | 5 of 5 | 0 of 0 |
| J. Speed | 2 of 2 | 0 of 1 |
| K. Size and coverage | 6 of 6 | 0 of 3 |

## Goals not yet met: the roadmap

Each is a gap between the repo and what a Jalasa needs.

| Case | What it tests | Expected | Found |
|---|---|---|---|
| A7 | The heart as a concept: not in the concept index yet | `passages>=500, works>=50` | 0 passages in 0 works; FAILED: passages>=500 (found 0); works>=50 (found 0) |
| A8 | The Miʿraj, the Sidra, the Kursi and the Throne are not in the concept index (seven heavens case) | `passages>=100, works>=20` | 0 passages in 0 works; FAILED: passages>=100 (found 0); works>=20 (found 0) |
| B9 | The same hadith in its popular wording should lead to Muslim's version | `in:Muslim` | 3 hadith (Ahmad), 14 critic passages; FAILED: in:Muslim |
| B10 | Al-Tirmidhi's own hadith is in the corpus but missing from his hadith layer | `in:Tirmidhi` | 3 hadith (Ibn Hibban, al-Nasaʾi), 5 critic passages; FAILED: in:Tirmidhi |
| B12 | Muslim words it "بالنية ... لامرئ": the popular wording should still lead to his version | `in:Muslim` | 11 hadith (Abu Dawud, Ahmad, Ibn Hibban, Ibn Khuzayma, Ibn Maja, al-Bazzar), 15 critic passages; FAILED: in:Muslim |
| B11 | A master's saying (al-Shadhili) should be traced to who said it, not only reported as absent | `critics>=1` | 0 hadith, 0 critic passages; FAILED: critics>=1 (found 0) |
| B15 | Al-Tirmidhi's own hadith, missing from his layer like B10 | `in:Tirmidhi` | 1 hadith (Ahmad), 7 critic passages; FAILED: in:Tirmidhi |
| B16 | The same fault: found in five other collections, not in al-Tirmidhi's | `in:Tirmidhi` | 6 hadith (Ahmad, Ibn Hibban, Ibn Maja, al-Tabarani, al-Tayalisi), 1 critic passages; FAILED: in:Tirmidhi |
| B17 | A short part of a long hadith should still find it in the layer | `in:Ibn Hibban` | 0 hadith, 1 critic passages; FAILED: in:Ibn Hibban |
| C7 | An Arabic phrase should reach Rumi's Persian (آینه دل): needs a link between Arabic and Persian terms | `each_folder` | 0 records in 0 works; FAILED: folders_with_hits>=2 (found 0) |
| D8 | The works on judging should carry the caliphs' judgments under a wording the council can find | `records>=1` | 0 records in 0 works; FAILED: records>=1 (found 0) |
| E3 | A real disagreement: one phrase misses the school that words it differently. Needs an index of legal questions | `each_folder` | 12 records in 10 works (hanbali 2, maliki 4, shafii 6); FAILED: folders_with_hits>=4 (found 3) |
| E4 | The same, for the qunut at dawn | `each_folder` | 32 records in 16 works (hanbali 1, maliki 11, shafii 20); FAILED: folders_with_hits>=4 (found 3) |
| F3 | A hadith-layer id should resolve to its source page too | `` | the record did not resolve: record not found |
| H6 | A juristic type exists and is used | `entries>=1` | 0 entries of type ruling; FAILED: entries>=1 (found 0) |
| J3 | Fast enough to test every saying in a long lecture at once | `seconds<=1` | 2 seconds; FAILED: seconds<=1 (found 1.52) |
| K7 | Target: four in ten hadith with a classical grade | `value<=0.60` | 70.0%; FAILED: value<=0.60 (found 0.7) |
| K8 | Target: most narrator names linked | `value>=0.60` | 44.9%; FAILED: value>=0.60 (found 0.45) |
| K9 | A dossier for the heart and one for each master | `value>=6` | 4; FAILED: value>=6 (found 4) |

## Passing



| Case | What it tests | Expected | Found |
|---|---|---|---|
| A1 | The covenant verse: many commentaries, oldest first | `passages>=100, works>=20, oldest_first==1` | 605 passages in 69 works |
| A2 | "Was he who was dead and We gave him life" (used in the heart lecture) | `passages>=100, works>=20` | 194 passages in 40 works |
| A3 | The fitra verse | `passages>=200, works>=30` | 457 passages in 40 works |
| A4 | "Rather, what they earned has rusted upon their hearts": the Qur'anic basis for the stain on the heart | `passages>=20, works>=8` | 154 passages in 35 works |
| A5 | A key term across the works | `passages>=1000, works>=100` | 2514 passages in 168 works |
| A6 | The hidden hierarchy | `passages>=300, works>=50` | 506 passages in 73 works |
| B1 | A sound hadith is found in al-Bukhari with its parallels | `in:Bukhari, collections>=5, cites` | 11 hadith (Abu Dawud, Ahmad, Ibn Hibban, Ibn Khuzayma, Ibn Maja, al-Bazzar), 15 critic passages |
| B2 | A fabricated saying reaches the fabrication works | `critic:Jawzi, critics>=12, modern_apart` | 2 hadith (al-Bayhaqi, al-Bazzar), 24 critic passages |
| B3 | A saying with no source: al-ʿIraqi's verdict on al-Ghazali's hadith | `not_in_layer, says:Iraqi:لم أر له أصلا, critic:Fattani` | 0 hadith, 4 critic passages |
| B4 | A weak hadith: the critic's words on the chain | `in:Bayhaqi, says:Iraqi:بسند ضعيف, critic:Jawzi` | 1 hadith (al-Bayhaqi), 6 critic passages |
| B5 | The compiler's own grade is shown | `in:Tirmidhi, grade:Tirmidhi:حسن صحيح, collections>=5` | 17 hadith (Ahmad, al-Bayhaqi, al-Bazzar, al-Darimi, al-Hakim, al-Tabarani), 17 critic passages |
| B6 | A later critic's verdict joined as data | `in:Abu Dawud, grade:Dhahabi:شرط, modern_apart` | 11 hadith (Abu Dawud, Abu Yaʿla, Ahmad, Ibn Hibban, Ibn Khuzayma, al-Bayhaqi), 11 critic passages |
| B7 | Loose wording finds the critics who quote it differently | `not_in_layer, critic:Sakhawi, entries>=2` | 0 hadith, 6 critic passages |
| B8 | Found when given in Muslim's own wording | `in:Muslim` | 2 hadith (Ibn Khuzayma, Muslim), 3 critic passages |
| B13 | Al-Hakim's "sound" and al-Dhahabi's "fabricated" on the same report, side by side (seven heavens case) | `in:Hakim, grade:Dhahabi:موضوع, modern_apart` | 1 hadith (al-Hakim), 0 critic passages |
| B14 | A weak report with the reading its transmitters gave it | `in:Ahmad, critic:Sakhawi` | 1 hadith (Ahmad), 7 critic passages |
| C1 | Al-Ghazali on the mirror of the heart | `records>=3` | 6 records in 1 works (ghazali 6) |
| C2 | Ibn ʿArabi on the same image | `records>=3, works>=3` | 9 records in 6 works (ibnarabi 9) |
| C3 | Al-Jilani on the same image | `records>=3` | 6 records in 2 works (jilani 6) |
| C4 | Rumi on the mirror of the heart, in Persian, in the Mathnawi and the Divan | `records>=5, each_folder` | 9 records in 3 works (mathnawi 5, rumi 4) |
| C5 | The Ihya passage on the five causes is reachable by its own words | `records>=1` | 6 records in 1 works (ghazali 6) |
| C6 | The plain word "heart" reaches all four masters (Rumi where he writes in Arabic) | `each_folder` | 3246 records in 39 works (ghazali 828, ibnarabi 2019, jilani 379, rumi 20) |
| C8 | Rumi on Jibril's halt at the Sidra (seven heavens case) | `records>=1` | 1 records in 1 works (mathnawi 1) |
| C9 | Ibn ʿArabi's cosmology: the starless sphere | `records>=20` | 56 records in 7 works (ibnarabi 56) |
| C10 | A master's saying traced to who said it: al-Shadhili, in Ibn ʿAtaʾ Allah and al-Shaʿrani (heart case) | `records>=2` | 3 records in 3 works (wilaya 3) |
| C11 | Al-Jilani's sermon on polishing the rust of hearts | `records>=1` | 2 records in 1 works (jilani 2) |
| D1 | Hadith that reach Abu Bakr in the layer | `hadith>=100` | 222 hadith reach Abu Bakr in the layer |
| D2 | Hadith that reach ʿUmar | `hadith>=500` | 1024 hadith reach Umar in the layer |
| D3 | Hadith that reach ʿUthman | `hadith>=150` | 263 hadith reach Uthman in the layer |
| D4 | Hadith that reach ʿAli | `hadith>=1000` | 2372 hadith reach Ali in the layer |
| D5 | The report of ʿUmar's conversion in Ibn Saʿd and al-Baladhuri | `records>=2` | 3 records in 3 works (history 1, sahaba 2) |
| D6 | ʿUmar's judgments in the Companion reports | `records>=20` | 100 records in 5 works (athar 100) |
| D7 | Abu Bakr's own sayings across the Companion folders | `each_folder` | 34 records in 12 works (athar 12, consensus 7, judging 1, sahaba 14) |
| E1 | A common legal phrase reaches all four schools | `each_folder, works>=20` | 206 records in 35 works (hanafi 40, hanbali 55, maliki 28, shafii 83) |
| E2 | A legal maxim is found in the maxims literature | `each_folder` | 16 records in 8 works (hanafi 14, hanbali 2) |
| F1 | A critic's record resolves to its page | `` | urn:openiti:0902Sakhawi.MaqasidHasana.JK001160-ara1:p03238 |
| F2 | The Ihya passage on the five causes resolves | `` | urn:shamela:ghazali.ihya_with_iraqi:r01491 |
| G1 | Modern verdicts never appear among the classical ones | `modern_apart, says:Busiri:حفص, hadith>=10` | 24 hadith (Abu Yaʿla, Ibn Maja, al-Bayhaqi, al-Bazzar, al-Tabarani), 102 critic passages |
| G2 | A classical critic and a modern one on the same hadith, in separate columns | `in:Abu Dawud, grade:Nawawi:حسن, modern_apart` | 3 hadith (Abu Dawud, al-Bazzar, al-Hakim), 7 critic passages |
| H1 | Every cited record resolves | `` | 273 entries, 103 cited records (103 resolved); 0 problems |
| H2 | Voices' positions are recorded | `entries>=78` | 78 entries of type position |
| H3 | Verdicts on inferences are recorded | `entries>=38` | 38 entries of type verdict |
| H4 | Sayings examined by a study are recorded (22 from the seven heavens case, 7 from the heart lecture) | `entries>=29` | 29 entries of type saying |
| H5 | What was found on each saying is recorded | `entries>=29` | 29 entries of type authentication |
| I1 | With and without vowel marks | `` | first: 11 hadith, 15 passages; second: 11 hadith, 15 passages |
| I2 | With and without hamza and ta marbuta | `` | first: 17 hadith, 17 passages; second: 17 hadith, 17 passages |
| I3 | Latin text does not break the command | `` | ran without error |
| I4 | A one-word saying does not break the command | `` | ran without error |
| I5 | Persian letters and digits do not break the search | `` | ran without error |
| J1 | Testing a batch of sayings stays cheap per saying (about 2 seconds on two processors) | `seconds<=8` | 2 seconds |
| J2 | The whole batch of this document's sayings | `seconds<=180` | 32 seconds |
| K1 | The hadith layer has not shrunk | `value>=164000` | 164521 |
| K2 | All collections are in the layer | `value>=21` | 21 |
| K3 | The works index has not shrunk | `value>=390` | 396 |
| K4 | Classical grade coverage has not fallen back | `value<=0.705` | 70.0% |
| K5 | Narrator links have not fallen back | `value>=0.44` | 44.9% |
| K6 | With the modern column, under half the hadith have no grade at all | `value<=0.46` | 45.7% |

## Timings

- authenticate_all: 32 seconds
- authenticate_per_saying: 2 seconds
