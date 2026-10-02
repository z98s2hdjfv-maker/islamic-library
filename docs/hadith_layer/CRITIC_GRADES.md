# v44: the critics' verdicts as data

**v47 adds five more critics, the compilers' own remarks, a wider Sahih note, more narrator links and a modern
column: see `GRADE_GAP_V47.md`. The counts below are those of v44.**

Until v43 only al-Dhahabi's verdicts on al-Hakim were joined to the hadith they judge; every other critic was prose to
be searched. v44 extracts the verdicts of the critics who write in a fixed formula and joins them to the hadith layer,
adds a note where a hadith's wording is also in al-Bukhari or Muslim, puts al-Albani on al-Tirmidhi in a separate modern
table, and gathers the critics' numbered entries on current sayings into one table.

Nothing in the corpus or in `apparatus/hadith` is edited. Every verdict is the critic's own words with the record to cite.

| Table | Critic | Verdicts found | Hadith that received a verdict |
|---|---|---|---|
| `apparatus/hadith_grades/busiri_misbah_ibnmaja.tsv` | al-Busiri (d. 840), Misbah al-zujaja | 1,245 | 1,231 of Ibn Maja |
| `apparatus/hadith_grades/haythami_majma.tsv` | al-Haythami (d. 807), Majma' al-zawa'id | 16,258 | 6,645 of Ahmad and al-Tabarani's Kabir |
| `apparatus/hadith_grades/dhahabi_talkhis_mustadrak.tsv` (v35) | al-Dhahabi (d. 748), Talkhis | 5,711 | 5,610 of al-Hakim |
| `apparatus/hadith_grades_modern/albani_tirmidhi.tsv` | al-Albani (d. 1420), MODERN | 3,777 | 3,651 of al-Tirmidhi |
| `apparatus/hadith_links/in_sahih.tsv.gz` | (a note, not a critic) | | 10,608 hadith whose wording is also in al-Bukhari or Muslim |
| `apparatus/sayings/sayings.tsv.gz` | al-Dhahabi, al-Sakhawi, al-Qari | 2,607 entries | 384 sayings found in more than one of the three |

Built by `pipeline/hadith/build_critic_grades.py` and `pipeline/hadith/build_sayings.py`; counts in
`catalogs/critic_grades_summary.json`. Columns are described at the top of each script.

## How to read a row
- **scope = chain.** al-Haythami and al-Busiri judge a chain or its narrators: "its narrators are trustworthy",
  "in it is so-and-so, who is weak". That is not "the hadith is sound" or "the hadith is weak": it says nothing of the
  other chains, of corroboration, or of hidden defects. Report it as his statement about that chain.
- **class** is a coarse label made by rule from his words, for filtering only. Always quote `verdict`.
- **candidates** above 1: the same wording has several chains in the collection and the verdict belongs to one of
  them. Read his passage before citing.
- **hadith_id empty:** the verdict is kept but no hadith in the layer matched. Most of al-Haythami's unjoined verdicts
  are on al-Bazzar, Abu Ya'la and al-Tabarani's Awsat and Saghir, which the library does not hold.
- **The Sahih wording note** says the wording is also in al-Bukhari or Muslim (at least 60% of the shorter text shared).
  The chain in the other collection may differ and may be weak. It is a pointer to the sound version, not a grade.
- **Modern stays apart**: its own folder, never added to the classical grades or to the search index's grades.
- **Sayings: `cues`** are verdict words in the order they occur; an entry may say "no chain is known, but the meaning
  is sound". Quote `verdict`.

## Joining rules
Texts normalised; transmission words dropped; compared by 3-word sequences. A verdict joins a hadith when at least half
of the critic's quoted sequences occur in it (at least 4), and for al-Haythami also when (a) the Companion he names is in
that hadith's chain, (b) the wording itself is shared, not only names, and (c) a verdict that names its source ("the
narrators of Ahmad are trustworthy") goes only to that collection. More than five equal matches: left unjoined.

## Coverage after v44 (113,509 hadith)
| | Hadith | Share |
|---|---|---|
| No classical grade before v44 | 86,819 | 76.5% |
| No classical grade after v44 | 78,943 | 69.5% |
| Neither a classical grade nor the Sahih wording note | 69,041 | 60.8% |

What remains is mostly Ahmad (20,479), al-Tabarani (16,010), al-Nasa'i (14,220), Abu Dawud (4,671), al-Daraqutni
(4,454), al-Darimi (3,206) and Ibn Maja (2,607). No classical work in the library grades these hadith one by one.
To go further the library needs more works: see "Next" below.

## Checked by hand (2026-10-01, by Claude, not a scholar)
al-Haythami: 55 random joins read after tuning, 54 the right hadith and Companion, 1 doubtful. al-Busiri: 8 of 8.
al-Albani on al-Tirmidhi: 6 of 6. Sahih wording note: 6 of 6. Status: unverified until a scholar samples them.

## Next
- Works that would grade what remains: al-Mundhiri's Mukhtasar Sunan Abi Dawud and al-Targhib; al-Zayla'i's and Ibn
  Hajar's takhrij (in the library, but their verdicts are discursive, not formulaic); al-Bazzar's and Abu Ya'la's
  musnads and al-Tabarani's Awsat (so al-Haythami's other 9,000 verdicts can join); Ibn Hibban's Sahih; for a modern
  column, al-Arna'ut on Ahmad's Musnad and al-Albani on Abu Dawud, al-Nasa'i and Ibn Maja.
- Ibn al-Jawzi's Mawdu'at and al-Suyuti's La'ali as entries in the sayings table (they need their chains parsed).
