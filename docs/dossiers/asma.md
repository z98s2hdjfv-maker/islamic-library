# Dossier: the Beautiful Names (al-asmāʾ al-ḥusnā)
*How the Names join creation to the Creator, why they were taught to Adam, and how we address Him by them.*
Repo state: v30. Load this file into the Claude Project so a new chat starts here. Record ids below are the
last part of each `id` in the corpus; open them with `pipeline/index/lookup.py`.

## 1. Start here (one command each)
```
python3 pipeline/index/lookup.py --repo . --verse 2:31        # the names taught to Adam: 246 passages, 32 works
python3 pipeline/index/lookup.py --repo . --verse 7:180       # "call upon Him by them": 215 passages, 34 works
python3 pipeline/index/lookup.py --repo . --verse 17:110      # "call Him Allah or al-Rahman": 528 passages, 51 works
python3 pipeline/index/lookup.py --repo . --verse 59:23       # the densest cluster of names: 566 passages, 54 works
python3 pipeline/index/lookup.py --repo . --concept takhalluq --work asma,ibnarabi
python3 pipeline/index/lookup.py --repo . --concept kawn_jami --work nur,ibnarabi
```
Also: 20:8 (36 passages), 59:22 (346), 59:24 (76), and the names table `reports/asma/names.tsv`
(each of the 99: Qur'an form count, first verse, al-Ghazālī's unit, al-Qurṭubī's units).

## 2. The ḥadīth base: settled and unsettled
- **Sound:** "God has ninety-nine names; whoever enumerates them enters Paradise" (al-Bukhārī, Muslim), with no list.
- **The list:** only in al-Tirmidhī (`0279Tirmidhi.Sunan` p09314), graded by him *gharīb*: "no other chain listing
  the names is sound." Ibn Ḥajar (`asma/0852…TakhrijAhadithAsmaHusna` p00143, p. 12): the defect is "the
  possibility that the list was inserted (*mudraj*) by one of the narrators."
- **So:** the number is prophetic; the familiar list is very likely an early scholarly compilation. Several listed
  names do not occur in the Qur'an in that form (*al-Qābiḍ*, *al-Mudhill*, *al-Ḍārr*: see names.tsv), and Qur'anic
  names such as *al-Rabb* are absent from it.

## 3. What Adam was taught (2:31): three readings
| Reading | Source | Status |
|---|---|---|
| The name of every thing, down to the humblest household objects | Ibn ʿAbbās in al-Ṭabarī I:514 (`p01741`, `p01742`) | typed |
| The names of all his descendants | Ibn Zayd in al-Ṭabarī I:517 (`p01751`) | typed |
| The names of his offspring and of the angels, since "He presented *them*" uses the pronoun for rational beings | al-Ṭabarī's own preference, I:517 (`p01751`) | typed |

## 4. Why Adam: the names seek a mirror
- **Ibn ʿArabī, Fuṣūṣ ch. 1:** God willed, "through His Most Beautiful Names," to see their realities, His own
  reality, "in a comprehensive being (*kawn jāmiʿ*) that gathers the whole matter." Al-Qāshānī's commentary
  names it the Perfect Man, with the world alongside him (`nur/0736…Qashani.SharhFusus` leaf 12; clean OCR, not independently corroborated: see v34 note below).
  Adam is taught all the names because he is where they are all reflected together; the angels each hold some.
- **Futūḥāt ch. 558**, "on knowing the Most Beautiful Names": one *ḥaḍra* (presence) per name
  (`ibnarabi/futuhat.arabiyya` r02226–r02360; Cairo ed. IV:196–326).
- **al-Qayṣarī, Muqaddima ch. 2–3** on the names and the fixed entities (`nur/0751…Qaysari.SharhFusus`; OCR, no
  witness; check against Mukhtar Ali's edition).

## 5. How the names join Creator and creation
- **al-Ghazālī** (`asma/0505Ghazali.MaqsadAsna` p00080, p. 44): "the servant's perfection and happiness lie in
  taking on the character of God's traits and adorning himself with the meanings of His attributes and names,
  as far as is conceivable for him." Each name in the *Maqṣad* ends with the servant's share in it.
- **Ibn ʿArabī, Kashf al-maʿnā** (`asma/0638IbnCarabi.KashfMacna` leaf 53; OCR, no witness; check against
  Beneito 2024): three relations with every name: *taʿalluq* (dependence, as it points to the Essence),
  *taḥaqquq* (knowing its meaning as it applies to Him and to you), *takhalluq* (standing in it "as befits you, as
  it is ascribed to Him as befits Him"). Every name can be taken on as a trait except *Allāh*: dependence only.
- **Formula:** each name is His in reality, the world's as an effect, and the human's as a trait.

## 6. How we address Him
- **al-Qushayrī, Laṭāʾif al-ishārāt** III:261 (`tafsir_sufi/…LataifIsharat` p00294): Adam was told "tell the angels
  what I taught you"; we are told, in effect, "converse with Me, My servant, with what I taught you." Prayer is
  *munājāt* (intimate converse).
- **7:180** closes the circle: "To God belong the Most Beautiful Names, so call upon Him by them."
- Manuals in `corpus/asma`: al-Nawawī's *Adhkār* (the ḥadīth for each formula), Ibn ʿAṭāʾ Allāh's *Ḥikam* and
  *munājāt*, al-Jazūlī's *Dalāʾil al-khayrāt*, Ibn al-Qayyim's *al-Wābil al-ṣayyib*, al-Jīlānī's *Ghunya*
  ("call upon Him by the names He may be described by"; he refers back to the 99).

## 7. The other voices
- **The grammarians** (al-Zajjāj, al-Zajjājī, al-Khaṭṭābī): what each name means and how it is derived; al-Zajjājī
  treats *al-Nūr* from 24:35 (`asma/0337…IshtiqaqAsmaAllah` p01338); al-Bayhaqī likewise (`p00712`).
- **Ibn Taymiyya** names them 92 times in *Majmūʿ al-fatāwā* (`--concept asma_husna --work critics`):
  read there for his limits on what may be said of the names; not yet summarised here.
- Ṭabarī answers *what* was taught (language, report); the Sufis answer *why* (the structure of being). Different
  claims, not rival answers to one question.

## 8. Confidence and gaps
- Typed: al-Ṭabarī, al-Qushayrī, al-Ghazālī, al-Tirmidhī, Ibn Ḥajar, the Futūḥāt (Shamela text).
- OCR: *Kashf al-maʿnā* (no witness), al-Qayṣarī (no witness), al-Qāshānī (no page corroborated since v34: its
  earlier "corroborated" rested on a copy of the same OCR; the one independent witness is another edition),
  al-Qurṭubī's *Asnā*, al-Rāzī's *Lawāmiʿ*: see `reports/collation/confidence.tsv.gz`.
- Missing: al-Qushayrī's *al-Taḥbīr fī ʿilm al-tadhkīr* (his commentary on the names), Ibn ʿArabī's *Awrād al-usbūʿ*.
- References: `beneito2024_secret_names` (Arabic of the Kashf), `kazi2018_unveiling_names`, `ali2020_horizons`.

## 9. Open questions for the next sessions
1. The Greatest Name (*al-ism al-aʿẓam*): 257 passages (`--concept ism_azam`); Bursevi, al-Munāwī, al-Qayṣarī, al-Rāzī.
2. Ibn Taymiyya on the names (section 7).
3. The "presences" of Futūḥāt ch. 558 name by name, against al-Ghazālī's servant's share.
4. How the names relate to the Muhammadan Reality (nūr dossier, to come).
