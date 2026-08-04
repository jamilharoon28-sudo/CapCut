# Risk Register

| Risk | Likelihood | Impact | Mitigation / gate | Trigger response |
|---|---|---:|---|---|
| CapCut update changes schema | High | Critical | Exact-version compatibility registry; canary; direct writes off after update | Drop to handoff/read-only and re-run Phase 0 |
| Generated CapCut project appears corrupt | Medium | Critical | Duplicate-only, atomic writes, lint, ten-run canary, backup/restore | Close CapCut, restore/remove duplicate, disable adapter |
| Tool modifies original project | Low if rules followed | Critical | Original immutability checks and Coach-only naming/ids | Halt release; investigate and add regression test |
| CapCut open during mutation | Medium | Critical | PID/process guard and exclusive lock | Queue/refuse until closed |
| CapCut has no official write API | Certain | High | Permanent safe handoff; unofficial adapter explicitly version-gated | Never describe handoff as direct automation |
| Premium resource ids change or expire | Medium | High | Clone known-good template; harvest only from app-authored drafts; validate | Omit affected element and guide user manually |
| UI automation clicks wrong control | Medium | High | AXUIElement-first, version map, unexpected-dialog pause, emergency stop | Halt; require manual step; disable script version |
| Imported SRT behaves differently from auto captions | Medium | Medium | Guidance branch and test segment; knowledge map | Re-apply style manually or use template caption track |
| Style dataset contains inconsistent/poor edits | High | High | Quality labels, robust weights, conflict display, held-out set | Exclude/downweight and ask user to approve profile |
| Raw footage is incomplete | Medium | High | Dataset validation and unmatched reporting | Do not treat inference as full editor behaviour |
| Raw/final alignment matches wrong repeated take | Medium | High | Audio+transcript+visual verification and sequence constraints | Flag low confidence and require correction |
| Claude invents footage/UI/actions | Medium | High | JSON Schema, supplied ids only, knowledge step ids, validator | Reject response; one repair; deterministic fallback |
| Claude unavailable/limit reached | Medium | Medium | Local deterministic pipeline and cache | Continue local stages; pause semantic features |
| Surprise paid Claude usage | Low | High | Paid overage off; hard limit; usage status | Stop calls and notify user |
| Continuous screenshots consume allowance/privacy | Medium | High | Screenshot only on explicit **I'm stuck**; local OCR first | Disable screen help and delete captured temp data |
| M2 becomes hot/slow | Medium | Medium | One heavy job, proxies, low priority, pause with CapCut/battery | Pause/throttle and resume later |
| Disk fills with proxies/backups | High | High | Free-space gate, content cache budget, safe cleanup categories | Pause before write; show cleanup choices |
| Local cleanup synchronises a cloud deletion | Low if boundaries enforced | Critical | Cloud mounts ineligible; Drive/CapCut adapters read-only; staging separated | Halt cleanup, disable source moves, verify remote state |
| Large Drive download is interrupted/corrupt | Medium | Medium | Chunked staging, partial journal, expected size/hash, retry/backoff | Resume or restart staging; never analyse unverified bytes |
| Google/Claude policy creates unexpected charge | Medium | High | Current-policy links, usage meter, $0 overage default, no billing fallback | Stop remote calls and continue local pipeline |
| Variable frame rate causes sync drift | Medium | High | Detect VFR; normalise proxy/timeline carefully | Warn and transcode analysis/working copy |
| Audio cuts click or clip words | Medium | Medium | Phoneme/breath margins, crossfades, boundary tests | Mark cut for review/restore context |
| B-roll uses media without rights | Medium | High | Owned local library only; provenance | Placeholder and user selection, never web-download automatically |
| Client-sensitive data leaves Mac | Low | High | Local processing; minimal Claude payload; explicit screen permission | Disable call and show payload preview where relevant |
| Third-party dependency license unclear | Medium | High | License gate and notices | Do not vendor/use until resolved |
| Upstream repository abandoned | Medium | Medium | Small adapter boundaries, pinned revisions, fixtures | Fork only with compatible license or replace component |
| Application binds to network | Low | High | Loopback test and local auth | Block release |
| User is overwhelmed by controls | Medium | High | Four primary actions, Advanced hidden, one instruction at a time | Usability test and simplify |
| Automation harms learning | Medium | Medium | Learn Mode and explanation of decisions | Encourage guided practice and progressively reduce help |
| User assumes performance guarantee | Medium | Medium | No viral/publish-ready claims; evidence-based time study | Display limitations and approval requirement |
| Final export matched to wrong project | Medium | Medium | Multi-signal match and ambiguity prompt | Ask user; never auto-learn from ambiguous export |
| Incorrect Style DNA update | Medium | High | Candidate version, diff, explicit approval and rollback | Roll back immediately |
| Model/tool update changes outputs | High | Medium | Pin versions; fingerprints; golden regression corpus | Re-evaluate before promotion |
| Local database corruption | Low | High | WAL, migrations, backups, integrity checks | Restore latest valid backup and rebuild caches |

## Release-blocking risks

The following must be resolved or the related feature disabled:

- project corruption;
- original-project mutation;
- unsupported CapCut direct writes;
- path escape/arbitrary command execution;
- network exposure;
- surprise paid usage;
- unreviewed destructive UI automation;
- unclear license for copied/vendored code.

## Acceptable deferred risks

The product may ship with clear limitations for:

- imperfect editorial recommendations;
- incomplete B-roll matching;
- no direct write on an unsupported CapCut version;
- manual Premium steps where Accessibility mapping is unstable;
- longer processing on low-memory M2 configurations.

Safe fallback is an intentional product feature, not a failed implementation.
