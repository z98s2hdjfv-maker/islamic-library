# Dossier: the heart (qalb) and its mirror

> **A map, not an answer.** This dossier says where the library's evidence is. Query the repo and cite from the files.

*From the heart case (2 October 2026): Dr. Umar Faruq Abd-Allah's lecture on al-Ghazali's five conditions of the heart.* Repo state: v53.

## 1. Start here
```
python3 pipeline/index/lookup.py --repo . --concept qalb                      # the doctrine of the heart by phrases: 3,371 passages, 221 works
python3 pipeline/index/lookup.py --repo . --concept qalb --work ghazali,jilani,ibnarabi,rumi,mathnawi
python3 pipeline/index/lookup.py --repo . --verse 83:14                       # "what they earned has rusted upon their hearts"
python3 pipeline/search/textsearch.py "مرآة القلب" --folder rumi,mathnawi      # reaches Rumi's آینه دل through the term bridge
python3 pipeline/hadith/authenticate.py --brief "إن العبد إذا أخطأ خطيئة نكتت في قلبه نكتة سوداء" "إن القلوب تصدأ كما يصدأ الحديد"
```
The concept `qalb` indexes phrases (the mirror, rust, polish, hardness, life, death and soundness of the heart), not the bare word, which is on almost every page. Verses: 83:14, 6:122, 26:89, 22:46, 50:37, 39:22.

## 2. Al-Ghazali's five causes (the spine of the subject)
Ihyaʾ, the Book of the Wonders of the Heart, 3:490-492: `urn:shamela:ghazali.ihya_with_iraqi:r01490`, `r01491`, `r01492`. A mirror fails to show an image for five reasons, and so does the heart:
1. deficiency in itself (the heart of a child);
2. the murk of sins;
3. being turned away from the reality sought, even in obedience;
4. a veil of belief received by imitation;
5. not knowing the direction from which the thing is found: the two premises that must be paired.

## 3. The voices
| Voice | What he says | Where |
|---|---|---|
| The Qur'an | "What they earned has rusted upon their hearts" | 83:14 |
| The Prophet ﷺ | The black spot on the heart, polished by repentance: sound (al-Tirmidhi, printed 3334: fair and sound; al-Nasaʾi; Ibn Hibban) | `urn:hadith:0279Tirmidhi.Sunan:p08858` (in his layer since v53) |
| al-Ghazali (d. 505) | the five causes; a mirror wiped after being soiled is not like one never stained | Ihyaʾ 3:490-492 |
| al-Jilani (d. 561) | "Polishing the rust of hearts"; "make me your mirror" | al-Fath al-rabbani, `urn:shamela:jilani.fathrabbani:r00106`, `r00035` |
| Ibn ʿArabi (d. 638) | the rust is the wrong images themselves; the polish is remembrance and recitation | Futuhat 4:25, `urn:shamela:ibnarabi.futuhat.arabiyya:r02051` |
| Rumi (d. 672) | "Do you know why your mirror tells nothing? Because the rust has not been cleared from its face" | Mathnawi 1:34, 2:72, 1:3154; see the Rumi dossier |
| al-Shadhili (d. 656) | the light of the disobedient believer (his saying, not a hadith) | Lataʾif al-minan p. 31 (OCR) |

## 4. Sayings and their standing (from the sijill)
| Saying | Standing |
|---|---|
| The black spot on the heart | sound |
| "Follow a bad deed with a good one" | sound (al-Tirmidhi: fair and sound) |
| "Hearts rust as iron rusts" | weak (al-ʿIraqi) |
| "Whoever commits a sin, an intellect leaves him" | no basis (al-ʿIraqi: "I have seen no basis for it") |

## 5. In the sijill
`topic:heart`; 15 verdicts `verdict:heart-*`; positions `position:heart-01` to `heart-19`. The speaker is confirmed as Dr. Umar Faruq Abd-Allah (`position:housam-confirms-heart-speaker`).

## 6. Gaps
- The standing of Ibn Masʿud's saying that sin makes one forget knowledge (do list item 26).
- The classical grade of Anas's report of ʿUmar's conversion (item 27).
- The verdicts of the earlier chat on this lecture have not been compared with this run (item 21).
