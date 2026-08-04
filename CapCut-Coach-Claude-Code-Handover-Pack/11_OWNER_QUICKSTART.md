# Owner Quickstart — From Download to First Useful Edit

This is the only page the owner needs for the first setup. Claude Code receives the technical detail from the rest of the pack.

## Before starting

Have these ready:

- the M2 Mac with CapCut Desktop Premium installed;
- Claude Code signed in through the existing Max plan;
- at least 30 GB of free space for development, models, proxies and test media;
- optional Google Drive for desktop configured to **Stream files**, not Mirror, if footage is stored in Drive;
- one short, non-sensitive raw video for the first test;
- permission to create a disposable CapCut project;
- later, 15–20 good examples containing raw footage, its matching approved finished video and the script/recording instructions.

Do not use an important live CapCut project for the first test.

## Start Claude Code

1. Create a new folder named `CapCut-Coach` somewhere you can find easily.
2. Put this entire handover folder inside it without renaming the numbered files.
3. Open Terminal in the `CapCut-Coach` folder and start Claude Code.
4. Open `07_START_PROMPT_FOR_CLAUDE_CODE.md`, copy the large first prompt and paste it into Claude Code.
5. Let Claude Code read the handover and build the unblocked Phase 0 checks. Do not tell it to skip the safety gate to save time.

## The one manual CapCut test

Claude Code should first build the doctor and canary instructions. When it asks for a disposable project:

1. Open CapCut and create a new clearly named test project such as `COACH_CANARY_DELETE_ME`.
2. Add a 10–20 second test clip.
3. Add or generate one caption so the project contains a real caption track.
4. Save it, close the project and fully quit CapCut.
5. Give Claude Code only the disposable project's location when asked.
6. Follow its exact reopen/verify steps. Never approve a test against the only copy of a real project.

The application must remain in safe handoff mode if this canary is unsupported or fails. That still provides transcription, rough cuts, previews, SRT captions, instructions and export review.

## First useful milestone

The first version worth using does not need preference learning or direct CapCut writing. It should already:

- import protected copies of footage;
- transcribe locally;
- remove obvious silence, mistakes and repeated takes;
- render two or three rough-cut previews;
- export an edit plan and SRT;
- open the safest CapCut handoff;
- explain the remaining steps in plain language.

Use that vertical slice on test footage before asking Claude Code to build the more fragile automation.

## Add the editor style

After the first milestone works, prepare the paired examples exactly as described in `06_DATASET_AND_LEARNING_GUIDE.md`. Keep five good pairs out of the learning set so Coach can be judged on videos it has not copied from.

For each example, identify the script pack, raw footage folder and matching approved final. Script ZIPs and Word documents are supported. CapCut project files and revision notes are optional but improve what can be learned.

After Coach verifies its learning capsule, use **Finish & Free Space**. Choose **Keep learning, remove large local files** to retain the script, finished video and learned style while moving eligible standalone local raw files to macOS Trash. Google Drive/CapCut Cloud sources are never eligible. Review the exact file list and size before confirming; Coach never empties Trash.

Choose **Balanced** creativity for normal work. Coach will preserve the learned style while showing a Faithful version and an Enhanced version containing a few reversible Coach ideas. Approving or rejecting those ideas teaches it how much flair you like.

## Continue to completion

Use the three follow-up prompts at the bottom of `07_START_PROMPT_FOR_CLAUDE_CODE.md` in order:

1. continue after the CapCut canary;
2. add paired style learning;
3. add finishing, export review and packaging.

At every milestone, ask Claude Code to show the acceptance-test report. A feature is complete only when its required test passes; hardware- or data-dependent tests should be labelled blocked until the evidence exists.

## When it is ready

Claude Code should deliver a normal Mac setup flow. After installation, the owner should use four actions—**Create Edit**, **Open in CapCut**, **Show My Next Step** and **Review Export**—without opening Terminal.

Keep the handover pack with the repository. If CapCut updates, direct project writing must turn itself off until the canary is repeated for the new exact version.

Cloud rule: Coach may read from the specific Drive/CapCut project you select, but it never deletes, moves or changes anything in CapCut Cloud, Team Spaces or Google Drive. **Free local space** only removes Coach staging/caches and explicitly approved standalone local raw files.
