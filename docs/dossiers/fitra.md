# Dossier: the fitra (primordial nature)

> **A map, not an answer.** This dossier says where the library's evidence is. Before answering a study question, query the repo itself (see `START_HERE.md`): run the verse or concept lookup, open the cited records, and search the hadith layer and the grading works. Cite from the files, not from this page.

*What "every child is born on the fitra" and Q30:30 mean, what the fitra knows, and whether it can be lost.*
Repo state: v42 (pages corrected). Earlier findings: `sijill/views/inferences.md` (topic:fitra).

## 1. Start here
```
python3 pipeline/index/lookup.py --repo . --verse 30:30        # 457 passages in 40 works
python3 pipeline/index/lookup.py --repo . --concept fitra      # 2,513 passages in 167 works
python3 pipeline/search/textsearch.py "كل مولود يولد على الفطرة" "لا تبديل" "عالم الذر" --folder fitra,tafsir --count
```
Also 7:172 (the covenant), 16:78 ("knowing nothing"), 91:8, 20:50.

## 2. The three fitra works (corpus/fitra, all typed)
| Work | Where | What |
|---|---|---|
| Ibn ʿAbd al-Barr (d. 463), al-Tamhid | `…TamhidMuwatta.JK000585-ara1:p01516`, vol. 18 pp. 57-97 (one record; exact pages via cite.py: "soundness and uprightness" 18:70, "observation and reason belie" 18:88) | survey of every reading; "soundness and uprightness" is the most correct; inborn knowledge is "what observation and reason belie"; yet the pull toward a Creator once reason matures is "the consensus of Ahl al-Sunna" |
| Ibn Taymiyya (d. 728), Darʾ taʿarud | `…DarTacarud.JK000362-ara1:p09798`, vol. 8 p. 384 | the fitra contains acknowledging and loving the Creator, like a newborn's desire for suitable milk; not knowledge of the religion at birth; messengers complete it |
| Ibn al-Qayyim (d. 751), Shifaʾ al-ʿalil | `…ShifaCalil.JK000100-ara1:p00527` (1:295), `p00448` (1:253-254), `p00516` (1:287) | lā tabdīl: no one but God could replace it and He does not; ʿUmar and Muʿadh: sincerity is the fitra |

## 3. Companions and Followers
- Abu Hurayra recites 30:30 after the hadith: al-Bukhari, Fath al-Bari 1358 (`urn:hadith:0256Bukhari.Sahih:1292`).
- Muʿadh to ʿUmar, "sincerity is the fitra": al-Tabari 18:493 (`…JamicBayan.Shamela0007798-ara1:p56462`).
- ʿIkrima, fitra = God's religion (`p56472`); Mujahid, "no changing God's creation" = His religion, read as a command (`p56470`).

## 4. Where the debate is
- **What the fitra knows:** capacity and leaning (Ibn ʿAbd al-Barr, Ibn Taymiyya, al-Ghazali) versus inborn faith
  (Ibn ʿArabi). Q16:78, 42:52.
- **Lā tabdīl:** a statement that it cannot be replaced (Ibn al-Qayyim) or a command not to change God's religion
  (al-Tabari, Mujahid, ʿIkrima, Qatada).
- **The covenant (7:172) and the "loins of Adam":** Ishaq b. Rahawayh, Hammad b. Salama; discussed and limited by
  Ibn ʿAbd al-Barr and Ibn Taymiyya.
- **Grades of remembrance:** Rumi, Fihi ma fihi ch. 14; al-Ghazali (Ihyaʾ).

## 5. Gaps
- Exact pages anywhere: `pipeline/search/cite.py <record_id> "<phrase>"` (v42).
- Record ids still to look up: al-Ghazali's Ihyaʾ passages, the Futuhat pages, Fihi ma fihi ch. 14 (see the sijill's open questions).
