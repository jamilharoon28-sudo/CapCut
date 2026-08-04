# Google Drive and Large-Media Ingestion

## 1. Non-negotiable cloud boundary

CapCut Coach is read-only toward:

- CapCut account, Cloud and Team Spaces;
- Google Drive and Shared Drives;
- any other connected cloud source.

It must never call remote delete, trash, move, rename, update, upload, permission or sharing operations. **Finish & Free Space applies only to Coach-managed local staging/caches and explicitly approved standalone local raw files.** It never removes remote media or any file inside a mounted/synchronised Google Drive folder because a local deletion may synchronise to the cloud.

## 2. Supported sources

The Create Project flow accepts three cards:

1. **Script** — `.docx`, `.pdf`, `.txt`, `.md` or safe ZIP bundle.
2. **Raw footage** — local files/folders, external SSD or selected Google Drive folder.
3. **Finished references** — approved MP4/MOV files and optional local/read-only CapCut projects.

The user may add multiple scripts, shoots and finals, then confirm or correct Coach's proposed pairings.

## 3. Recommended Google Drive connection

### Lane A — Drive for desktop stream mode (v1)

- User installs/signs into Google Drive for desktop.
- Coach opens a native folder picker and the user selects only the relevant streamed folder.
- Coach stores a macOS security-scoped bookmark for that folder.
- Source is treated as immutable/read-only.
- Files are staged into Coach's own temporary workspace only when processing requires local random access.
- Coach deletes its own staging copy after the verified capsule is created; it never deletes/dehydrates the Drive-mounted source.

This is the simplest owner experience and avoids a Google Cloud/OAuth setup. Stream mode is preferred; Mirror mode defeats the disk-saving purpose.

### Lane B — native read-only Drive connection (v1.1)

- Installed-app OAuth 2.0 with system browser and PKCE; never collect a Google password.
- Google Picker/folder browser lets the user approve specific folder ids.
- Enforce selected-folder ancestry in the application even if the granted OAuth scope is broader.
- Store refresh credentials in macOS Keychain.
- Only list/metadata/download methods are implemented; no write-capable Drive client exists in the runtime.
- Support My Drive and Shared Drives, pagination, shortcuts, changes, retry/backoff and revoked access.
- Chunk/resume large downloads into Coach staging and verify size/hash before processing.

Sources:

- https://developers.google.com/identity/protocols/oauth2/native-app
- https://developers.google.com/workspace/drive/api/guides/about-sdk

## 4. Multi-gigabyte file design

There is no artificial browser-upload size limit because local/Drive sources are registered by path or file id rather than copied through an HTML multipart request.

Requirements:

- tested with individual 2 GB, 10 GB and 50 GB media fixtures;
- incremental SHA-256 and metadata reads; never load a full file into RAM;
- chunked/resumable Drive staging with `.partial` state;
- ffprobe before transcode;
- VideoToolbox 720p analysis proxies and compact thumbnails;
- one heavy job at a time;
- pause/resume across app restarts and network loss;
- free-space gate before every download/proxy/render;
- deduplicate identical content by hash;
- process files in a bounded queue and release handles immediately;
- support external SSD staging through an owner-selected working location.

For a typical 2 GB shoot, recommend at least 15 GB free for active processing and 30 GB free during development. Show projected temporary use before starting.

## 5. Automatic separation and pairing

Coach should accept an untidy shoot folder and perform:

1. Media inventory by timestamp, duration, orientation, camera metadata and hash.
2. Script-pack parsing into campaigns, reels, shots, speech, overlays, cutaways and CTAs.
3. Scene segmentation and low-resolution visual/audio feature extraction.
4. Clip labels such as arrival, exterior, consultation, practitioner, device, treatment, close-up, result, reaction and CTA asset.
5. Candidate mapping from each requested script shot to one or more raw ranges.
6. Raw-to-finished alignment for learning examples.
7. Confidence scoring and a simple visual confirmation only for ambiguous matches.

Do not pretend certainty. A missing/ambiguous shot appears as **Needs your choice** with two or three thumbnails.

## 6. Learn without retaining the raw files

Before local cleanup, create and verify the learning capsule specified in the master spec. It preserves the script structure, hashes/metadata, alignment/edit decisions, Style DNA contribution and compact low-resolution evidence. It does not preserve enough media to reconstruct a full-resolution edit.

Cleanup categories:

- **Safe now:** Coach staging, proxies, extracted audio, thumbnails and failed renders.
- **Owner confirmation:** standalone local raw files outside any synced/cloud mount.
- **Never touched:** CapCut Cloud/account, Google Drive, synced/mounted Drive sources, original CapCut projects and unrelated local media.

## 7. Acceptance scenarios

- Select one Drive folder containing a 2 GB shoot, script ZIP and finished reference; only that subtree is indexed.
- Revoke Drive access halfway through a download; job pauses and resumes without corruption.
- Disconnect the network; already staged jobs continue and missing files show a clear wait state.
- Attempt cleanup on a Drive-mounted path; source remains untouched and only Coach staging is removed.
- Point at mixed footage for several reels; parser creates candidate groupings and asks only for low-confidence corrections.
- Delete local raw after capsule verification; Style DNA remains usable but exact full-resolution re-edit is clearly marked unavailable.
