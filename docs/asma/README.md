# The Beautiful Names and the address to God (v26)

15 works from OpenITI in `corpus/asma/` (search `--author asma`), plus a table of the 99 names that joins the
Qur'an, the ḥadīth and the commentaries: `reports/asma/names.tsv`.

| Strand | Works |
|---|---|
| hadith | Ibn Ḥajar, *Takhrīj aḥādīth al-asmāʾ al-ḥusnā*; al-Bayhaqī, *al-Asmāʾ wa-l-ṣifāt* |
| language | al-Zajjāj, *Tafsīr asmāʾ Allāh*; al-Zajjājī, *Ishtiqāq asmāʾ Allāh*; al-Khaṭṭābī, *Shaʾn al-duʿāʾ* |
| commentary | al-Ghazālī, *al-Maqṣad al-asnā*; al-Qurṭubī, *al-Asnā*; Fakhr al-Dīn al-Rāzī, *Lawāmiʿ al-bayyināt*; Ibn ʿAṭāʾ Allāh, *al-Qaṣd al-mujarrad* (on the name *Allāh*) |
| address | Ibn ʿAṭāʾ Allāh, *al-Ḥikam* (with his *munājāt*); al-Jazūlī, *Dalāʾil al-khayrāt*; al-Nawawī, *al-Adhkār*; Ibn al-Qayyim, *al-Wābil al-ṣayyib*; al-Jīlānī, *al-Ghunya* and *Jalāʾ al-khāṭir* |

Already in the library and central here: Ibn ʿArabī's Futūḥāt ch. 558, "on knowing the Beautiful Names,"
one *ḥaḍra* (presence) per name (`corpus/ibnarabi/futuhat.arabiyya` r02226–r02360, Cairo ed. IV:196–326);
the Fuṣūṣ; al-Qayṣarī's Muqaddima ch. 2–3 on the names and the fixed entities (`corpus/nur`);
al-Qushayrī's *Laṭāʾif al-ishārāt*; the Mathnawī.

## The names table (`pipeline/asma/build_names_table.py`)
The list comes from the only narration that enumerates the names: al-Tirmidhī, *Jāmiʿ* (record p09314),
read from the corpus, never retyped: Allāh and 98 names. For each name: verses of the Qur'an containing its
word form (a form count: *al-ḥaqq* or *al-ʿalī* also have ordinary uses), the first such verse, the unit where
al-Ghazālī's *Maqṣad* treats it (all 98 found; he treats *Allāh* in his introduction), and the number of
units of al-Qurṭubī's *Asnā* naming it.

**On the list itself.** "God has ninety-nine names; whoever enumerates them enters Paradise" is sound
(al-Bukhārī, Muslim), but without a list. Al-Tirmidhī grades the listed version *gharīb* and says no other
chain listing the names is sound. Ibn Ḥajar (*Takhrīj*, p. 12) finds the weakness not in al-Walīd b. Muslim's
reliability but in "the possibility that the list was inserted (*mudraj*) by one of the narrators," supported by
other narrations that list different names. Many Qur'anic names (e.g. *al-Rabb*, *al-Ilāh*, *al-Akram*) are absent
from it, and several listed names do not occur in the Qur'an in that form (the table shows which).

## Caveats
Uncorrected OCR (OpenITI Kraken/AOCP): al-Qurṭubī, al-Rāzī, al-Qaṣd al-mujarrad, Dalāʾil al-khayrāt, Jalāʾ al-khāṭir.
*al-Ḥikam* is one OpenITI version with little paragraphing (12 units).
Still missing: al-Qushayrī's *al-Taḥbīr fī ʿilm
al-tadhkīr*, and Ibn ʿArabī's *Awrād al-usbūʿ*: candidates for the witness and archive.org searches.

## v27: two works from archive.org scans (`catalogs/archive_works.tsv`, uncorrected OCR)
- **Ibn ʿArabī, *Kashf al-maʿnā ʿan sirr asmāʾ Allāh al-ḥusnā*** (`corpus/asma/0638IbnCarabi.KashfMacna`, 194 leaves):
  a modern critical edition collating three manuscripts. Its governing rule (leaf 53): the servant has three
  relations with every divine name: *taʿalluq* (dependence on it, as it points to the Essence), *taḥaqquq*
  (knowing its meaning as it applies to Him and to you) and *takhalluq* (standing in it as befits you, as it is
  ascribed to Him as befits Him). All the names can be taken on as traits except *Allāh*, which is for
  dependence alone. Check wording against Beneito's edition (`beneito2024_secret_names`).
- **Ibn ʿArabī, *Tarjumān al-ashwāq*** with his own commentary *Dhakhāʾir al-aʿlāq*
  (`corpus/ibnarabi/0638IbnCarabi.TarjumanAshwaq`, 242 leaves), ed. ʿAbd al-Raḥmān al-Muṣṭāwī (2004).
Script: `pipeline/works/ingest_archive_works.py` (general form of the v20 script; the target folder is a column).
