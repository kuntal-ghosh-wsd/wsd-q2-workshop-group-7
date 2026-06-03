# Refactoring — When and How

Refactoring is changing the structure of code **without changing its behaviour**. It's worth doing when it makes the next change easier; it's wasted effort when done for its own sake.

## Contents
- [When to refactor (and when not to)](#when-to-refactor-and-when-not-to)
- [Refactor before, not during](#refactor-before-not-during)
- [Core refactoring moves](#core-refactoring-moves)
- [Detecting code smells](#detecting-code-smells)
- [Safety net](#safety-net)
- [Common mistakes](#common-mistakes)

## When to refactor (and when not to)

**Refactor when:**

- You're about to add a feature and the current shape makes it harder than it should be.
- A bug fix would be cleaner if a function were broken into pieces first.
- A repeated pattern has appeared **three times** (the Rule of Three) and is now begging for an extraction.
- A name has become misleading because its meaning changed.

**Do not refactor when:**

- Nothing is changing in that area — refactoring "for cleanliness" with no concrete follow-up is churn.
- You're in the middle of an unrelated feature PR (mix = bad review).
- You can't articulate a concrete benefit ("this feels nicer" is not a benefit).
- The code is about to be deleted.

The litmus test: "What specifically will be easier after this refactor?" If you cannot answer in one sentence with a concrete future change, skip it.

## Refactor before, not during

**Refactor first, then add the feature.** Two diffs, in this order:

1. **PR 1 — Refactor.** Change shape. No behaviour change. All existing tests pass unchanged.
2. **PR 2 — Feature.** Add new behaviour on the refactored shape. New tests.

Reviewer can focus on "did the refactor actually preserve behaviour" in PR 1 and "is the new behaviour correct" in PR 2 — separately. Mixed PRs hide both.

If you discover mid-feature that you need a refactor: **stash, refactor in a separate PR, land it, rebase, continue**. Don't smuggle the refactor into the feature PR.

## Core refactoring moves

These are the high-yield moves. Each preserves behaviour.

### Extract function

Pull a chunk of logic into a named function. The function name documents what the chunk does. Yields biggest readability gain when the extracted name is genuinely more informative than the inline code.

### Inline function / variable

The opposite. If a function is used in one place and its body is shorter than its call site, inline it.

### Rename

Almost always cheap, often the highest-leverage refactor. If a name is misleading, rename it. Your IDE handles the mechanics — use it.

### Extract type / struct / class

When several values always travel together (e.g. `firstName`, `lastName`, `email`), make them a type. Reduces parameter count and gives them a name.

### Replace conditional with polymorphism

When a `switch` or chain of `if`s on the same enum is repeated in multiple places, the enum is asking to be a type with subtypes. Apply with care — only worth it when there are 3+ such conditionals.

### Replace flag parameter with separate functions

`render(data, summaryOnly: true)` → `renderSummary(data)` / `renderDetail(data)`. Two clear functions beat one ambiguous one.

### Decompose conditional

When a condition is hard to read (`if (date.after(SUMMER_START) && date.before(SUMMER_END) && !customer.preferredRate)`), extract it into a named function: `if (qualifiesForSummerSurcharge(date, customer))`.

### Move function

When a function reads or writes more state from another class/module than its own, it belongs over there.

### Replace magic literal with named constant

`if (status == 3)` → `if (status == OrderStatus.SHIPPED)`. Constants are documentation.

## Detecting code smells

The classic smells are still the right starting list:

| Smell | What it looks like | Refactor |
|---|---|---|
| **Long function** | Doesn't fit on one screen | Extract function |
| **Long parameter list** | 4+ params | Extract type, or rethink coupling |
| **Duplicated code** | Same shape in 3+ places | Extract function |
| **Large class/module** | Hundreds of unrelated methods | Split by responsibility |
| **Feature envy** | Function constantly reads another object's fields | Move function |
| **Data clumps** | Same group of vars passed everywhere | Extract type |
| **Primitive obsession** | Everything is a string or int | Introduce types (`UserId`, `Email`) |
| **Switch statements** | Same switch in 3+ places | Polymorphism |
| **Speculative generality** | Abstraction with one implementation | Inline |
| **Comments** | Long comment explaining what code does | Extract function with that name |

The goal is naming the smell so the refactor becomes obvious. If you can't name the smell, the code may be fine.

## Safety net

Every refactor needs a safety net or it's just guessing:

1. **Tests must exist** for the area being refactored. If they don't, write characterization tests first — tests that pin down current behaviour, even if that behaviour is wrong. Then refactor. Then fix the behaviour in a separate PR.
2. **Run tests after each move**, not at the end. A failing test after one move is a 30-second debug; after twenty moves, an hour.
3. **Use the IDE's refactoring tools** for mechanical operations (rename, extract). They preserve behaviour mechanically; hand-edits drop semicolons.
4. **Keep the diff small.** A 2000-line "refactor" PR is impossible to verify. Split into a sequence of small, mechanical moves.

## Common mistakes

- **Refactoring without tests.** You don't know if you preserved behaviour. You're just hoping.
- **Refactoring while changing behaviour.** Reviewers cannot tell which line caused which change. Split.
- **Premature abstraction.** Three lines repeated twice is not a pattern. Three lines repeated five times across the codebase is.
- **Generalizing for hypothetical future needs.** The future need rarely arrives in the shape you predicted.
- **Renaming and moving in the same commit.** The diff makes the rename invisible. Rename in one commit, move in the next.
- **Refactoring code that's about to be deleted.** Verify before polishing.
- **Calling cleanup "refactor".** Cleanup (delete dead code, fix names) is fine but say what it is. "Refactor" implies structural change.
