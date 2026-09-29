# Collation: checking OCR against independent free witnesses (v22)

The verification layer (v21, `README.md` here) records human checks. Collation adds an automatic check:
each OCR page is lined up against the same passage in other, independent copies of the work, and every
page gets a confidence level. The corpus is never edited; this only writes reports.

Principle: an OCR error is rarely repeated identically by a different scan or a different edition.
Where independent witnesses agree, the reading is corroborated, as a report gains strength from
corroborating chains (*mutābaʿāt*); where they disagree, the passage needs a human eye.

## Files
| File | Role |
|---|---|
| `catalogs/witnesses.tsv` | One row per witness: base work, witness id, kind (`corpus` file in the repo, `archive` archive.org OCR, `openiti` raw file), relation, source, pinned md5/sha256, note. |
| `sources/witnesses/<work>/<witness>/` | The downloaded witness files, byte-exact (repo witnesses are read in place). |
| `pipeline/verify/collate.py` | The collation (method in its header). |
| `reports/collation/summary.tsv` | Per work and witness: pages aligned, mean agreement, % corroborated, % divergent. |
| `reports/collation/records.tsv.gz` | Per page and witness: agreement, witness location, up to 6 differing word spans ("base → witness"). |
| `reports/collation/confidence.tsv.gz` | **The overlay**: one row per page (`record_id`) with OCR score, best agreement, best witness, verification status and level. Join your own data on `record_id`. |
| `reports/collation/confidence_summary.tsv` | Per work: pages by level. |

## Levels
`verified` (checked in `catalogs/verification_log.tsv`) · `corroborated` (agreement ≥ 0.85 with a witness) ·
`partial` (0.60–0.85: read the listed differences) · `divergent` (< 0.60: check the scan or a printed edition) ·
`unmatched` (no witness passage found) · `no_witness` (none catalogued yet).

agreement = share of the page's 4-letter sequences, spaces removed, also found in the matched witness window.
Two clean typeset copies of the same text score about 0.87–0.92: one wrong letter breaks up to four sequences,
and running heads and editors' footnotes differ between editions.

## Reading the relation column
- `same_edition_rescan`: another scan or text layer of the same printed edition. Differences are OCR errors.
- `other_edition` / `other_edition_typed`: a different edition. Differences mix OCR errors with genuine
  textual variants and different footnotes, so "divergent" there means "differs", not "wrong".

## First results (v22)
Strongest: al-Qāshānī's Fuṣūṣ commentary (345/349 pages corroborated), Suhrawardī's Ḥikmat al-ishrāq (208/242),
al-Jīlī's al-Insān al-kāmil (213/281). Weakest: the Niẓām al-Dīn Fuṣūṣ OCR (136/499 divergent) and Aflākī
(329/1236 divergent). The al-Manṣūb Futūḥāt is mostly `partial` (5847/7976) against the Bulaq-based typed
texts: expected for a different edition, and the listed differences separate misreadings from variants.
No free witness yet: al-Qayṣarī's Fuṣūṣ commentary (only unreadable lithographs), Shams's Maqālāt, the
wilāya OCR works (incl. al-Munāwī's Kawākib, 12,046 pages), al-Jīlī's Kamālāt, al-Qūnawī's Nuṣūṣ.

## Adding a witness
Add a row to `catalogs/witnesses.tsv` (for archive.org: the file base and the md5 of its
`_hocr_searchtext.txt.gz` and `_hocr_pageindex.json.gz`, from the item's metadata), then run
`python3 pipeline/verify/collate.py --repo .`. A changed source file stops the run.

## Second round of witnesses (v23)
11 more archive.org witnesses (26 in all) for 6 works that had none. Pages corroborated / total:
al-Shaʿrānī, al-Kibrīt al-aḥmar 669/785 (3 witnesses); al-Jīlī, al-Kamālāt al-ilāhiyya 459/627;
Ibn ʿAṭāʾ Allāh, Laṭāʾif al-minan 310/442 (3); al-Yāfiʿī, Rawḍ al-rayāḥīn 471/964; Ibn al-Zayyāt,
al-Tashawwuf 285/1187 (2; mostly partial, 784); al-Qūnawī, al-Nuṣūṣ 78/153.
Tried and dropped: a Kamālāt item that is a different compilation (2% of pages aligned) and a Rawḍ lithograph
whose OCR aligned on 3 pages. Searched without a usable result: al-Munāwī's al-Kawākib al-durriyya (the one
scan has no OCR text), Shams's Maqālāt, Ibn Khaldūn's Shifāʾ al-sāʾil, al-Tirmidhī's Masʾala fī waṣf al-mufarradīn,
and a typeset al-Qayṣarī Fuṣūṣ commentary (only lithographs). These need a scan with OCR, a printed copy, or
the scan itself (`ref_id = scan` in the verification log).
Found along the way, not yet in the corpus: al-Shaʿrānī's al-Yawāqīt wa-l-jawāhir (clean scans, item alcha3rani).
