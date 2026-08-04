# Smart Preflight — Coach Tells the Owner What It Needs

## 1. Product rule

The beginner never has to guess what to upload, how to label footage or why an edit is weak. After the owner adds whatever they currently have, Coach analyses the script, footage, audio and assets first. It then says one of:

- **Ready to create** — everything necessary is available.
- **Ready, with suggestions** — Coach can proceed; one or more optional items would improve the result.
- **I need your help with X things** — a material ambiguity or missing requirement prevents an honest/usable result.

Coach asks only for missing information it cannot derive safely. It must not present a long setup questionnaire before inspecting the sources.

## 2. Automatic preflight sequence

1. Parse the script/brief into story beats, required facts, overlay copy, CTA, shot roles, brand needs and audio notes.
2. Inventory the raw folder incrementally and build low-resolution evidence.
3. Match every required story beat to one or more usable footage ranges.
4. Inspect provided logo, font, colour, outro, music and sound-effect assets.
5. Detect speech/music/SFX, audio quality and soundtrack structure.
6. Determine target format, duration and safe default from the script and prior jobs.
7. Produce a readiness report before expensive final rendering.

## 3. What Coach may request

### Story and facts

- the intended objective when the script genuinely supports several;
- missing CTA, offer/date/location or must-include wording;
- clarification of an ambiguous or potentially misleading claim;
- confirmation before shortening or rewriting a factual statement.

### Footage

- a missing shot role such as practitioner, equipment, treatment detail, environment, product, reaction/result or CTA visual;
- which person/service belongs to the current reel when automatic grouping is ambiguous;
- a replacement when all candidates are blurred, obstructed, duplicated or too short;
- permission to continue with a crop, still-frame motion or labelled placeholder.

When footage is missing, Coach generates a plain recording request:

> **One shot would improve this:** a steady 3–5 second close-up of the product being used. Film vertically, keep the subject centred and hold still for one second before and after the action.

### Brand assets

- transparent logo;
- approved colours/fonts;
- CTA/end-card wording;
- approved outro animation.

Offer alternatives: **Upload it**, **Use a clean text logo**, **Use Coach defaults**, or **Continue without it** where honest.

### Audio

- an owned/licensed soundtrack when the script requests a music-led montage;
- permission to use an approved local royalty-cleared track;
- confirmation to create a speech-only or silent version;
- replacement for clipped/noisy speech that cannot be repaired safely.

Never download or reuse a copyrighted reference track merely because it fits.

### Delivery

- platform/aspect ratio only if it cannot be inferred;
- desired duration when the script/previous pattern gives no safe answer;
- whether captions must be burned in, supplied as SRT or both.

## 4. Request-card design

Every request card contains:

- **What is needed** in ordinary language;
- **Why it matters** in one sentence;
- a thumbnail/script quotation showing the affected moment;
- **Recommended option** first;
- one or more safe alternatives;
- the effect of proceeding without it;
- **Do this later** only when the project can continue safely.

Example:

```text
I need one ending choice

Your script says “Book now,” but I did not find a website, phone number or booking link.

[Add booking details — Recommended]
[Use “Contact us to book”]
[Finish without a call to action]
```

Avoid technical messages such as “low semantic-match confidence.” Say: **I found two possible treatment clips. Which one belongs to this video?**

## 5. Blocking versus optional

Block only for:

- unresolved person/service identity;
- missing mandatory/factual content;
- unsupported or unsafe media;
- no usable footage for a required claim/beat;
- rights/permission uncertainty;
- destructive/publishing permission;
- free-space or system-safety threshold.

Do not block for:

- missing music when a clean speech/silent edit is viable;
- missing logo when an approved text end card is viable;
- an optional cutaway/effect;
- preference uncertainty that Clean/Enhanced/Bold candidates can expose;
- a low-risk choice with an owner-approved conservative default.

## 6. Readiness model

```json
{
  "status": "READY_WITH_SUGGESTIONS",
  "required_resolved": 8,
  "required_total": 8,
  "blocking_requests": [],
  "suggestions": [
    {
      "type": "missing_logo",
      "message": "A transparent logo would make the ending match your reference style.",
      "recommended_action": "upload_logo",
      "fallback": "generated_text_end_card",
      "affected_story_beats": ["outro"]
    }
  ]
}
```

Internally store confidence, evidence ids and validation rules. Normal UI shows only the plain-language outcome.

## 7. Learning and reuse

- Remember stable owner choices such as default platform, output resolution, brand asset locations, caption preference and approved music library.
- Never ask the same resolved question on every job.
- Keep campaign-specific claims, dates, prices and CTAs scoped to that campaign.
- Expire or re-confirm time-sensitive offers.
- If a previously available asset is missing, say exactly which saved item cannot be found and offer to locate it.

## 8. Acceptance gates

- A beginner can add only a script and raw folder and receive a useful readiness result without knowing editing terminology.
- Every script beat is marked covered, optional, missing or ambiguous with evidence.
- Coach never declares **Ready** while a mandatory fact/shot is unresolved.
- Coach never blocks when a safe honest fallback exists; the fallback and quality impact are visible.
- Missing-footage guidance says exactly what to film, orientation, subject/action, framing and minimum stable duration.
- The user can resolve every request using buttons/pickers, not Terminal or manual paths.
- Re-running preflight after adding an item clears the correct request without repeating heavy completed analysis.
