# Mathnawi spec and pilot: status (2026-09-25)

Spec (living doc, v0.2): https://claude.ai/code/artifact/59ec0f9e-cdad-4549-9df3-8736e90d80c5

## Where things live
- MASTER COPY on Housam's iPad (Files app):
  - mathnawi_library_2026-09-25_v6_rebuilt.zip. The original v6 download was lost, so v6 was rebuilt by script from the same commit. All 25,637 couplets match the project TSVs, and the works counts are identical. See README_v6_rebuild.md inside the zip.
  - library_v7_addendum_2026-09-25.zip (other authors; see works/ganjoor_survey.md).
  - Six Konya image packs (konya_pages_part01-06, 546 pages).
- The rebuilt v6 does not contain the full Konya per-couplet tables, variant_sites_konya.tsv, the masnavi.net witness text or Nicholson's English column. These came from reading the images and fetching the site, so they could not be regenerated. Their summaries are kept here in the project: konya_book1_differences.tsv, book1_variants_konya_not_ganjoor.tsv, books2-6_konya_not_ganjoor.tsv, collation_pilot.tsv and pilot_hadith_check.json.
- Network: the workspace can reach masnavi.net, museum.ganjoor.net, api.ganjoor.net, i.ganjoor.net and GitHub (git clone of ganjoor-data works). Konya page p0336 is damaged in Ganjoor's scan.

## Done
- All six books are numbered by Nicholson (aligned with masnavi.net; totals 4003/3810/4810/3855/4238/4916). Ganjoor-only couplets carry suffixes and the status interpolation_candidate; transposed couplets are marked.
- Book One: full couplet-by-couplet Konya check (4,013 couplets) and the three-witness decision at 588 variants (Konya: Ganjoor 302, Nicholson 47, neither 8).
- Books 2-6: Konya checked at all 1,211 places where the editions differ (Konya: Ganjoor 459, Nicholson 129, neither 9, spelling only 573).
- Konya colophon read: Muhammad b. Abdallah al-Qunawi al-Mawlawi, Monday, Rajab 677 AH.
- Pilot: hadith checked; frame and speaker maps for §§42-96.
- v6: Rumi's other works on Ganjoor, Baha Walad's Ma'arif (Part One) and Sultan Walad's Waladnama.
- v7 addendum: al-Ghazali's Kimiya, the Divan attributed to al-Jilani (doubtful), Maybudi's Kashf al-asrar, the Persian Ibn 'Arabi school, Sana'i and 'Attar, each with an attribution flag.

## Outstanding
- Optional: regenerate the full Konya and masnavi.net tables for the master copy. This means re-reading the images or re-fetching masnavi.net.
- Not on Ganjoor: Rumi's Maktubat; Shams's Maqalat; Aflaki; Sipahsalar; Burhan al-Din; the rest of Baha Walad's Ma'arif. Arabic corpora for Ibn 'Arabi, al-Jilani and al-Ghazali need other sources.
- Scholar review: the attribution flags in v7 and the model-read Konya readings (55 + 166 rows).
- Verify that the Divan numbering is Furuzanfar's.
- Hadith citation gaps: the Muslim number (§43), al-Albani's Silsila number (§76) and the Nahj al-Balagha number (§70).
- Annotation layers beyond §§42-96.
