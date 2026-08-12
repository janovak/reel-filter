# Domain language

The words this codebase uses for its own concepts. Add a term here when you name a
module after a concept that is not yet in this list.

## Movie

One film or TV movie. Identified by `omdb_id`. Before OMDb enrichment, `omdb_id` holds a
placeholder of the form `kim-{title}-{year}`, which is how the pipeline finds the rows
that still need metadata. Model: `backend/src/models/movie.py`.

## Content Score

The three 0–10 measures Kids-in-Mind publishes for a Movie: **sex/nudity**,
**violence/gore**, **language/profanity**. One Content Score per Movie.
Model: `backend/src/models/content_score.py`.

The 0–10 range is divided into six **tiers** — None (0), Mild (1–2), Moderate (3–4),
Strong (5–6), Intense (7–8), Extreme (9–10). The tiers are published in `README.md` and
currently re-typed in four places that disagree with each other; see review candidate 3.

## Filter Set

The complete set of criteria one search runs under: title text, genres, year range, MPAA
Ratings, minimum quality ratings, minimum awards, and the three Content Score thresholds,
plus pagination.

A member of a Filter Set is **active** when the user has set it, and **empty** otherwise.
The empty value differs by member (`0` for the quality ratings, `null` for a Content
Threshold, `[]`/`undefined` elsewhere) — `frontend/src/domain/filterSet.ts` is the one
place that rule lives; nothing else re-derives it.

A **Content Threshold** is one of the three Content Score members of a Filter Set. They
behave as a group: when any one is active, Movies with no Content Score drop out of the
results entirely.

## MPAA Rating

The certificate a Movie carries. The allowed set is twelve values — six MPAA
(`G`, `PG`, `PG-13`, `R`, `NC-17`, `Not Rated`) and six TV Parental Guidelines
(`TV-Y`, `TV-Y7`, `TV-G`, `TV-PG`, `TV-14`, `TV-MA`), because Kids-in-Mind covers TV
movies and specials as well as theatrical releases. The two families stay distinct;
`TV-PG` is not folded into `PG`.

The twelve values are currently typed out in four places; see review candidate 4.

## KIM Entry

One line parsed from a Kids-in-Mind A–Z index page, in the form
`Title [Year] [Rating] - Sex.Violence.Language`. The crawl reads all 26 index pages and
never visits a detail page. A KIM Entry becomes a Movie plus a Content Score.

## Enrichment

The second pipeline stage: for each Movie that still carries a `kim-` placeholder, look it
up in OMDb by title and year and fill in the metadata. Quota-metered — OMDb's free tier
allows 1,000 requests a day, so a large backlog clears over several days.

## Refresh Log

One row per pipeline run, recording counts and outcome. `/api/health` reads the most
recent one to report `last_refresh`. Model: `backend/src/models/data_refresh_log.py`.
