# Dossier: Rumi's voice (Mawlana Jalal al-Din Rumi, d. 672 AH)

> **A map, not an answer.** This dossier says where Rumi speaks on the subjects the cases keep returning to. Before answering, query the repo itself (see `START_HERE.md`), open the couplets and read around them. Cite from the files, not from this page.

*Why this dossier exists.* Rumi was reported silent in the ether case because the search was made in Arabic. He writes in Persian with his own vocabulary. Rule (START_HERE.md, section 4b): never record him as silent before his own words have been searched. Repo state: v54.

## 1. What the library holds

| Work | Where | Size | Note |
|---|---|---|---|
| Mathnawi, six books | `corpus/mathnawi/full/book1..6.jsonl` (also `corpus/mathnawi/book1..6.tsv`) | 25,637 couplets | Ganjoor text; ids `urn:sufi:rumi.mathnawi:<book>.b<number>`; Nicholson numbering, fully checked only in Book 1 |
| Divan-i Shams | `corpus/rumi/diwan.gh` (ghazals), `.rb` (quatrains), `.tj`, `.ms` | about 40,000 couplets | individual poems may be spurious; many quatrains are doubtful |
| Fihi ma fihi | `corpus/rumi/fihi.d.jsonl` | 269 passages | his prose discourses |
| Majalis-i sabʿa | `corpus/rumi/majalis.m.jsonl` | 669 passages | seven sermons |
| Around him | `corpus/shams`, `corpus/bahawalad`, `corpus/sultanwalad`, `corpus/aflaki` | | Shams's Maqalat is OCR; his letters (Maktubat) are not in the library |

No translation is stored. Claude reads the Persian and translates each passage it quotes; every translation below is Claude's own and is a reading aid, to be checked by a reader of Persian. There is no classical commentary on the Mathnawi in the library yet (do list item 58), so every reading of a story is a reader's reading unless Rumi states the moral himself.

## 2. How to reach him
```
python3 pipeline/search/textsearch.py "مرآة القلب" "عالم الأمر" --folder rumi,mathnawi     # Arabic term -> his Persian words (term bridge)
python3 pipeline/search/textsearch.py "لامکان" --folder rumi,mathnawi --count                # or search his word directly
python3 pipeline/index/lookup.py --repo . --concept malakut --work rumi,mathnawi --per-work 5   # his couplets on a concept
```
The bridge is `catalogs/term_bridge.tsv`: one row per Arabic term with his Persian words for it. Add a row when a term is missing. A Persian word matched through the bridge is not sense-filtered: read the couplet.

## 3. Where he speaks, by subject

Counts are passages in his works in the concept index (v53). The couplets are a first selection, a few per subject, not all he says.

### The heart and its mirror (qalb)
`--concept qalb --work rumi,mathnawi` (222 passages). His words: آینه دل (mirror of the heart), صیقل (polish), زنگار (rust), چشم دل (eye of the heart), اهل دل (people of heart).

| Mathnawi | id | Persian | Claude's translation |
|---|---|---|---|
| 1:34 | `1.b0034` | آینه‌ت دانی چرا غمّاز نیست؟ / زآن که زنگار از رخش مُمتاز نیست | Do you know why your mirror tells nothing? Because the rust has not been cleared from its face. |
| 1:3154 | `1.b3154` | سینه صیقلها زده در ذکر و فکر / تا پذیرد آینهٔ دل نقش بکر | They have polished their breasts in remembrance and reflection, so that the mirror of the heart may receive the virgin image. |
| 2:72 | `2.b0072` | آینهٔ دل چون شود صافی و پاک / نقش‌ها بینی برون از آب و خاک | When the mirror of the heart becomes clear and pure, you will see images beyond water and clay. |
| 2:2063 | `2.b2063` | آینهٔ دل صاف باید تا درو / وا شناسی صورت زشت از نکو | The mirror of the heart must be clear, so that in it you may tell the ugly form from the fair. |
| 1:725 | `1.b0725` | دل ترا در کوی اهلِ دل کشد / تن ترا در حبس آب و گل کشد | The heart draws you to the quarter of the people of heart; the body draws you to the prison of water and clay. |
| 3:2245 | `3.b2245` | تو همی‌گویی مرا دل نیز هست / دل فراز عرش باشد نی به پست | You say: I too have a heart. The heart is above the Throne, not down below. |

### The unseen realm (Malakut): the placeless and the world of the Command
`--concept malakut --work rumi,mathnawi` (150). The Arabic word ملکوت occurs 4 times in all his works and never in the Mathnawi. His words: لامکان (the placeless, 91 times), عالم امر (world of the Command), بی‌جهت (directionless), جهان جان / عالم جان (world of the soul), عالم غیب.

| Mathnawi | id | Persian | Claude's translation |
|---|---|---|---|
| 4:3692 | `4.b3692` | عالم خلقست با سوی و جهات / بی‌جهت دان عالم امر و صفات | The world of creation has sides and directions; know the world of the Command and the attributes to be without direction. |
| 4:3693 | `4.b3693` | بی‌جهت دان عالم امر ای صنم / بی‌جهت‌تر باشد آمر لاجرم | Know the world of the Command to be without direction, my dear; the Commander, then, is more without direction still. |
| 1:1581 | `1.b1581` | صورتش بر خاک و جان بر لامکان / لامکانی فوق وهم سالکان | His form is on the earth and his soul in the placeless, a placelessness beyond the fancy of the wayfarers. |
| 1:1026 | `1.b1026` | می‌زند بر تن ز سوی لامکان / می‌نگنجد در فلک خورشید جان | It strikes the body from the side of the placeless; the sun of the soul is not contained in the sky. |
| 3:3971 | `3.b3971` | آنچنانک چار عنصر در جهان / صد مدد آرد ز شهر لامکان | Just as the four elements in this world draw a hundred supplies from the city of the placeless. |

### The Ascent, the Throne and the seven heavens
`--concept miraj` (76), `arsh` (146), `kursi` (35), `sab_samawat` (66), `sidra` (16), each with `--work rumi,mathnawi`. His words: معراج، براق، عرش، کرسی، هفت آسمان، هفت گردون، سدره.

| Mathnawi | id | Persian | Claude's translation |
|---|---|---|---|
| 2:2226 | `2.b2226` | قصد در معراج دید دوست بود / درتبع عرش و ملایک هم نمود | The aim in the Ascent was the sight of the Friend; the Throne and the angels were shown along the way. |
| 4:553 | `4.b0553` | نه چو معراج زمینی تا قمر / بلک چون معراج کلکی تا شکر | Not like an ascent from the earth to the moon, but like the ascent of a reed to sugar. |
| 3:4512 | `3.b4512` | گفت پیغامبر که معراج مرا / نیست بر معراج یونس اجتبا | The Prophet said: my ascent has no preference over the ascent of Yunus. |
| 1:2652 | `1.b2652` | در فراخی عرصهٔ آن پاک‌جان / تنگ آمد عرصهٔ هفت آسمان | In the breadth of that pure soul's field, the field of the seven heavens became narrow. |
| 5:872 | `5.b0872` | دل که گر هفصد چو این هفت آسمان / اندرو آید شود یاوه و نهان | A heart in which seven hundred of these seven heavens would be lost and hidden. |

### The Light
`textsearch.py "نور الله" --folder rumi,mathnawi` (bridge: نور حق 33, نور خدا 12); `--concept nur_muhammadi` (13: نور محمد، نور مصطفی، نور احمد).

| Mathnawi | id | Persian | Claude's translation |
|---|---|---|---|
| 2:1286 | `2.b1286` | چشم حس اسپست و نور حق سوار / بی‌سواره اسپ خود ناید به کار | The eye of sense is the horse and the light of God the rider; without the rider the horse is of no use. |
| 2:1295 | `2.b1295` | زانک محسوسات دونتر عالمیست / نور حق دریا و حس چون شب‌نمیست | For the things of sense are a lower world; the light of God is a sea and sense is like a dewdrop. |
| 6:1861 | `6.b1861` | آنچنان که از صقل نور مصطفی / صد هزاران نوع ظلمت شد ضیا | As, from the polish of the light of Mustafa, a hundred thousand kinds of darkness became radiance. |

### The saints (wilaya) and the Pole
`--concept wilaya` (98), `qutb` (38), `abdal` (17). His words: اولیا، مرد حق، مردان خدا، قطب، ابدال، پیر. He does not use the term 'the Perfect Human' (انسان کامل: 0 times).

| Mathnawi | id | Persian | Claude's translation |
|---|---|---|---|
| 1:265 | `1.b0265` | هَمسری با انبیا برداشتند / اولیا را همچو خود پنداشتند | They claimed equality with the prophets; they supposed the saints to be like themselves. |
| 2:2214 | `2.b2214` | چون شوی دور از حضور اولیا / در حقیقت گشته‌ای دور از خدا | When you are far from the presence of the saints, you are in truth far from God. |
| 1:1930 | `1.b1930` | هین که اسرافیل وقتند اولیا / مرده را زیشان حیاتست و نما | Take heed: the saints are the Israfil of the age; from them the dead have life and growth. |
| 2:1984 | `2.b1984` | سر نخواهی که رود، تو پای باش / در پناهِ قطبِ صاحب‌راٰی باش | If you do not want to lose your head, be a foot; be under the protection of the Pole who has judgement. |

### The covenant and the fitra
`--concept fitra --work rumi,mathnawi` (90). He says الست (Alast, the day of 'Am I not your Lord?', 86 times) far more than فطرت (4 times).

| Mathnawi | id | Persian | Claude's translation |
|---|---|---|---|
| 1:1241 | `1.b1241` | بُد عُمر را نام اینجا بت‌پرست / لیک مؤمن بود نامش در اَلَست | Here ʿUmar's name was idol-worshipper, but at Alast his name was believer. |
| 3:2348 | `3.b2348` | هر که خوابی دید از روز الست / مست باشد در ره طاعات مست | Whoever saw a dream of the day of Alast is drunk on the path of obedience, drunk. |
| 2:2970 | `2.b2970` | هر که در روز الست آن شیر خورد / همچو موسی شیر را تمییز کرد | Whoever drank that milk on the day of Alast distinguishes the milk, as Moses did. |

### Annihilation (fana)
`--concept fana_baqa --work rumi,mathnawi` (373). His words: فنا (223) and نیستی (non-being, 151).

| Mathnawi | id | Persian | Claude's translation |
|---|---|---|---|
| 5:4146 | `5.b4146` | کی شود کشف از تفکر این انا / آن انا مکشوف شد بعد از فنا | How should this 'I' be unveiled by thinking? That 'I' is unveiled after annihilation. |
| 4:555 | `4.b0555` | خوش براقی گشت خنگ نیستی / سوی هستی آردت گر نیستی | The steed of non-being became a fine Buraq: it brings you to Being, if you have become nothing. |

### The decree, compulsion and free choice
`--concept qada_qadar --work rumi,mathnawi` (339). His words: قضا، جبر، اختیار.

| Mathnawi | id | Persian | Claude's translation |
|---|---|---|---|
| 1:617 | `1.b0617` | این نه جَبر این معنی جبّاری است / ذکرِ جبّاری برای زاری است | This is not compulsion (jabr); it is the meaning of His almightiness (jabbari). The mention of almightiness is for the sake of humility. |
| 1:618 | `1.b0618` | زاری ما شد دلیل اضطرار / خجلت ما شد دلیل اختیار | Our weeping is the proof of our helplessness; our shame is the proof of our free choice. |
| 5:3018 | `5.b3018` | جملهٔ عالم مقر در اختیار / امر و نهی این میار و آن بیار | The whole world acknowledges free choice: command and prohibition, 'bring this' and 'do not bring that'. |

### The Universal Intellect
`--concept aql_awwal --work rumi,mathnawi` (68). His words: عقل کل، عقل کلی, set against the partial intellect (عقل جزوی).

| Mathnawi | id | Persian | Claude's translation |
|---|---|---|---|
| 2:978 | `2.b0978` | این جهان یک فکرتست از عقل کل / عقل چون شاهست و صورتها رسل | This world is one thought from the Universal Intellect; the Intellect is like a king and the forms are its envoys. |
| 4:1258 | `4.b1258` | عقل جزوی را وزیر خود مگیر / عقل کل را ساز ای سلطان وزیر | Do not take the partial intellect as your vizier; make the Universal Intellect your vizier, O king. |

## 4. Positions already recorded in the sijill

- The heart's mirror and its rust: `position:heart-05` (Mathnawi 1:34, 2:72, 1:3154).
- The unseen realm is real and has no location: `position:ether-rumi-placeless` (4:3692-3693, 1:1581). Corrected on 3 October 2026 after the Persian search.
- 'I am as My servant thinks of Me': `position:qudsi-rumi-as-my-servant-thinks` (Fihi ma fihi, `urn:sufi:rumi.fihi:d10.p005`).
- The seven heavens case and the fitra case each record a position of his; see `sijill/views/voices.md`.

## 5. Reading his stories

A couplet from a story is quoted with its story, its speaker (the narrator, a character, or Rumi in his own voice) and the layer of the meaning given (the plain sense, Rumi's own stated moral, a reader's reading). START_HERE.md, section 4c.

```
python3 pipeline/mathnawi/story.py 1:263 --show 2     # the couplet, Rumi's heading for its section, its story, its recorded readings
python3 pipeline/mathnawi/story.py --stories 1         # the 20 stories of Book 1 (Claude's reading of the headings)
python3 pipeline/mathnawi/story.py --headings 4        # Rumi's own headings for any book: all 972 sections are in apparatus/mathnawi/sections.tsv
```

The first story read this way is the grocer and the parrot (1:247-323): 11 passages and 33 readings in the sijill (`sijill/views/readings.md`), sections 1 to 8 of 12. Rumi's own stated moral is "do not measure the affairs of the pure by yourself" (1:263). The same image is not one fixed symbol: "the parrot of the soul" (1:1575) belongs to another story, the merchant and his caged parrot.

## 6. Confidence and gaps

- The Persian text is typed (Ganjoor) and unverified against a critical edition; Book 1 has been compared with the Konya manuscript pages on a pilot basis (`apparatus/mathnawi`).
- Nicholson numbers outside Book 1 are derived and may be off by a few couplets.
- The translations are Claude's. The selection is Claude's. Neither has been reviewed by a scholar.
- Missing: a classical commentary, Rumi's letters, Aflaki's Manaqib in a clean text, Shams's Maqalat in a typed text.
