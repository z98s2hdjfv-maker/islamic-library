# v17: ḥadīth links — parallels, narrators, search

Built by `pipeline/hadith/build_hadith_links.py` from the v16 layer (`apparatus/hadith/`) and Ibn Ḥajar's *Taqrīb al-Tahdhīb* (`corpus/rijal/`). Everything is derived automatically and marked `status: unverified`.

## 1. Parallels — `apparatus/hadith_links/parallels.tsv.gz`

Versions of the same ḥadīth are grouped by the wording of the matn (MinHash over 3-word shingles, kept at ≥ 0.3 overlap, grouped transitively; matns under 6 words are not grouped). A group holding both al-Bukhārī and Muslim is flagged `agreed_upon`.

First build: 13,196 groups (52,390 ḥadīth), 10,936 of them across collections, 1,004 in both al-Bukhārī and Muslim. That is roughly half the classical count of *muttafaq ʿalayh* ḥadīth: many riwāyāt in Muslim say only *bi-mithlihi* ("with the same wording") and have no matn to match.

## 2. Narrators — `apparatus/rijal/taqrib_index.tsv.gz`, `apparatus/hadith_links/chains.jsonl.gz`

- The *Taqrīb* is parsed into 8,824 entries, each with Ibn Ḥajar's grade, its rank on his 12-step scale (1 Companion … 12 liar), and his six-book sigla.
- Each isnād (the last chain after any *taḥwīl* ح) is split into names. A name is linked only when exactly one entry fits, tried in order: the conventional identifications in `catalogs/narrator_aliases.tsv` (al-Aʿmash = Sulaymān b. Mihrān, al-Zuhrī = Ibn Shihāb, …; ambiguous names like a bare *Sufyān*, *Ḥammād* or *Yaḥyā b. Saʿīd* are never linked); the start of an entry's name; a kunya or nisba; each narrowed by the six-book siglum when the ḥadīth is in one of the Six Books. Every link records how it was made (`match`).
- Coverage: 44.5% of all narrator names, 54% in the Six Books. The *Taqrīb* only covers narrators of the Six Books, so the teachers of al-Ṭabarānī, al-Ḥākim and al-Dāraquṭnī are mostly absent.
- `weakest_rank` is the lowest-ranked **linked** narrator. **It is not a grade of the ḥadīth**: it ignores unlinked narrators, breaks in the chain, hidden defects (*ʿilal*) and corroboration.

## 3. Search

The search index gains two tables, `hadith` and `hadith_units`, and `search.py` gains filters:

```
search.py "انما الاعمال بالنيات" --hadith-only
search.py --root صبر --caliph Umar
search.py "الحلال بين" --narrator "النعمان بن بشير"
search.py --root صلو --graded "حسن صحيح"
search.py --root رحم --agreed
search.py --root طهر --max-weakest-rank 4          # linked narrators all saduq or better (not a grade)
search.py --parallels urn:hadith:0256Bukhari.Sahih:1
```

Each ḥadīth hit shows its ḥadīth id, narrator, caliph, grades found in the sources, number of collections, and the weakest linked narrator.

## Known limits

- Parallels by wording only: paraphrased versions can be missed, and very common phrases can join unrelated reports.
- Narrator links are heuristic; spot checks were mostly right, but an unverified link must not be cited as Ibn Ḥajar's verdict on that person without checking the entry (`taqrib_no`).
- `narrator_aliases.tsv` was drafted by Claude from standard identifications and should be reviewed by a specialist.
