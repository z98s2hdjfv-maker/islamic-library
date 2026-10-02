# v45: the authentication canon (54 works)

The audit (v42) listed works a hadith critic reaches for that the library lacked. All of them were found in OpenITI as
typed text (none is OCR) and are imported by `pipeline/works/ingest_canon.py --canon authentication` from pinned files
(`catalogs/authentication_canon.tsv`, `catalogs/authentication_canon_pins.json`: repo, commit, path, sha256).

| Folder | Works | What they are |
|---|---|---|
| `corpus/hadith_extra/` | 8 | Collections: al-Bazzar's Musnad, Abu Ya'la's Musnad, al-Tabarani's Awsat and Saghir, Ibn Hibban's Sahih (in Ibn Balban's arrangement, al-Ihsan), al-Bayhaqi's Shu'ab al-iman, the Musnads of al-Tayalisi and al-Humaydi |
| `corpus/grading/` | 16 added | al-Mundhiri (Mukhtasar Sunan Abi Dawud, al-Targhib); al-Haythami's zawa'id books (Kashf al-astar, al-Maqsad al-'ali, Mawarid al-zam'an, Ghayat al-maqsad); Ibn Hajar (al-Matalib al-'aliya, Mukhtasar zawa'id al-Bazzar, al-Diraya, Bulugh al-maram); Ibn al-Mulaqqin's al-Badr al-munir; al-Nawawi's Khulasa; Ibn 'Abd al-Hadi (Tanqih, al-Muharrar); al-Zayla'i on the Kashshaf; al-Suyuti's al-Jami' al-saghir |
| `corpus/mawduat/` | 11 | Fabricated and current sayings: al-'Ajluni's Kashf al-khafa', Ibn 'Arraq's Tanzih al-shari'a, al-Fattani, al-Shawkani, al-Suyuti's Durar, al-Jawraqani's Abatil, Ibn al-Jawzi's 'Ilal mutanahiya, Ibn al-Qaysarani (two), al-Saghani, Ibn 'Abd al-Hadi |
| `corpus/cilal/` | 8 | Hidden defects: al-Daraqutni, Ibn Abi Hatim, al-Tirmidhi's 'Ilal kabir, Ibn al-Madini, Ahmad. Narrator criticism: Ibn 'Adi's Kamil, al-'Uqayli, Ibn Hibban's Majruhin |
| `corpus/mustalah/` | 10 | Hadith method: al-Ramahurmuzi, al-Hakim, al-Khatib's Kifaya, Ibn al-Salah's Muqaddima, al-Nawawi's Taqrib, Ibn Hajar's Nukhba, Nuzha and Nukat, al-Suyuti's Tadrib, al-'Iraqi's Alfiyya |
| `corpus/modern/` | 1 added | MODERN: al-Albani's Sahih wa-da'if al-Jami' al-saghir (14,550 verdicts) |

## What changes for a study
- `authenticate.py` now searches 59 works (was 19): `catalogs/authentication_works.tsv`. "Seek knowledge even in China"
  went from 6 classical works to 16, from al-'Uqayli (d. 322) to al-Shawkani.
- The sayings table gained al-'Ajluni's 3,240 entries (5,847 in all; 1,234 sayings appear in more than one work), and
  al-Albani's 14,550 verdicts are a separate modern table (`apparatus/sayings/sayings_modern.tsv.gz`).
- The eight new collections are searched as text and shown in their own section. They are **not yet in the hadith
  layer**: no numbering, parallels, chain data or joined verdicts. That is the next step, and it is what lets
  al-Haythami's remaining 9,300 verdicts (on al-Bazzar, Abu Ya'la, the Awsat and Saghir) join their hadith.

## Cautions
- **al-Mundhiri's Mukhtasar (ed. Hallaq):** the bracketed tags after a hadith ([صحيح], [ضعيف]) are the modern editor's.
  al-Mundhiri's own words follow the bullet. Never cite a bracket as al-Mundhiri.
- **Ibn Hibban's Sahih** is filed in OpenITI under Ibn Balban (d. 739), who rearranged it; the hadith and the claim of
  soundness are Ibn Hibban's (d. 354). Footnote gradings in this edition, where present, are modern.
- **al-Albani's Sahih wa-da'if al-Jami'** is filed in OpenITI under al-Suyuti (key `modern.0911Suyuti.SahihWaDacif`);
  the verdicts are al-Albani's and the work is in the modern layer.
- **al-Jami' al-saghir:** the printed grade symbols are known to be unreliable in places.
- The works were chosen by Claude as the standard reference set; scholar review of the list is pending.

## Not found, still to source
al-Munawi's Fayd al-qadir is in OpenITI (1.6 million words) and was left out for size; say the word to add it.
Modern gradings of Ahmad's Musnad (al-Arna'ut) and al-Albani's gradings of Abu Dawud, al-Nasa'i and Ibn Maja are not
in OpenITI as separate works.
