# Manuscripts catalog and the Shams concordance (v25)

## catalogs/manuscripts.tsv: an isnād for the texts
For each work, the manuscripts behind the printed edition we hold: library, shelfmark, copyist, date, what the
manuscript is to the text, the evidence, its source, and a status saying what is still to confirm. Only facts
taken from a named source are entered; nothing is inferred.

Main source: *The Islamisation of Anatolia* database (University of St Andrews, ERC grant 284076),
https://www.islam-anatolia.ac.uk/?page_id=333, which records over 7,000 medieval Anatolian manuscripts
(catalogue data only, no scans). Scans of many of those manuscripts can be read, after free registration,
at Türkiye Yazma Eserler Kurumu (yazmaeserler.gov.tr); they are handwritten, so they serve for checks by eye
of pages our reports flag, not as automatic witnesses.

First entries (Shams and Aflākī): the Konya Mevlana Museum copy of the Maqālāt (no. 2154, from a secondary
source); the oldest copy of the short version, in Sulṭān Walad's hand (Chittick after Movahhed; also the
St Andrews database); Movahhed's six oldest manuscripts in two versions; the St Andrews record for Aflākī.

## reports/concordance/chittick_movahhed.tsv
Shams's Maqālāt has no free witness, so its reference is William Chittick's *Me & Rumi* (Fons Vitae, 2004;
`chittick2004_me_and_rumi` in secondary_literature, access: owned). Chittick cites Movahhed's page for every
passage he translates. The concordance lists his 577 citations with the page of his book, the volume and
page in Movahhed, and our OCR record for it: numbers only, no text from the book (it is copyrighted and not
in the repo). Built by `pipeline/verify/build_chittick_concordance.py` from a local copy.

Tested mapping (see the script's header): cited page ≤ 597 is vol. 1 at the same page; above 597 it is vol. 2
at page − 597. Checked on two passages: (299) = vol. 1 p. 299, Shams on Ibn ʿArabī not following the Prophet;
(697-98) = vol. 2 p. 100, the Khiḍr story.

Use: to check a Shams page, open the concordance row for its record, then read Chittick's translation at the
listed page of your copy. It confirms which passage it is and its sense, not Persian wording.

## Finding recorded at v25: Shams OCR page numbers are off by one
In `corpus/shams/maqalat.movahhed_ocr.jsonl`, archive.org's `printed_page` runs one ahead of the number
printed in the page header (vol. 1 p. 299 is stored as 300; vol. 2 p. 51 as 52; p. 100 as 101).
Cite Shams by the header number, i.e. `printed_page` − 1. The corpus is left as imported.
