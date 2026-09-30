# v16: ḥadīth layer (numbering, isnād/matn, narrator, grades)

Built by `pipeline/hadith/build_hadith_layer.py` from `corpus/hadith/` (v15). Output: `apparatus/hadith/<collection>.jsonl.gz`, one record per ḥadīth, and `catalogs/hadith_layer_summary.json`. Everything is derived automatically and marked `status: unverified`.

## Record

| field | meaning |
|---|---|
| `id` | `urn:hadith:<collection>:<number>` |
| `number`, `numbering` | the edition's own number where the text carries one (`edition`), else a running count (`sequential`) |
| `isnad`, `matn`, `split_method` | split at the editions' `*` marker, else at the first mention of the Prophet |
| `narrator` | last narrator in the isnād: normally the Companion who heard the Prophet; for reports stopping at a Companion or Successor, that authority. Heuristic; unresolved forms like أبيه ("his father") are left as written |
| `caliph` | Abu Bakr / Umar / Uthman / Ali when the narrator is named as one of them |
| `grades` | only grades found in the sources: al-Bukhārī and Muslim (ṣaḥīḥ by inclusion), Ibn Khuzayma (his own claim), and inline verdicts of al-Tirmidhī and al-Ḥākim (هذا حديث ...) |
| `comments` | the compiler's remarks after the matn (قال أبو داود، قال أبو عيسى ...) |
| `source_ids` | the corpus paragraph ids the ḥadīth was assembled from |

## Numbering by collection

- al-Bukhārī: numbering of the JK text (al-Bughā, 7,124), **not** the Fatḥ al-Bārī numbering (7,563) used on many websites. Since v37 each hadith also carries its **Fatḥ al-Bārī number** in `edition_numbers` (7,027 of 7,135, matched by text to OpenITI Shamela0001681; 139 flagged `uncertain` because al-Bukhārī repeats narrations in near-identical words). See `apparatus/hadith_numbers/` and pipeline/hadith/edition_numbers.py.
- Muslim: ʿAbd al-Bāqī numbering (1–3,033); each riwāya under a number is N.1, N.2, …; the muqaddima is `intro.k`.
- Abū Dāwūd (5,274), Ibn Māja (4,341), al-Nasāʾī al-Mujtabā (5,758): the standard edition numbers.
- Aḥmad's Musnad: numbering of the Shamela text (al-Risāla edition).
- al-Tirmidhī: sequential here; since v37 each hadith also carries the **printed Shākir / ʿAbd al-Bāqī number** in `edition_numbers` (3,829 of 3,843), read from the headings of the same text (layer 2105 = printed 2139).
- al-Dāraquṭnī: sequential here (the text carries no usable running number).
- Riyāḍ al-ṣāliḥīn, the Forty and al-Baghawī's Sharḥ al-sunna are not processed yet.

## Not included, on purpose

- Modern grades (al-Albānī, al-Arnaʾūṭ and others). They are not in these texts, and no grade is invented.
  Since v35, al-Albānī's works are in the library as a separate **modern layer** (`corpus/modern`, category
  `modern`): searchable and citable, but never merged into these grades. Later classical critics are added:
  al-Dhahabī's Talkhīṣ on the Mustadrak joins these grades (`apparatus/hadith_grades`); see docs/canons/README.md.
- al-Dhahabī's notes on al-Ḥākim (not in this edition of the Mustadrak).

## Next steps

- Link parallel versions of the same ḥadīth across collections (e.g. agreed upon by al-Bukhārī and Muslim).
- Resolve narrator names to one entry per person using `corpus/rijal/` (Tahdhīb al-Kamāl, Taqrīb) and attach Ibn Ḥajar's grade of each narrator.
- Scholar review of a sample to measure the heuristics' accuracy.
