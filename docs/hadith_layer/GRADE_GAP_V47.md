# v47: five steps on the grade gap

After v46, 118,613 of the layer's 164,521 hadith (72.1%) had no classical grade. v47 takes the five steps that the
library's own holdings allow. Everything is tables: nothing in the corpus or in `apparatus/hadith` is edited, every
row is the critic's own words with the record to cite, and modern verdicts stay in their own folder.
Built by `pipeline/hadith/build_grades_v47.py` (steps 1, 2, 3, 5) and `pipeline/hadith/build_hadith_links.py` (step 4).

## 1. More classical critics joined (`apparatus/hadith_grades/`)
| Table | Critic | Verdicts found | Hadith that received one |
|---|---|---|---|
| `mundhiri_mukhtasar_abidawud.tsv` | al-Mundhiri (d. 656), his note after each hadith of Abu Dawud | 2,491 | 2,430 of Abu Dawud: 690 with a verdict, 1,757 where he says al-Bukhari or Muslim reported it |
| `nawawi_khulasa.tsv` | al-Nawawi (d. 676), Khulasat al-ahkam | 501 | 316 |
| `mundhiri_targhib.tsv` | al-Mundhiri, al-Targhib wa-l-tarhib | 2,540 | 1,889 |
| `ibnhajar_bulugh.tsv` | Ibn Hajar (d. 852), Bulugh al-maram | 440 | 391 |
| `busiri_ithaf.tsv` | al-Busiri (d. 840), Ithaf al-khayra | 2,818 | 657 (al-Tayalisi, al-Humaydi, Abu Ya'la, Ahmad) |

- **A verdict that names several collections** ("رواه أبو داود والنسائي بإسناد صحيح") is joined to each one the
  library holds. The chain he means may be one of them: `candidates` counts the hadith that received the row.
- **Reported verdicts.** Ibn Hajar and al-Mundhiri often report another critic ("وصححه ابن خزيمة"). The row is filed
  under the author of the book; read `verdict` to see whose judgment it is.
- **Two conventions, labelled as such.** al-Nawawi files weak hadith under "فصل في ضعيفه": such a row has class
  `weak_by_section` and the verdict begins `[فصل في ضعيفه]`. al-Mundhiri opens a hadith with "روي" when he holds it
  weak (his preface): class `weak_by_convention`. Neither is a statement in so many words.
- **Most of the Ithaf stays unjoined** (2,162 verdicts): they are on the musnads of Musaddad, Ibn Abi Shayba,
  Ibn Mani', al-Harith, Ishaq, 'Abd b. Humayd and Ibn Abi 'Umar, which the library does not hold as collections.
- **Not used:** Ibn Hajar's Mukhtasar zawa'id al-Bazzar. The only free text is badly damaged (letters dropped
  throughout), so a join by wording would be unreliable.

## 2. The compilers' own remarks (`apparatus/hadith_grades/compilers_remarks.tsv`)
14,915 remarks on 14,885 hadith, in the compiler's words: "قال أبو داود ...", "قال أبو عبد الرحمن هذا خطأ",
al-Daraqutni's "رشدين ضعيف" and "إسناد صحيح", al-Bayhaqi's "هذا مرسل", Ibn Khuzayma's "إن صح الخبر", al-Bazzar's and
al-Tabarani's notes on who alone narrates it.
- 2,001 hadith carry a remark that is a judgment (weak 842, sound 538, fair 251, very weak 127 ...). Among them are
  about 540 hadith of al-Tirmidhi whose grade the layer had missed because he words it "حديث فلان حديث حسن صحيح".
- 11,644 are notes of **uniqueness** ("لم يروه عن فلان إلا فلان") and 1,262 are **defect notes** ("خالفه فلان",
  "والصواب موقوف"). These are evidence for a critic, not grades, and are **not counted as grades**.
- The remarks of al-Daraqutni, al-Bayhaqi and al-Nasa'i that stand unmarked at the end of a text are found by the
  critics' vocabulary. Some are missed, and a few rows may be the tail of a report: read the hadith record.

## 3. The Sahih wording note, wider (`apparatus/hadith_links/in_sahih.tsv.gz`)
Before, a hadith got the note only inside its parallel group. Now every hadith is compared directly with al-Bukhari
and Muslim, and three columns are added:
- `companion`: **same** (the hadith's Companion is in the Sahih hadith's chain: 14,595), **unknown** (1,726),
  **other** (500: the wording is in the Sahih from another Companion; kept only when at least 80% is shared).
- `basis`: parallel_group, wording, critic_takhrij.
- `critic_record`: where a classical critic says al-Bukhari or Muslim reported it (1,758 hadith, nearly all
  al-Mundhiri on Abu Dawud). That is a scholar's statement, stronger than a match of wording.
17,994 hadith carry the note (15,710 before). It is still a note on the wording, never a grade of the chain.

## 4. Narrator links (`apparatus/hadith_links/chains.jsonl.gz`, `weak_links.tsv.gz`)
- A name that fits several Taqrib entries is now settled by its neighbours in the chain: the one candidate already
  attested as the student of the next narrator or the teacher of the previous one (`match` = neighbour).
  20,163 more names linked; 44.9% of all names (42.7% before).
- **Only names with a father's name** ("محمد بن جعفر" from Shu'ba = Ghundar). One-word names and bare kunyas are left
  unlinked on purpose: a trial showed the method fails there, because the best-known bearer of a short name is
  never spelled out (a bare "عكرمة" from Ibn 'Abbas went to 'Ikrima b. Khalid). Names reviewed as ambiguous in
  `catalogs/narrator_aliases.tsv` stay unlinked too.
- `weak_links.tsv.gz`: for hadith with **no classical grade**, the narrators in the chain whom Ibn Hajar ranks
  da'if or below, with the Taqrib record to cite: 5,159 rows on 4,979 hadith. Evidence about one narrator, not a
  grade: the link is automatic, and corroboration and hidden defects are not weighed.

## 5. A modern column (`apparatus/hadith_grades_modern/`), kept apart
| Table | Critic | Hadith |
|---|---|---|
| `arnaut_ahmad.tsv` | Shu'ayb al-Arna'ut on Ahmad's Musnad | 25,897 |
| `husayn_asad_abuyacla.tsv` | Husayn Salim Asad on Abu Ya'la | 6,951 |
| `albani_abidawud.tsv` | al-Albani on Abu Dawud | 4,535 |
| `husayn_asad_darimi.tsv` | Husayn Salim Asad on al-Darimi | 3,392 |
| `albani_jami.tsv` | al-Albani on al-Suyuti's Jami' saghir, joined by wording to every collection but the two Sahihs | 9,077 |
| `albani_tirmidhi.tsv` (v44) | al-Albani on al-Tirmidhi | 3,651 |

- **Sources.** al-Arna'ut and Husayn Asad: three printings on OpenITI that carry the editor's verdict after each
  hadith, pinned in `catalogs/modern_editions_pins.json` and kept in `sources/openiti/modern_editions/`. They are not
  corpus works and are not searched; only the verdict lines are taken. `critic_record` is the edition and its
  hadith number (not a corpus record). al-Albani on Abu Dawud: the tags the modern editor printed in al-Mundhiri's
  Mukhtasar, which he states are al-Albani's.
- **Ahmad:** the printing's numbering differs from the layer's, so the join is by wording alone; 2,240 joined rows are
  on a wording that has several chains in the Musnad (`candidates` above 1).
- **al-Nasa'i and Ibn Maja have no modern column of their own.** al-Albani's Sahih wa-da'if of the two is not on
  OpenITI. They receive only what the Jami' saghir join gives (343, 489 and 689 hadith).
- New class `sound_by_support`: "صحيح لغيره", "صحيح وهذا إسناد ضعيف" (sound through other routes, this chain weak).

## Coverage (164,521 hadith)
| | v46 | v47 |
|---|---|---|
| No classical grade | 118,613 (72.1%) | 115,147 (70.0%) |
| Neither a classical grade nor the Sahih wording note | 104,928 (63.8%) | 100,212 (60.9%) |
| Neither a classical nor a modern grade | not measured | 75,190 (45.7%) |

Largest changes: Abu Dawud 5,275 -> 4,270 without a classical grade (and 4,665 -> 2,471 with nothing at all),
al-Tirmidhi 1,223 -> 527, al-Daraqutni 4,604 -> 4,210, al-Nasa'i's two books 17,470 -> 17,077.
Two counting rules changed and move a few numbers the other way: v47 counts a verdict as a grade only when its
words classify (an unclassified row of al-Haythami no longer counts: al-Tabarani's Kabir and Awsat lose 35), and
the Sahih note counts only when the Companion is not another.
The honest reading: the classical gap closed by two points. What remains (al-Nasa'i, Ahmad, al-Tabarani, al-Bazzar,
Shu'ab al-iman) has no classical work in the library that grades it hadith by hadith. The modern column is what
covers Ahmad, Abu Ya'la, al-Darimi and Abu Dawud, and it must be cited as modern.

## Checked by hand (2026-10-02, by Claude, not a scholar)
- The five classical tables: 45 random joins read (9 each). All the right hadith; one of al-Busiri's doubtful.
- The modern tables: 40 random joins read (8 each). All the right hadith.
- Neighbour links: 40 random links read, none visibly wrong; the 60 most frequent read after the rule was narrowed.
- The Sahih note by wording alone: 12 read. The Companion column was right in each; two "other" rows were a short
  Sahih wording inside a long report, which is why "other" now needs a wording of some length.
- `class` is made by rule from the critic's words and is wrong in places (a verdict that reports two critics, or
  that judges another route). **Always quote `verdict`.** Status: unverified until a scholar samples the tables.

## Next
- al-Albani's Sahih wa-da'if of al-Nasa'i and Ibn Maja, and a usable text of Ibn Hajar's zawa'id of al-Bazzar, if
  free witnesses turn up.
- The remaining musnads of the Ithaf (Musaddad, Ibn Abi Shayba ...) are quoted in full inside it: they could be
  lifted into the layer so that al-Busiri's other 2,160 verdicts have something to join.
- One-word narrator names: a reviewed alias list by teacher and student (e.g. 'Ikrima from Ibn 'Abbas).
