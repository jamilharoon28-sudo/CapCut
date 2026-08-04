# Autonomy Policy and Human Gates

## 1. Goal

Maximise useful automation while keeping the owner in control of facts, publishing and destructive local actions.

## 2. Actions Coach performs automatically

- inspect selected folders and script packs;
- safely extract/parse documents;
- inventory, hash, deduplicate and proxy footage;
- transcribe and label footage locally;
- separate campaigns/reels/shots;
- match script beats to candidate footage;
- detect weak/duplicate clips;
- plan Clean/Enhanced/Bold edits;
- create text, captions, graphics, reframing and transitions;
- render previews and final candidates;
- run technical/editorial QC;
- create learning capsules and preference-update candidates;
- remove recomputable Coach staging/caches under the configured automatic cache budget.

## 3. Actions needing lightweight confirmation

- choose between genuinely ambiguous people/services/shots;
- approve a factual script rewrite or material claim change;
- select a candidate when Autopilot is not unlocked;
- accept a major Style DNA update;
- allow Accessibility assistance for the current CapCut step.

Questions use plain language, thumbnails and recommended defaults. Unanswered non-safety questions may use the conservative option if the owner enabled this behaviour.

## 4. Actions always requiring explicit confirmation

- final creative approval;
- publishing/uploading/sending anywhere;
- modifying any CapCut project through an unofficial adapter;
- moving eligible standalone local raw footage to Trash;
- enabling paid Claude/API overage;
- granting a new folder/account/Accessibility permission;
- changing cloud permissions or data—these are not implemented in v1.

## 5. Permanently prohibited

- delete/move/update CapCut Cloud, account or Team Space content;
- delete/move/update Google Drive or any mounted/synchronised cloud source;
- empty Trash or permanently delete originals;
- bypass CapCut compatibility/write guards;
- publish without final owner approval;
- invent footage, testimonials, results, prices or treatment claims;
- download unlicensed music/stock media;
- execute model-generated shell commands or paths;
- enable paid overage silently.
- require or initiate any new payment, subscription or paid licence.

## 6. Autopilot state machine

```text
OFF
  -> ELIGIBLE_AFTER_5_SAFE_JOBS
  -> OWNER_ENABLED
  -> ACTIVE_FOR_SELECTED_FORMATS
  -> PAUSED_ON_UNCERTAINTY_OR_UPDATE
```

Autopilot is format-scoped. Success on treatment montages does not automatically enable it for interviews or advertisements.

## 7. Uncertainty budget

Each project has a default maximum of one interruption before first preview. Accumulate other low-risk uncertainties and show them together after the render. Safety/factual ambiguities interrupt immediately.

If confidence is below threshold and no safe default exists, leave a labelled placeholder or ask rather than guessing.

## 8. Audit and reversibility

Every automated decision stores:

- input ids/features;
- selected alternative and rejected candidates;
- reason/confidence;
- playbook, Style DNA and prompt versions;
- whether it was deterministic or Claude-assisted;
- owner modification/approval outcome.

The owner can undo to the last approved graph and restore any removed shot/range while source media remains available.

## 9. Automation success measures

- active owner minutes saved;
- interruptions before first preview;
- percent of proposal retained;
- number of factual/safety corrections;
- number of low-value effects removed;
- time from input selection to reviewable preview;
- successful no-CapCut final exports;
- safe local-space reclaimed;
- zero cloud mutations and surprise charges.
