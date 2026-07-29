# Project data

This directory contains durable operational state used by project workflows.
Each subsystem owns a named directory under `data/`.

- `prompt-scout/` stores historical prompt rankings, deduplication IDs, explicit
  feedback, taste evidence, scan archives, and calibration history used by the
  `prompt_calibrator` agent.

Durable records are tracked with the repository. Transactional files belong in
the subsystem's ignored `work/` directory and must not be treated as completed
history.
