# Premium Beginner UX Design System

## 1. Product feeling

CapCut Coach should feel like a calm premium Mac creative tool, not a developer dashboard, AI chatbot or settings-heavy video editor. The owner is a beginner; every screen should make the next action obvious.

Design principles:

- one primary decision per screen;
- show video and outcomes before technical detail;
- plain language first, Advanced details behind disclosure;
- generous spacing, restrained motion and high-quality thumbnails;
- no terminal, JSON, model names, file paths or API vocabulary in normal mode;
- every automated decision is reversible;
- uncertainty becomes a visual choice, never a cryptic error.

## 2. Mac application shell

Deliver a normal `CapCut Coach.app` using a small native Swift/WKWebView shell around the local React application and FastAPI service. Provide a browser fallback for recovery. The shell owns native folder/file pickers, security-scoped bookmarks, Keychain, notifications, process detection and Accessibility prompts.

The normal user should launch from Applications/Dock. No Terminal after bootstrap.

## 3. Navigation

Five top-level destinations only:

- **Home**
- **Projects**
- **Learn My Style**
- **Connections**
- **Settings**

Project workflow uses a visible five-step path:

1. Sources
2. Script & Story
3. Coach Edit
4. Render Final
5. Review & Learn

## 4. Home screen

Lead card: **Create a video**.

Secondary actions:

- **Learn my style**
- **Continue a project**
- **Review my drafts**

Below: recent project cards with thumbnail, title, current step, clear status and one action. A compact storage card shows working space and a safe **Free local space** action. Never show cloud-delete wording.

## 5. Create Project experience

Three large source cards:

- **Add your script** — document/ZIP icon and detected reel count.
- **Add raw footage** — Mac, external drive or Google Drive.
- **Add a finished example** — optional accelerator; never required.

After selection, Coach shows: `11 reels found · 43 raw clips · 2 questions`. It proposes reel/shot/take grouping visually. The owner confirms only ambiguities instead of renaming files manually.

## 6. Edit review

Large video player in the centre; simple story/shot strip below; decision panel on the right.

Primary preview tabs:

- **Clean** (renamed **Faithful** once a personal profile exists)
- **Enhanced**
- **Bold**

Balanced defaults to Enhanced. Every creative addition has a small **Coach idea** badge; selecting it explains the reason and provides **Keep**, **Remove** and **Show another idea**.

Primary actions:

- **Use this edit**
- **Change opening**
- **Make it calmer/faster**
- **Render final**
- **Open in CapCut Free** (optional secondary action)

Do not expose a full professional timeline in beginner mode. Advanced can show source ids, confidence and timecodes.

## 7. CapCut guidance

One instruction card at a time:

- exact control name;
- where it is;
- why it matters;
- expected visual result;
- **Done**, **Show me**, **I'm stuck**.

Screenshots/Accessibility inspection occur only after explicit permission. Coach never claims it clicked something unless the expected state is verified.

## 8. Visual tokens

Use SF Pro/system font. Avoid novelty typefaces.

- App background: `#F6F5F2`
- Primary surface: `#FFFFFF`
- Preview canvas: `#111318`
- Primary text: `#15161A`
- Secondary text: `#676A73`
- Accent: `#6D5DFB`
- Accent hover: `#5949E8`
- Success: `#168A5B`
- Warning: `#B66A15`
- Danger: `#C84141`
- Hairline: `#E7E5E0`

Geometry:

- 8-point spacing system;
- 12 px control radius, 16 px card radius, 20 px modal radius;
- minimum 44 px interaction height;
- subtle shadows only on elevated preview/modals;
- motion 160–220 ms with reduced-motion support;
- no decorative gradients, glowing AI or excessive glassmorphism.

## 9. Copy rules

Prefer:

- **Coach is finding the strongest shots**
- **Two clips need your choice**
- **Your edit is ready to review**
- **2.4 GB of local working files can be removed**

Avoid:

- `Running embedding inference`
- `Low-confidence semantic alignment`
- `Cache eviction completed`
- `Mutation failed`

Advanced detail may contain the technical version with a Copy diagnostics action.

## 10. Polished states

Every screen must design and implement:

- empty;
- loading with real stage/progress;
- paused/waiting;
- offline;
- permission needed;
- low storage;
- success;
- recoverable failure;
- no-results/ambiguous choice.

Never use indefinite fake progress. Show the current file/stage, completed count, estimated temporary storage and whether the user can safely close the app.

## 11. Accessibility and QA

- Full keyboard navigation and visible focus.
- VoiceOver labels and logical order.
- WCAG AA contrast.
- Text remains usable at 200% scaling.
- Captions on all instructional videos.
- Never rely on colour alone.
- Playwright screenshots at 1280×800, 1440×900 and 1728×1117.
- Visual-regression approval for Home, Create, Pairing, Edit Review, CapCut Guide, Storage and error states.

## 12. UX release gate

A first-time owner can:

1. connect a specific Drive/local folder;
2. add a script ZIP and raw footage, with a finished video optional;
3. confirm automatic grouping;
4. review Clean/Enhanced/Bold edits;
5. render a final MP4 and optionally continue in CapCut Free;
6. approve the export and free only local working space;

without Terminal, external instructions or fear that cloud files will be deleted.
