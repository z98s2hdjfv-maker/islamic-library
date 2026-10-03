# Jalasa stress test: scorecard

Run 2026-10-03 on `67d1589 Add files via upload` in 187 seconds. Cases come from `docs/jalasa/STRESS_TEST.md`; edit that document to change them.

**Must: 74 of 74 pass.** These are things the repo already does; a failure is a regression.
**Goal: 0 of 12 met.** These are things the Jalasa needs that the repo does not do yet.

| Capability | Must | Goal met |
|---|---|---|
| A. The Qur'an and its commentators | 11 of 11 | 0 of 0 |
| B. The Sunna: testing a saying | 15 of 15 | 0 of 4 |
| C. The masters of the council | 13 of 13 | 0 of 0 |
| D. The caliphs and the Companions | 7 of 7 | 0 of 1 |
| E. The schools of law: showing a disagreement | 2 of 2 | 0 of 2 |
| F. Citing: every claim traceable | 5 of 5 | 0 of 0 |
| G. Classical and modern kept apart | 2 of 2 | 0 of 0 |
| H. The sijill: recording what the council found | 5 of 5 | 0 of 1 |
| I. Odd input | 5 of 5 | 0 of 0 |
| J. Speed | 2 of 2 | 0 of 1 |
| K. Size and coverage | 7 of 7 | 0 of 3 |

## Goals not yet met: the roadmap

Each is a gap between the repo and what a Jalasa needs.

| Case | What it tests | Expected | Found |
|---|---|---|---|
| B9 | The same hadith in its popular wording should lead to Muslim's version | `in:Muslim` | 3 hadith (Ahmad), 14 critic passages; FAILED: in:Muslim |
| B12 | Muslim words it "بالنية ... لامرئ": the popular wording should still lead to his version | `in:Muslim` | 11 hadith (Abu Dawud, Ahmad, Ibn Hibban, Ibn Khuzayma, Ibn Maja, al-Bazzar), 15 critic passages; FAILED: in:Muslim |
| B11 | A master's saying (al-Shadhili) should be traced to who said it, not only reported as absent | `critics>=1` | 0 hadith, 0 critic passages; FAILED: critics>=1 (found 0) |
| B17 | A short part of a long hadith should still find it in the layer | `in:Ibn Hibban` | 0 hadith, 1 critic passages; FAILED: in:Ibn Hibban |
| D8 | The works on judging should carry the caliphs' judgments under a wording the council can find | `records>=1` | 0 records in 0 works; FAILED: records>=1 (found 0) |
| E3 | A real disagreement: one phrase misses the school that words it differently. Needs an index of legal questions | `each_folder` | 12 records in 10 works (hanbali 2, maliki 4, shafii 6); FAILED: folders_with_hits>=4 (found 3) |
| E4 | The same, for the qunut at dawn | `each_folder` | 32 records in 16 works (hanbali 1, maliki 11, shafii 20); FAILED: folders_with_hits>=4 (found 3) |
| H6 | A juristic type exists and is used | `entries>=1` | 0 entries of type ruling; FAILED: entries>=1 (found 0) |
| J3 | Fast enough to test every saying in a long lecture at once | `seconds<=1` | 1 seconds; FAILED: seconds<=1 (found 1.46) |
| K7 | Target: four in ten hadith with a classical grade | `value<=0.60` | 70.0%; FAILED: value<=0.60 (found 0.7) |
| K8 | Target: most narrator names linked | `value>=0.60` | 44.9%; FAILED: value>=0.60 (found 0.45) |
| K10 | A dossier for each of the other masters (al-Ghazali, al-Jilani, Ibn ʿArabi) | `value>=10` | 7; FAILED: value>=10 (found 7) |

## Passing



| Case | What it tests | Expected | Found |
|---|---|---|---|
| A1 | The covenant verse: many commentaries, oldest first | `passages>=100, works>=20, oldest_first==1` | 605 passages in 69 works |
| A2 | "Was he who was dead and We gave him life" (used in the heart lecture) | `passages>=100, works>=20` | 194 passages in 40 works |
| A3 | The fitra verse | `passages>=200, works>=30` | 457 passages in 40 works |
| A4 | "Rather, what they earned has rusted upon their hearts": the Qur'anic basis for the stain on the heart | `passages>=20, works>=8` | 154 passages in 35 works |
| A5 | A key term across the works | `passages>=1000, works>=100` | 2697 passages in 194 works |
| A6 | The hidden hierarchy | `passages>=300, works>=50` | 544 passages in 83 works |
| A7 | The heart as a concept, by its phrases (added in v53) | `passages>=500, works>=50` | 3371 passages in 221 works |
| A8 | The Miʿraj as a concept (v53; with sidra, kursi, arsh, sab_samawat) | `passages>=100, works>=20` | 2564 passages in 187 works |
| A9 | The Malakut as a concept (ether case; v53) | `passages>=1000, works>=100` | 3805 passages in 212 works |
| A10 | 'The first created thing' as a concept (ether case; v53) | `passages>=200, works>=50` | 531 passages in 111 works |
| A11 | The Throne, sense-filtered (v53) | `passages>=1000, works>=100` | 3937 passages in 219 works |
| B1 | A sound hadith is found in al-Bukhari with its parallels | `in:Bukhari, collections>=5, cites` | 11 hadith (Abu Dawud, Ahmad, Ibn Hibban, Ibn Khuzayma, Ibn Maja, al-Bazzar), 15 critic passages |
| B2 | A fabricated saying reaches the fabrication works | `critic:Jawzi, critics>=12, modern_apart` | 2 hadith (al-Bayhaqi, al-Bazzar), 24 critic passages |
| B3 | A saying with no source: al-ʿIraqi's verdict on al-Ghazali's hadith | `not_in_layer, says:Iraqi:لم أر له أصلا, critic:Fattani` | 0 hadith, 4 critic passages |
| B4 | A weak hadith: the critic's words on the chain | `in:Bayhaqi, says:Iraqi:بسند ضعيف, critic:Jawzi` | 1 hadith (al-Bayhaqi), 6 critic passages |
| B5 | The compiler's own grade is shown | `in:Tirmidhi, grade:Tirmidhi:حسن صحيح, collections>=5` | 17 hadith (Ahmad, al-Bayhaqi, al-Bazzar, al-Darimi, al-Hakim, al-Tabarani), 17 critic passages |
| B6 | A later critic's verdict joined as data | `in:Abu Dawud, grade:Dhahabi:شرط, modern_apart` | 11 hadith (Abu Dawud, Abu Yaʿla, Ahmad, Ibn Hibban, Ibn Khuzayma, al-Bayhaqi), 11 critic passages |
| B7 | Loose wording finds the critics who quote it differently | `not_in_layer, critic:Sakhawi, entries>=2` | 0 hadith, 6 critic passages |
| B8 | Found when given in Muslim's own wording | `in:Muslim` | 2 hadith (Ibn Khuzayma, Muslim), 3 critic passages |
| B10 | Al-Tirmidhi's own hadith, in his layer since v53 with his grade | `in:Tirmidhi, grade:Tirmidhi:حسن صحيح` | 4 hadith (Ibn Hibban, al-Nasaʾi, al-Tirmidhi), 5 critic passages |
| B13 | Al-Hakim's "sound" and al-Dhahabi's "fabricated" on the same report, side by side (seven heavens case) | `in:Hakim, grade:Dhahabi:موضوع, modern_apart` | 1 hadith (al-Hakim), 0 critic passages |
| B14 | A weak report with the reading its transmitters gave it | `in:Ahmad, critic:Sakhawi` | 2 hadith (Ahmad, al-Tirmidhi), 7 critic passages |
| B15 | Al-Tirmidhi's own hadith, in his layer since v53 | `in:Tirmidhi` | 2 hadith (Ahmad, al-Tirmidhi), 7 critic passages |
| B16 | The same: in his layer since v53 | `in:Tirmidhi` | 7 hadith (Ahmad, Ibn Hibban, Ibn Maja, al-Tabarani, al-Tayalisi, al-Tirmidhi), 1 critic passages |
| B18 | The JK editions write 'يا بن آدم': ibn and bn are matched as one word since v53 (divine sayings case) | `in:Tirmidhi, collections>=4` | 8 hadith (Ahmad, al-Bayhaqi, al-Darimi, al-Tabarani, al-Tirmidhi), 7 critic passages |
| B19 | The Pen hadith with al-Tirmidhi's own grade (ether case; v53) | `in:Tirmidhi, in:Abu Dawud, grade:Tirmidhi:حسن غريب` | 10 hadith (Abu Dawud, Ahmad, al-Bazzar, al-Hakim, al-Tabarani, al-Tayalisi), 17 critic passages |
| C1 | Al-Ghazali on the mirror of the heart | `records>=3` | 8 records in 2 works (ghazali 8) |
| C2 | Ibn ʿArabi on the same image | `records>=3, works>=3` | 11 records in 7 works (ibnarabi 11) |
| C3 | Al-Jilani on the same image | `records>=3` | 10 records in 4 works (jilani 10) |
| C4 | Rumi on the mirror of the heart, in Persian, in the Mathnawi and the Divan | `records>=5, each_folder` | 9 records in 3 works (mathnawi 5, rumi 4) |
| C5 | The Ihya passage on the five causes is reachable by its own words | `records>=1` | 6 records in 1 works (ghazali 6) |
| C6 | The plain word "heart" reaches all four masters (Rumi where he writes in Arabic) | `each_folder` | 3246 records in 39 works (ghazali 828, ibnarabi 2019, jilani 379, rumi 20) |
| C7 | An Arabic phrase reaches Rumi's Persian (آینه دل) through the term bridge (v53) | `each_folder` | 19 records in 5 works (mathnawi 6, rumi 13) |
| C20 | The Malakut in Rumi's own words (عالم امر, Mathnawi 4:3692-3693): the passage missed in the ether case | `records>=2` | 2 records in 1 works (mathnawi 2) |
| C21 | Rumi's couplets are in the concept index (فنا، نیستی add over 300 passages; v53) | `passages>=400` | 452 passages in 45 works |
| C8 | Rumi on Jibril's halt at the Sidra (seven heavens case) | `records>=1` | 1 records in 1 works (mathnawi 1) |
| C9 | Ibn ʿArabi's cosmology: the starless sphere | `records>=20` | 56 records in 7 works (ibnarabi 56) |
| C10 | A master's saying traced to who said it: al-Shadhili, in Ibn ʿAtaʾ Allah and al-Shaʿrani (heart case) | `records>=2` | 3 records in 3 works (wilaya 3) |
| C11 | Al-Jilani's sermon on polishing the rust of hearts | `records>=1` | 6 records in 3 works (jilani 6) |
| D1 | Hadith that reach Abu Bakr in the layer | `hadith>=100` | 222 hadith reach Abu Bakr in the layer |
| D2 | Hadith that reach ʿUmar | `hadith>=500` | 1027 hadith reach Umar in the layer |
| D3 | Hadith that reach ʿUthman | `hadith>=150` | 263 hadith reach Uthman in the layer |
| D4 | Hadith that reach ʿAli | `hadith>=1000` | 2375 hadith reach Ali in the layer |
| D5 | The report of ʿUmar's conversion in Ibn Saʿd and al-Baladhuri | `records>=2` | 3 records in 3 works (history 1, sahaba 2) |
| D6 | ʿUmar's judgments in the Companion reports | `records>=20` | 100 records in 5 works (athar 100) |
| D7 | Abu Bakr's own sayings across the Companion folders | `each_folder` | 34 records in 12 works (athar 12, consensus 7, judging 1, sahaba 14) |
| E1 | A common legal phrase reaches all four schools | `each_folder, works>=20` | 206 records in 35 works (hanafi 40, hanbali 55, maliki 28, shafii 83) |
| E2 | A legal maxim is found in the maxims literature | `each_folder` | 16 records in 8 works (hanafi 14, hanbali 2) |
| F1 | A critic's record resolves to its page | `` | urn:openiti:0902Sakhawi.MaqasidHasana.JK001160-ara1:p03238 |
| F2 | The Ihya passage on the five causes resolves | `` | urn:shamela:ghazali.ihya_with_iraqi:r01491 |
| F3 | A hadith-layer id resolves to its source page (v53) | `` | urn:hadith:0261Muslim.Sahih:121.1 |
| F4 | A Mathnawi couplet resolves to its book and Nicholson number (v53) | `` | urn:sufi:rumi.mathnawi:4.b3692 |
| F5 | A hadith added to al-Tirmidhi's layer in v53 resolves with its printed number | `` | urn:hadith:0279Tirmidhi.Sunan:p08858 |
| G1 | Modern verdicts never appear among the classical ones | `modern_apart, says:Busiri:حفص, hadith>=10` | 24 hadith (Abu Yaʿla, Ibn Maja, al-Bayhaqi, al-Bazzar, al-Tabarani), 102 critic passages |
| G2 | A classical critic and a modern one on the same hadith, in separate columns | `in:Abu Dawud, grade:Nawawi:حسن, modern_apart` | 3 hadith (Abu Dawud, al-Bazzar, al-Hakim), 7 critic passages |
| H1 | Every cited record resolves | `` | 507 entries, 222 cited records (222 resolved); 0 problems |
| H2 | Voices' positions are recorded | `entries>=109` | 109 entries of type position |
| H3 | Verdicts on inferences are recorded | `entries>=70` | 70 entries of type verdict |
| H4 | Sayings examined by a study are recorded (22 seven heavens, 7 heart, 40 divine sayings, 12 ether) | `entries>=81` | 81 entries of type saying |
| H5 | What was found on each saying is recorded | `entries>=81` | 81 entries of type authentication |
| I1 | With and without vowel marks | `` | first: 11 hadith, 15 passages; second: 11 hadith, 15 passages |
| I2 | With and without hamza and ta marbuta | `` | first: 17 hadith, 17 passages; second: 17 hadith, 17 passages |
| I3 | Latin text does not break the command | `` | ran without error |
| I4 | A one-word saying does not break the command | `` | ran without error |
| I5 | Persian letters and digits do not break the search | `` | ran without error |
| J1 | Testing a batch of sayings stays cheap per saying (about 2 seconds on two processors) | `seconds<=8` | 1 seconds |
| J2 | The whole batch of this document's sayings | `seconds<=180` | 33 seconds |
| K1 | The hadith layer has not shrunk | `value>=164650` | 164652 |
| K2 | All collections are in the layer | `value>=21` | 21 |
| K3 | The works index has not shrunk | `value>=390` | 396 |
| K4 | Classical grade coverage has not fallen back | `value<=0.705` | 70.0% |
| K5 | Narrator links have not fallen back | `value>=0.44` | 44.9% |
| K6 | With the modern column, under half the hadith have no grade at all | `value<=0.46` | 45.7% |
| K9 | Dossiers: asma, fitra, nur, wilaya, and since v53 the heart, Rumi and the first created thing | `value>=7` | 7 |

## Timings

- authenticate_all: 33 seconds
- authenticate_per_saying: 1 seconds
