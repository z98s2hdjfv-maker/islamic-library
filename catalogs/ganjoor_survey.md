# Other works from Ganjoor: survey and v7 import (2026-09-25)

## v7 addendum: imported
`library_v7_addendum_2026-09-25.zip` (17 MB) goes on the iPad next to the v6 zip; v6 is not replaced. It was built by `ingest_works2.py` from ganjoor-data commit a64968e, the same commit v6 used. The unit logic is the same as v6, and every unit is `unverified`. Counts are in `works_summary_v7.json`. There are 42 works and 215,670 units (couplets or paragraphs). All catalog pages were found. No IDs are duplicated, and a second run reproduced every file byte for byte.

A new field, `attribution`, is set per work. **secure** covers 154,990 units. **doubtful** covers 11,202: the Jilani Divan, 'Iraqi's 'Ushshaq-nama and Istilahat, Shabistari's Mir'at, Kanz and Maratib, and 'Attar's Khusraw-nama. **spurious_attested** covers 49,478: the Tariq al-tahqiq ascribed to Sana'i, and eleven pseudo-'Attar works (Pand-nama, Futuwwat-nama, Bulbul-nama, Si fasl, Bayan al-irshad, Bi-sar-nama, Hilaj-nama, Mazhar, Jawhar al-dhat, Mazhar al-'aja'ib, Wuslat-nama, Nuzhat al-ahbab, Ushtur-nama). These ratings are the model's reading of general scholarly opinion. They still need review by a scholar.

- **Al-Ghazali:** Kimiya-yi sa'adat, 443 sections, 3,348 paragraphs.
- **Divan attributed to al-Jilani:** 74 ghazals, 641 couplets. Rated doubtful.
- **Maybudi:** Kashf al-asrar, 1,337 sections, 28,133 paragraphs and 2,008 couplets. IDs run by sura. Its 20,948 "not NFC" warnings come from the vowel-mark order in the Qur'anic Arabic. They were kept, as in the Mathnawi.
- **Ibn 'Arabi school:** 'Iraqi's Lama'at, Divan, 'Ushshaq-nama and Istilahat; Awhad al-Din Kirmani's ruba'is; Shabistari's Gulshan-i raz, Haqq al-yaqin, Sa'adat-nama, Mir'at, Kanz and Maratib; Jami's Divan, Haft awrang, Baharistan and Arba'in.
- **Rumi's sources:** Sana'i's Hadiqa, Divan and Tariq; 'Attar's Mantiq al-tayr, Ilahi-nama, Musibat-nama, Asrar-nama, Tadhkirat al-awliya, Divan, Mukhtar-nama and Khusraw-nama, plus the pseudo-'Attar works.

## Checked and not on Ganjoor
- Rumi circle: Ganjoor has nothing beyond what v6 holds. Shams-i Tabrizi, Aflaki, Sipahsalar and Burhan al-Din are not there. ("Shams Maghribi" is a different, later poet.)
- Ibn 'Arabi himself, and al-Jilani's and al-Ghazali's Arabic works: these need Arabic sources.
- Available but not imported: Hujwiri's Kashf al-mahjub (210); Najm al-Din Razi's Mirsad al-'ibad (43); 'Ayn al-Qudat's Tamhidat and Lawa'ih; Ansari (Tabaqat al-sufiyya, Sad maydan, Munajat); Asrar al-tawhid (477); Shah Ni'matullah Wali.
