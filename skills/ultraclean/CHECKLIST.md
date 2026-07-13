# Ultraclean — Decay & Slop Checklist

Every finding follows the **Iron Law**: `Symptom → Source → Consequence → Remedy`.
A finding without a consequence and a remedy is noise, not a finding.

## brooks-review — 6 decay risks (diagnosis lens), split by who owns them

The disjoint-partition design means each risk is naturally owned by either a **cleaner**
(partition-local, deep) or the **scavenger** (cross-cutting, whole-scope).

| # | Risk | Symptoms (abbreviated) | Owner |
|---|------|------------------------|-------|
| 1 | **Cognitive Overload** | fn > 20 lines mixing abstraction levels, nesting > 3, > 4 params, magic numbers, cryptic names, 3+ condition booleans, train-wreck chains, flag args, primitive obsession, shallow modules | cleaner (local) |
| 2 | **Change Propagation** | one change touches > 3 unrelated files, divergent change, feature envy, inappropriate intimacy, orthogonality violation, information leakage, Hyrum's-Law coupling | **scavenger** (cross-cutting) |
| 3 | **Knowledge Duplication** | same decision in > 1 place, copy-paste logic, one concept named many ways, parallel hierarchies, repeated config literals | cleaner if in-file; **scavenger** if across modules |
| 4 | **Accidental Complexity** | speculative generality (no consumer), lazy classes, middle-men, second-system over-build, switch-instead-of-polymorphism, unused config/extension points, tactical-debt scaffolding | cleaner (local) |
| 5 | **Dependency Disorder** | cycles, high→low-level imports, unstable-under-stable deps, Demeter violations, fan-out > 5, ISP violations, inconsistent architecture | **scavenger** (cross-cutting) |
| 6 | **Domain Model Distortion** | anemic model (logic in services, data-bag objects), ubiquitous-language drift, refused bequest, LSP violation, value-objects-as-entities, bounded-context crossing without ACL | cleaner if local; **scavenger** if naming drift spans the tree |

Sources: Fowler *Refactoring* · McConnell *Code Complete* · Ousterhout *A Philosophy of Software
Design* · Evans *DDD* · Martin *Clean Architecture* (SOLID/ADP/SDP/SAP) · Hunt & Thomas *Pragmatic
Programmer* · Brooks *Mythical Man-Month* · Winters et al. *SWE at Google* (Hyrum's Law).

## ai-slop-cleaner — slop taxonomy (cleanup targets)

**Duplication** · **Dead code** · **Needless abstraction** · **Boundary violations** ·
**Missing tests** · **UI/design defaults** (apply the ai-slop-cleaner UI checklist — Korean body
≥ 14px, shadow/gradient restraint, content hierarchy, palette rationale, layout rhythm — only when
reviewing front-end, as prompts not absolute bans).

## ponytail ladder — the over-engineering lens (cut bar)

The volume-reduction half of "clean": the cleanest form of code is the code that does not exist.
Walk the ladder top-down; the **first rung that holds is the remedy** (a higher rung already covers
the code, so the code below it is slop):

1. **YAGNI** — speculative need with no consumer → skip / delete. (overlaps Accidental Complexity)
2. **Already in this codebase** — a helper / util / type / pattern already lives here → reuse it, delete the re-implementation. (overlaps Knowledge Duplication)
3. **Stdlib does it** — hand-rolled thing the standard library ships → replace with the stdlib call.
4. **Native platform feature** — code (or a dependency) doing what the platform already does → use the native feature, drop the dep.
5. **Installed dependency** — an already-present dep solves it; never add a new dep for a few lines.
6. **One line** — same logic, fewer lines → show the shorter form.

Tag every finding (cleaner + scavenger + reviewer) with the ponytail vocabulary so one report speaks
one language: `delete:` (dead code / unused flexibility — replacement: nothing) · `stdlib:` (name the
function) · `native:` (name the feature / drop the dep) · `yagni:` (one-impl abstraction, config
nobody sets, layer with one caller) · `shrink:` (same logic, fewer lines). These are the
**how-to-cut** vocabulary mapped onto the brooks risks above, not a competing taxonomy.

## SAFE vs RISKY — the cleanup gate

| | **SAFE -> fix now** | **RISKY -> reduce risk, then fix or report only** |
|---|---|---|
| Scope | local to the partition, single file | crosses files / modules / partitions |
| Behavior | provably preserving | could change observable output or a contract |
| Examples | delete dead code / unused imports & exports, in-file dedup, consolidate repeated literals & consts, rename locals, drop comment slop, tighten obvious error handling, remove debug leftovers | extract/move modules, change signatures or public API, collapse abstractions used elsewhere, alter control flow affecting output, anything needing edits outside the partition, anything under behavior you cannot cheaply test |

**When unsure -> RISKY, but RISKY is not permission to preserve slop.** First try to make the
cleanup safe: add the narrowest behavior lock, split the change into a local deletion, or route it
through the post-review single-threaded writer pass. If it still cannot be safely fixed in this
cleanup pass, leave the code unchanged and record a report-only deferred finding. Never create
`TODO`, `FIXME`, `XXX`, `HACK`, `slop-clean`, or placeholder comments as cleanup output.

## What NOT to flag

- Linear code with clear names and guard clauses (not overload).
- Repetition across separate bounded contexts; temporary migration duplication.
- A switch over an external protocol / closed enum; thin wrappers absorbing vendor churn.
- Composition roots / orchestration layers / adapters with high or two-way fan-out by design.
- DTOs, persistence records, API payload models being data-only.
- Domain terminology that matches how experts actually speak.
- **Generated, vendored, lock, and minified files → skip entirely**, note in the report.

**Never cut these even when they read as extra code (ponytail "when NOT to be lazy"):** input
validation at trust boundaries, error handling that prevents data loss, security measures,
accessibility basics, hardware calibration knobs (a real clock drifts, a sensor reads off), and
anything explicitly requested. The one regression / smoke / `assert` self-check a behavior lock
leaves behind is the cleanup *minimum*, not bloat — never flag it for deletion.

## Health Score

Base **100**; **−15** per 🔴 Critical, **−5** per 🟡 Warning, **−1** per 🟢 Suggestion; floor 0.
- 🔴 Critical — breaking velocity / creating production risk *today*
- 🟡 Warning — will, if left unaddressed, within the next few features
- 🟢 Suggestion — worth fixing when nearby, not urgent

Compute per partition; the overall score is the codebase/branch roll-up over all findings
(cleaner + scavenger), Critical first, with a one-line recommended fix order when > 5 findings.

Report the ponytail volume metric beside the score: **`net: -<N> lines, -<M> deps`** — what this pass
actually removed (and what a deferred finding *would* remove). Volume reduction is a first-class
outcome, not a side effect. A partition with nothing left to cut reports **`Lean already. Ship.`**
instead of inventing findings.
