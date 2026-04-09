# Goal Authoring Guide

## 1. Overview

A **goal** is a Markdown file that declares a desired outcome, a list of council
members (each identified by a persona file and an authority tier), and a corpus
scope. Goals let you assemble a reusable, named configuration for a particular
deliberation context without embedding council composition in every query.

Goals are processed offline into `goals_manifest.json` and referenced at runtime
by name via the CLI or HTTP API.

---

## 2. File Format

A goal file is a `.md` file with YAML front matter. The front matter block is
delimited by `---` lines and must appear at the very top of the file.

### Required front-matter fields

| Field | Type | Description |
|---|---|---|
| `desired_outcome` | string | Human-readable description of what this goal is trying to accomplish. |
| `corpus_path` | string | Path (relative to the project root) of the corpus directory to search. |
| `council` | list | Ordered list of council member references (see below). |

### Council member reference fields

| Field | Type | Description |
|---|---|---|
| `persona_file` | string | Filename of the persona Markdown file, relative to `personas_dir`. |
| `authority_tier` | integer | Deliberation authority (1 = highest). |

### Worked schema example

```
---
desired_outcome: "A human-readable description of what this goal is trying to accomplish."
corpus_path: "corpus"
council:
  - persona_file: "filename.md"   # relative to personas_dir
    authority_tier: 1              # 1 = highest authority (synthesizer)
  - persona_file: "other.md"
    authority_tier: 2
---
Optional body text with additional context.
```

The body text (after the closing `---`) is passed to the council as supplemental
context. It is optional.

**The file extension must be `.md`.** Files with other extensions are ignored by
`goals process`.

---

## 3. Authority Tiers

The `authority_tier` integer controls the order in which council members
contribute during deliberation.

- **Tier 1** is the highest authority. In multi-tier deliberations the tier-1
  member speaks last (or synthesizes), so their framing takes precedence.
- **Tier 2, 3, …** contribute earlier in the deliberation chain.
- Lower numerical tier = higher authority. Members with the same tier value
  deliberate at equal standing.

Assign tier 1 to the persona whose judgment should carry the most weight in the
final synthesis. Assign higher-numbered tiers to personas that provide
supporting analysis or alternative viewpoints.

---

## 4. Corpus Path

`corpus_path` names the directory (relative to the project root) that contains
the documents to be searched for this goal.

```
corpus_path: "corpus"
```

The `corpus` directory is the default. You may point different goals at
different sub-directories if your project organizes documents by topic or
audience.

The path must be a relative path. Absolute paths and traversal sequences
(`../`) are not supported.

---

## 5. Processing Goals

Before a goal can be used at runtime, it must be processed into the manifest:

```
corpus-council goals process
```

This command:

1. Reads every `.md` file in the configured `goals_dir` (default: `goals/`).
2. Validates each file's YAML front matter and all `persona_file` references.
3. Writes `goals_manifest.json` with all validated goals sorted by name.

**Idempotency guarantee:** Running `goals process` twice on the same input
produces byte-for-byte identical output. The manifest is written via an atomic
rename (`.tmp` → final path), so a partial write never leaves a corrupt file.

Re-run `goals process` whenever you add, modify, or delete a goal file. The
command exits non-zero if any goal file fails validation, and the previous
manifest is left intact.

---

## 6. Using a Goal at Runtime

### CLI — `--goal` flag

Pass the goal name (the stem of the `.md` filename, without extension) to
`corpus-council query`:

```
corpus-council query --goal intake "What are my main barriers to change?"
```

The named goal is loaded from `goals_manifest.json`. Its `desired_outcome`,
`corpus_path`, and `council` replace the defaults for that query.

### HTTP API — `POST /query`

Include a `"goal"` field in the JSON request body:

```json
{
  "message": "What are my main barriers to change?",
  "goal": "intake"
}
```

The `"goal"` field accepts the same goal name string as the `--goal` CLI flag.
When `"goal"` is provided, the `desired_outcome`, `corpus_path`, and council
composition are sourced from the manifest entry for that name. All other
`POST /query` fields (e.g. `"mode"`) remain available.

---

## 7. Path Safety

`persona_file` values are validated at **`goals process` time** — before any
goal can reach the query path.

The validation rules are:

- The path must be a relative filename (e.g. `coach.md`), not an absolute path.
- After joining with `personas_dir`, the resolved path must remain inside
  `personas_dir`. Any traversal attempt (e.g. `../secrets.md`) raises an error
  and aborts processing.
- The resolved file must exist on disk.

Goals that fail path validation are rejected with a descriptive error message
and the manifest is not updated. This means a traversal payload cannot be
stored in the manifest and cannot be loaded at runtime.

---

## 8. Example

The file `goals/intake.md` is a complete, working goal shipped with the
project:

```
---
desired_outcome: "Conduct a structured customer intake interview to systematically
  gather user data including goals, current behaviours, perceived barriers,
  available resources, and motivational drivers that will inform a personalised
  COM-B behaviour-change plan."
corpus_path: "corpus"
council:
  - persona_file: "coach.md"
    authority_tier: 1
  - persona_file: "analyst.md"
    authority_tier: 2
---
The council convenes to conduct a warm yet thorough intake interview with the
customer. The coach leads with empathy, drawing out the customer's aspirations
and lived experience, while the analyst listens for patterns, gaps, and data
points that will anchor the eventual behaviour-change plan. Together they ensure
the session captures a complete picture of what the customer wants to achieve,
what is currently helping or hindering them, and what support structures are
already in place—producing a rich evidence base for the planning phase that
follows.
```

To process and use this goal:

```
corpus-council goals process
corpus-council query --goal intake "Tell me about yourself."
```
