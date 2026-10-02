# v48: fixes from the audit of v47

The audit of v47 (2026-10-02) found one bug and several weak labels. v48 corrects them and rebuilds the v47 tables
with the same script (`pipeline/hadith/build_grades_v47.py`). No verdict text, join or source changed: only labels,
one header, the start of some remarks, and duplicate rows.

| Problem | Fix |
|---|---|
| `weak_links.tsv.gz`: the header had one column too many, so the Taqrib record sat under `has_classical_grade` and `taqrib_record` was empty | Header corrected. The table lists only hadith with no classical grade, so that column is gone. Every row now has its `taqrib_record`. |
| A strengthening verdict followed by a reservation was filed as sound or fair ("إسناده صحيح لكن قوى أبو حاتم إرساله", "رجاله ثقات ... والمرسل أشبه") | Filed as `disputed`. 69 rows changed. |
| "رواه فلان بإسناد حسن" was filed as sound when a later clause reported another route as sound | The grade stated for the chain in hand decides: 38 rows changed from sound to fair. |
| A narrator called "مختلف في توثيقه" was not caught | Filed as `disputed_narrator`. 8 rows changed. |
| "وقال الترمذي: حسن صحيح" was given scope = chain | Scope = hadith. 260 rows changed scope. |
| al-Daraqutni's and al-Bayhaqi's unmarked remarks began a few words early, inside the hadith text | The narrator's name is now found from the hadith's own chain (see GRADE_GAP_V47.md, step 2). |
| The same verdict written twice on the same hadith | 32 duplicate rows removed from the modern tables. |

115 class labels changed in all, 111 of them towards the more cautious label. Coverage is unchanged in substance:
115,146 hadith without a classical grade (115,147 in v47).

Not changed: the one duplicate in `haythami_majma.tsv` (built by the v44 script), and the double filing of
al-Sakhawi's Maqasid source under both `sources/openiti/grading` and `sources/openiti/wilaya` (each canon keeps the
source it was built from; 0.4 MB).

## Repo tidy
The tree holds no zip files: the workflow deletes each update zip once applied. `.gitignore` now also ignores
stray archives (any `*.zip` other than a `library-update-*.zip`), editor and system files, and Python caches, so
none can be committed by accident. Nothing that is a source, or that a script reads, was removed.

`class` remains a rule-made label for filtering. **Always quote `verdict`.** Status: unverified until a scholar
samples the tables.
