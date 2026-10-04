# The Jalasa stress test

This document is the test. Each table row whose first cell is a case id is one case that
`pipeline/jalasa/stress_test.py` runs against the repo. Edit a row, add a row or delete a row, then run:

    python3 pipeline/jalasa/stress_test.py            # everything, two to four minutes
    python3 pipeline/jalasa/stress_test.py --only B,C # only some sections

The scorecard is written to `reports/jalasa/STRESS_REPORT.md`, and one line per run is added to
`reports/jalasa/stress_history.tsv`, so progress shows over time.

## What is being tested

A digital Jalasa is a council (Rumi, Ibn ʿArabi, al-Jilani, al-Ghazali and the four caliphs) that hears a claim
and weighs it against the Qur'an, the Sunna, the Companions and the masters. For that the repo must be able to do
twelve things. Each section below tests one of them.

Every case has a **level**:

- `must`: the repo already does this. A failure is a regression, and the script exits with an error.
- `goal`: the Jalasa needs this and the repo does not do it yet. It is tracked and never fails the run. When a
  goal starts passing, the scorecard says so: change it to `must` here so it is protected from then on.

The goals are the roadmap. Add a goal whenever a study shows something the council could not do.

## How to write a case

    | id | level | check | input | where | expect | why |

- **id**: a letter for the section and a number, unique (B7). **why**: one line, shown in the scorecard.
- **expect**: conditions joined by commas; all must hold. Numbers use `>=`, `<=`, `==`.
- Do not use the `|` character inside a cell.

| check | input | where | expect may use |
|---|---|---|---|
| `authenticate` | a saying in Arabic | (empty) | `in:Muslim` found in that collection; `not_in_layer`; `critic:Iraqi` that critic quotes it; `says:Iraqi:لم أر له أصلا` his passage holds these words; `grade:Tirmidhi:حسن صحيح` a classical grade; `modern_apart`; `cites`; `hadith>=N`, `critics>=N`, `collections>=N`, `entries>=N` |
| `same` | two sayings joined by a double slash: `A // B` | (empty) | (nothing: both must give the same hadith and passages) |
| `search` | a phrase | folders, comma-separated, or `all` | `records>=N`, `works>=N`, `each_folder` (every folder listed has a hit) |
| `verse` | sura:aya | (empty) | `passages>=N`, `works>=N`, `oldest_first==1` |
| `concept` | a concept key from `catalogs/concepts.tsv` | (empty) | `passages>=N`, `works>=N` |
| `caliph` | Abu Bakr, Umar, Uthman or Ali | (empty) | `hadith>=N` |
| `cite` | a record id | optional phrase | (nothing: the record must resolve to a page) |
| `sijill` | `validator`, or `type:saying` | (empty) | `entries>=N` for a type |
| `story` | a Mathnawi couplet, `book:number` or its id | optional text the output must hold | `heading==1`, `story==1`, `passages>=N`, `readings>=N` |
| `metric` | a measure (see section K) | (empty) | `value>=N` or `value<=N`; shares as decimals (0.70) |
| `time` | `authenticate_per_saying`, `authenticate_all`, `search_whole_corpus` | (empty) | `seconds<=N` |
| `crash` | any text | `authenticate` or a folder | (nothing: the tool must not fail) |

## A. The Qur'an and its commentators

The council starts from the verse. The lookup must return the commentaries on it, oldest first.

| id | level | check | input | where | expect | why |
|---|---|---|---|---|---|---|
| A1 | must | verse | 7:172 | | passages>=100, works>=20, oldest_first==1 | The covenant verse: many commentaries, oldest first |
| A2 | must | verse | 6:122 | | passages>=100, works>=20 | "Was he who was dead and We gave him life" (used in the heart lecture) |
| A3 | must | verse | 30:30 | | passages>=200, works>=30 | The fitra verse |
| A4 | must | verse | 83:14 | | passages>=20, works>=8 | "Rather, what they earned has rusted upon their hearts": the Qur'anic basis for the stain on the heart |
| A5 | must | concept | fitra | | passages>=1000, works>=100 | A key term across the works |
| A6 | must | concept | qutb | | passages>=300, works>=50 | The hidden hierarchy |
| A7 | must | concept | qalb | | passages>=500, works>=50 | The heart as a concept, by its phrases (added in v53) |
| A8 | must | concept | miraj | | passages>=100, works>=20 | The Miʿraj as a concept (v53; with sidra, kursi, arsh, sab_samawat) |
| A9 | must | concept | malakut | | passages>=1000, works>=100 | The Malakut as a concept (ether case; v53) |
| A10 | must | concept | awwal_makhluq | | passages>=200, works>=50 | 'The first created thing' as a concept (ether case; v53) |
| A11 | must | concept | arsh | | passages>=1000, works>=100 | The Throne, sense-filtered (v53) |

## B. The Sunna: testing a saying

Known answers. Each saying has a standing that the critics state in their own words; the tool must reach it.

| id | level | check | input | where | expect | why |
|---|---|---|---|---|---|---|
| B1 | must | authenticate | إنما الأعمال بالنيات وإنما لكل امرئ ما نوى | | in:Bukhari, collections>=5, cites | A sound hadith is found in al-Bukhari with its parallels |
| B2 | must | authenticate | اطلبوا العلم ولو بالصين | | critic:Jawzi, critics>=12, modern_apart | A fabricated saying reaches the fabrication works |
| B3 | must | authenticate | من قارف ذنبا فارقه عقل لا يعود إليه أبدا | | not_in_layer, says:Iraqi:لم أر له أصلا, critic:Fattani | A saying with no source: al-ʿIraqi's verdict on al-Ghazali's hadith |
| B4 | must | authenticate | إن القلوب تصدأ كما يصدأ الحديد | | in:Bayhaqi, says:Iraqi:بسند ضعيف, critic:Jawzi | A weak hadith: the critic's words on the chain |
| B5 | must | authenticate | أتبع السيئة الحسنة تمحها | | in:Tirmidhi, grade:Tirmidhi:حسن صحيح, collections>=5 | The compiler's own grade is shown |
| B6 | must | authenticate | رفع القلم عن ثلاثة عن الصبي حتى يحتلم وعن المجنون حتى يفيق | | in:Abu Dawud, grade:Dhahabi:شرط, modern_apart | A later critic's verdict joined as data |
| B7 | must | authenticate | كنت كنزا مخفيا فأحببت أن أعرف | | not_in_layer, critic:Sakhawi, entries>=2 | Loose wording finds the critics who quote it differently |
| B8 | must | authenticate | إن الإسلام يهدم ما كان قبله وأن الهجرة تهدم ما كان قبلها | | in:Muslim | Found when given in Muslim's own wording |
| B9 | goal | authenticate | الإسلام يجب ما كان قبله | | in:Muslim | The same hadith in its popular wording should lead to Muslim's version |
| B10 | must | authenticate | إن العبد إذا أخطأ خطيئة نكتت في قلبه نكتة سوداء | | in:Tirmidhi, grade:Tirmidhi:حسن صحيح | Al-Tirmidhi's own hadith, in his layer since v53 with his grade |
| B12 | goal | authenticate | إنما الأعمال بالنيات وإنما لكل امرئ ما نوى | | in:Muslim | Muslim words it "بالنية ... لامرئ": the popular wording should still lead to his version |
| B11 | goal | authenticate | لو كشف عن نور المؤمن العاصي لطبق ما بين السماء والأرض | | critics>=1 | A master's saying (al-Shadhili) should be traced to who said it, not only reported as absent |
| B13 | must | authenticate | لما اقترف آدم الخطيئة قال يا رب أسألك بحق محمد لما غفرت لي | | in:Hakim, grade:Dhahabi:موضوع, modern_apart | Al-Hakim's "sound" and al-Dhahabi's "fabricated" on the same report, side by side (seven heavens case) |
| B14 | must | authenticate | لو أنكم دليتم بحبل إلى الأرض السفلى لهبط على الله | | in:Ahmad, critic:Sakhawi | A weak report with the reading its transmitters gave it |
| B15 | must | authenticate | لو أنكم دليتم بحبل إلى الأرض السفلى لهبط على الله | | in:Tirmidhi | Al-Tirmidhi's own hadith, in his layer since v53 |
| B16 | must | authenticate | أين كان ربنا قبل أن يخلق خلقه قال كان في عماء ما تحته هواء وما فوقه هواء | | in:Tirmidhi | The same: in his layer since v53 |
| B18 | must | authenticate | يا ابن آدم إنك ما دعوتني ورجوتني غفرت لك على ما كان منك ولا أبالي | | in:Tirmidhi, collections>=4 | The JK editions write 'يا بن آدم': ibn and bn are matched as one word since v53 (divine sayings case) |
| B19 | must | authenticate | إن أول ما خلق الله القلم فقال له اكتب | | in:Tirmidhi, in:Abu Dawud, grade:Tirmidhi:حسن غريب | The Pen hadith with al-Tirmidhi's own grade (ether case; v53) |
| B17 | goal | authenticate | ما السماوات السبع في الكرسي إلا كحلقة ملقاة بأرض فلاة | | in:Ibn Hibban | A short part of a long hadith should still find it in the layer |

## C. The masters of the council

Each master must be able to speak on the case in his own words. The test case is the heart as a mirror.

| id | level | check | input | where | expect | why |
|---|---|---|---|---|---|---|
| C1 | must | search | مرآة القلب | ghazali | records>=3 | Al-Ghazali on the mirror of the heart |
| C2 | must | search | مرآة القلب | ibnarabi | records>=3, works>=3 | Ibn ʿArabi on the same image |
| C3 | must | search | مرآة القلب | jilani | records>=3 | Al-Jilani on the same image |
| C4 | must | search | آینه دل | rumi,mathnawi | records>=5, each_folder | Rumi on the mirror of the heart, in Persian, in the Mathnawi and the Divan |
| C5 | must | search | الأسباب الخمسة | ghazali | records>=1 | The Ihya passage on the five causes is reachable by its own words |
| C6 | must | search | القلب | ghazali,ibnarabi,jilani,rumi | each_folder | The plain word "heart" reaches all four masters (Rumi where he writes in Arabic) |
| C7 | must | search | مرآة القلب | rumi,mathnawi | each_folder | An Arabic phrase reaches Rumi's Persian (آینه دل) through the term bridge (v53) |
| C20 | must | search | عالم الأمر | mathnawi | records>=2 | The Malakut in Rumi's own words (عالم امر, Mathnawi 4:3692-3693): the passage missed in the ether case |
| C21 | must | concept | fana_baqa | | passages>=400 | Rumi's couplets are in the concept index (فنا، نیستی add over 300 passages; v53) |
| C8 | must | search | بسوزد پر من | mathnawi | records>=1 | Rumi on Jibril's halt at the Sidra (seven heavens case) |
| C9 | must | search | الفلك الأطلس | ibnarabi | records>=20 | Ibn ʿArabi's cosmology: the starless sphere |
| C10 | must | search | نور المؤمن العاصي | wilaya | records>=2 | A master's saying traced to who said it: al-Shadhili, in Ibn ʿAtaʾ Allah and al-Shaʿrani (heart case) |
| C11 | must | search | صدأ القلوب | jilani | records>=1 | Al-Jilani's sermon on polishing the rust of hearts |
| C22 | must | search | أنا ربك | critics | records>=1 | The light that said 'I am your Lord': Ibn Taymiyya tells al-Jilani's story (Majmuʿ 1:172; Jilani case, v55) |
| C23 | must | search | تؤلمني | jilani | records>=1 | Al-Jilani's last illness, 'all my limbs pain me except my heart', in Futuh al-ghayb (Jilani case, v55) |
| C24 | must | search | مملوكا | jilani | records>=1 | The slave with no choice beside his master, in al-Fath al-rabbani (Jilani case, v55) |

## D. The caliphs and the Companions

The four caliphs sit on the council through what is reported from them.

| id | level | check | input | where | expect | why |
|---|---|---|---|---|---|---|
| D1 | must | caliph | Abu Bakr | | hadith>=100 | Hadith that reach Abu Bakr in the layer |
| D2 | must | caliph | Umar | | hadith>=500 | Hadith that reach ʿUmar |
| D3 | must | caliph | Uthman | | hadith>=150 | Hadith that reach ʿUthman |
| D4 | must | caliph | Ali | | hadith>=1000 | Hadith that reach ʿAli |
| D5 | must | search | متقلدا السيف فلقيه رجل من بني زهرة | sahaba,history | records>=2 | The report of ʿUmar's conversion in Ibn Saʿd and al-Baladhuri |
| D6 | must | search | قضى عمر | athar | records>=20 | ʿUmar's judgments in the Companion reports |
| D7 | must | search | قال أبو بكر الصديق | athar,sahaba,judging,consensus | each_folder | Abu Bakr's own sayings across the Companion folders |
| D8 | goal | search | قضى عمر | judging | records>=1 | The works on judging should carry the caliphs' judgments under a wording the council can find |

## E. The schools of law: showing a disagreement

The council must show the structure of a disagreement, not a verdict. That needs every school's position on the
same question.

| id | level | check | input | where | expect | why |
|---|---|---|---|---|---|---|
| E1 | must | search | ينقض الوضوء | hanafi,maliki,shafii,hanbali | each_folder, works>=20 | A common legal phrase reaches all four schools |
| E2 | must | search | اليقين لا يزول بالشك | hanafi,hanbali | each_folder | A legal maxim is found in the maxims literature |
| E3 | goal | search | لمس المرأة | hanafi,maliki,shafii,hanbali | each_folder | A real disagreement: one phrase misses the school that words it differently. Needs an index of legal questions |
| E4 | goal | search | القنوت في الصبح | hanafi,maliki,shafii,hanbali | each_folder | The same, for the qunut at dawn |

## F. Citing: every claim traceable

| id | level | check | input | where | expect | why |
|---|---|---|---|---|---|---|
| F1 | must | cite | urn:openiti:0902Sakhawi.MaqasidHasana.JK001160-ara1:p03238 | | | A critic's record resolves to its page |
| F2 | must | cite | urn:shamela:ghazali.ihya_with_iraqi:r01491 | | | The Ihya passage on the five causes resolves |
| F3 | must | cite | urn:hadith:0261Muslim.Sahih:121.1 | | | A hadith-layer id resolves to its source page (v53) |
| F4 | must | cite | urn:sufi:rumi.mathnawi:4.b3692 | | | A Mathnawi couplet resolves to its book and Nicholson number (v53) |
| F5 | must | cite | urn:hadith:0279Tirmidhi.Sunan:p08858 | | | A hadith added to al-Tirmidhi's layer in v53 resolves with its printed number |
| F6 | must | cite | urn:openiti:0748Dhahabi.SiyarAclamNubala.Shamela0010906-ara1:p126086 | | | Al-Dhahabi's closing verdict on al-Jilani resolves to its page (Jilani case, v55) |

## G. Classical and modern kept apart

| id | level | check | input | where | expect | why |
|---|---|---|---|---|---|---|
| G1 | must | authenticate | طلب العلم فريضة على كل مسلم | | modern_apart, says:Busiri:حفص, hadith>=10 | Modern verdicts never appear among the classical ones |
| G2 | must | authenticate | استغفروا لأخيكم وسلوا له التثبيت فإنه الآن يسأل | | in:Abu Dawud, grade:Nawawi:حسن, modern_apart | A classical critic and a modern one on the same hadith, in separate columns |

## H. The sijill: recording what the council found

| id | level | check | input | where | expect | why |
|---|---|---|---|---|---|---|
| H1 | must | sijill | validator | | | Every cited record resolves |
| H2 | must | sijill | type:position | | entries>=115 | Voices' positions are recorded |
| H3 | must | sijill | type:verdict | | entries>=78 | Verdicts on inferences are recorded |
| H4 | must | sijill | type:saying | | entries>=84 | Sayings examined by a study are recorded (22 seven heavens, 7 heart, 40 divine sayings, 12 ether, 3 Jilani) |
| H5 | must | sijill | type:authentication | | entries>=84 | What was found on each saying is recorded |
| H6 | goal | sijill | type:ruling | | entries>=1 | A juristic type exists and is used |

## I. Odd input

The same saying typed differently must give the same answer, and nothing typed may break a tool.

| id | level | check | input | where | expect | why |
|---|---|---|---|---|---|---|
| I1 | must | same | إنما الأعمال بالنيات وإنما لكل امرئ ما نوى // إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى | | | With and without vowel marks |
| I2 | must | same | أتبع السيئة الحسنة تمحها // اتبع السيئه الحسنه تمحها | | | With and without hamza and ta marbuta |
| I3 | must | crash | seek knowledge even in China | authenticate | | Latin text does not break the command |
| I4 | must | crash | نور | authenticate | | A one-word saying does not break the command |
| I5 | must | crash | آینهٔ دل ۱۲۳ | rumi | | Persian letters and digits do not break the search |

## J. Speed

A study chat pays for every second and every step.

| id | level | check | input | where | expect | why |
|---|---|---|---|---|---|---|
| J1 | must | time | authenticate_per_saying | | seconds<=8 | Testing a batch of sayings stays cheap per saying (about 2 seconds on two processors) |
| J2 | must | time | authenticate_all | | seconds<=180 | The whole batch of this document's sayings |
| J3 | goal | time | authenticate_per_saying | | seconds<=1 | Fast enough to test every saying in a long lecture at once |

## K. Size and coverage

Floors that catch a regression, and targets that measure progress. Measures: `hadith`, `collections`, `works`,
`authentication_works`, `dossiers`, `parallel_groups`, `hadith_fully_linked`, `share_names_linked`,
`share_no_classical_grade`, `share_nothing_at_all`, `share_no_grade_classical_or_modern`.

| id | level | check | input | where | expect | why |
|---|---|---|---|---|---|---|
| K1 | must | metric | hadith | | value>=164650 | The hadith layer has not shrunk |
| K2 | must | metric | collections | | value>=21 | All collections are in the layer |
| K3 | must | metric | works | | value>=390 | The works index has not shrunk |
| K4 | must | metric | share_no_classical_grade | | value<=0.705 | Classical grade coverage has not fallen back |
| K5 | must | metric | share_names_linked | | value>=0.44 | Narrator links have not fallen back |
| K6 | must | metric | share_no_grade_classical_or_modern | | value<=0.46 | With the modern column, under half the hadith have no grade at all |
| K7 | goal | metric | share_no_classical_grade | | value<=0.60 | Target: four in ten hadith with a classical grade |
| K8 | goal | metric | share_names_linked | | value>=0.60 | Target: most narrator names linked |
| K9 | must | metric | dossiers | | value>=8 | Dossiers: asma, fitra, nur, wilaya, the heart, Rumi, the first created thing, and since v55 al-Jilani |
| K10 | goal | metric | dossiers | | value>=10 | A dossier for each of the other masters (al-Ghazali, al-Jilani, Ibn ʿArabi) |

## L. The masters' stories: voice and layers of meaning

A master who teaches by stories is not quoted by the bare couplet. The couplet must come with its story, with who is
speaking, and with whose reading is given (the author's own stated meaning, a commentator's, a reader's, Claude's).

| id | level | check | input | where | expect | why |
|---|---|---|---|---|---|---|
| L1 | must | story | 1:263 | طوطی | heading==1, story==1, passages>=2, readings>=4 | 'Do not measure the pure by yourself' comes back with the grocer and the parrot, and with its recorded readings |
| L2 | must | story | urn:sufi:rumi.mathnawi:4.b3692 | | heading==1 | A couplet in another book comes back with Rumi's own heading for its section |
| L3 | must | story | 1:1575 | The merchant and his caged parrot | heading==1, story==1 | 'The parrot of the soul' belongs to a different story from the grocer's parrot: the same image, another tale |
| L4 | must | sijill | type:reading | | entries>=46 | Readings are recorded, several to a passage, each with its layer and its reader |
| L5 | must | sijill | type:passage | | entries>=15 | Passages are recorded with the voice that speaks in them |
| L9 | must | story | 1:323 | طوطی | heading==1, story==1, passages>=2, readings>=4 | The last couplet of the grocer and the parrot comes back with its section and its readings: the story is read to its end (v55) |
| L6 | goal | story | 2:1720 | | story==1 | A story map for Books 2 to 6 (only Book 1 is mapped; the others have Rumi's headings) |
| L7 | goal | search | مثنوی | mathnawi_sharh | records>=1 | A classical commentary on the Mathnawi, in a folder corpus/mathnawi_sharh, so that the stories are read through the tradition and not only through Claude |
| L8 | goal | sijill | type:reading | | entries>=60 | The grocer and the parrot read to its end (sections 9 to 12), and a second story begun |

## Changing this document

- **After a study:** add a `must` for each thing the tools did well and a `goal` for each thing they could not do.
- **After an update:** run the test. Goals that now pass become `must`. Raise the floors in section K to the new values.
- **When a case is wrong** (the expected answer was mistaken): correct it here and say why in `why`.
- The expected answers are a reader's, not a scholar's. A scholar's correction to a case is the most valuable edit.
