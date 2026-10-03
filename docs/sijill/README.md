# The sijill: the record of the digital Jalasa (v41)

Each study tests claims against the Qur'an, the Sunna, the Companions and the masters, with every text open at once.
No gathering of scholars could hold that many voices in one sitting. The sijill keeps what those studies conclude,
so the deliberation grows instead of living only in a chat.

## Design: a growing web of entries
- **Everything is an entry**, one JSON object per line in `sijill/entries/*.jsonl`:
  `id` (type:slug), `type`, `schema` (1), `date`, `status` (draft | reviewed | superseded), `title`, `text`,
  `data` {...}, `links` [{rel, to, note}], `cites` [{record, loc, quote, level}], `by`.
- **Open registries.** `sijill/registry/types.tsv` and `relations.tsv` list the kinds of entry and link. A new kind
  (a madhhab ruling, a manuscript variant, "consensus claimed by") is one new row; nothing recorded changes.
- **Past, present, future.** Voices carry their death year (AH; the Qur'an is 0; the living are null). Source events
  carry their date. Open questions record what would settle them. So a question can be followed from the Companions to
  a present-day lecture and on to what is unresolved.
- **Nothing is overwritten.** A correction is a new entry linking `supersedes` to the old one; history is kept, an
  isnad for each finding.
- **Strict only where it matters.** The validator requires unique ids, registered types and relations, links to
  existing entries, and that every cited record id resolves in the library (corpus, hadith layer, Qur'an).
  Citations without an id yet (`loc` only) are allowed and flagged by an open question.
- **Views are generated, never edited:** `sijill/views/inferences.md` (each inference, its verdict, and the voices'
  positions oldest first), `voices.md` (for each pair of voices: agree / partly / differ, with counts),
  `open_questions.md`.
- **A synthesis layer, never mixed with the sources.** Entries start as `draft`; Housam marks them `reviewed`.
  A finding points to the masters; it never replaces them.

## Adding a study
1. The study chat ends with a findings block (JSON lines in the format above).
2. Save it as `sijill/entries/<date>-<topic>.jsonl` in a library update.
3. The workflow runs `python3 pipeline/sijill/sijill.py --repo . all`: validation, then the views.
Reuse existing ids: a voice is entered once (`voice:ibn-taymiyya`), and new positions link to it.

## Seed (v41)
The two studies of the fitra lecture (2026-10-01): 16 voices from the Qur'an to a present-day scholar, 5 inferences,
17 positions, 5 verdicts, 3 open questions; 13 cited records, all resolving.

## v53
- Two more cases recorded: the forty divine sayings (133 entries) and the ether and the Malakut (99 entries). The ether case links to three sayings already in the sijill instead of entering them again.
- An entry that links `{rel: answers}` to an open question closes it: the open-questions view lists it under "Answered". Used for the speaker of the heart lecture, confirmed by Housam (`voice:housam`).
- A new standing, `strange` (gharib): a single chain with no grade found. It is not a grade of weakness.
