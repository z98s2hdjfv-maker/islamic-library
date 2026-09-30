# Best readings for the OCR texts (v33)

`pipeline/verify/best_reading.py` builds, for every OCR page that has an independent witness, a reading
corrected word by word from the witnesses that `collate.py` aligns. The corpus is never edited: readings
live in `apparatus/best_reading/<work>.jsonl.gz`, and every change records its rule and its witnesses.
The rules (join, majority, lexicon, insert) and the safeguards are in the script's header. In short: a
word changes only when independent witnesses outvote it, or when it is not a word at all and a witness
offers a similar attested one. Nothing is deleted, and numbers, sigla and brackets stay where they are.

## How well it works (tested 2026-09-30, leave-one-out)
Each change was checked against a witness the builder had not seen:
| rule | confirmed | contradicted |
|---|---|---|
| majority (Kibrit, Lataif) | 95-99% | about 1-5% |
| lexicon (Kibrit, Lataif, Fusus, Shifa) | 97-100% | 0-3% |
| join | 90-100% | small counts |
| insert | 14 of 14 | 0 |
On the Futuhat, agreement with an independent typed edition rose from 0.70 to 0.76 (552 of 600 pages better).
"Confirmed" means another edition reads the same, so a residual share may be edition variants, not errors.

## Safeguards found in testing
- **Dependent witnesses** (reports/best_reading/witness_independence.tsv): a witness that reproduces 40%
  or more of the OCR's non-words is the same printing read by the same engine, so it is set aside:
  qashani_9979 (83%), kamalat_b (50%), ishraq_b (45%). **The collation levels in
  reports/collation/confidence.tsv rest partly on these, so "corroborated" is overstated for al-Qashani's
  Sharh al-Fusus, al-Jili's Kamalat and Suhrawardi's Hikmat al-ishraq.**
- **Witness families:** futuhat_shamela and futuhat_jk agree at 0.96, so they are one Bulaq-derived text and
  count as one vote. Without this, the Bulaq text would have outvoted 264,000 of Mansub's readings; with it,
  the Futuhat gets only OCR non-word fixes (121,532).
- **Persian (Aflaki):** the lexicon cannot judge Persian prose, so only majority applies; Aflaki has one
  witness, so it gets no changes.

## Using it
- Cite the page by its corpus uid and locator; say "best reading" when quoting a reading, and check the listed
  change (`changes`: at, ocr, reading, rule, by) when a word matters. `open` lists unresolved alternatives.
- Rebuild: `python3 pipeline/verify/best_reading.py --repo .` (about 6 minutes; the lexicon takes most of it).
