# Code Quality Heuristics

Code-quality judgments that hold across languages and frameworks. These are heuristics, not laws — they exist to save reviewer attention for the genuinely hard decisions.

## Contents
- [Naming](#naming)
- [Function size and shape](#function-size-and-shape)
- [Comments](#comments)
- [Error handling](#error-handling)
- [State and side effects](#state-and-side-effects)
- [Boundaries](#boundaries)
- [Things to delete](#things-to-delete)

## Naming

Names are the highest-leverage form of documentation. A reader spends more time reading names than reading any other part of the code.

**Rules:**

- A function/method name says **what it returns or causes** in the present tense: `getUserById`, `parseConfig`, `markOrderShipped`. Not `userHelper`, not `doProcessing`.
- A variable name says **what it holds**, not its type: `userCount`, not `userInt`; `pendingOrders`, not `arr`.
- A boolean reads like a yes/no question: `isReady`, `hasPermission`, `canEdit` — not `ready`, not `permission`.
- A type / class is a noun: `Order`, `EmailSender`, `RateLimiter` — not `OrderManager`, not `Stuff`.
- Avoid trailing noise words: `data`, `info`, `manager`, `handler`, `helper`, `util`. They almost always indicate fuzzy thinking. Be specific.

**Length follows scope.** Loop counter in a 3-line block: `i` is fine. Module-level variable: spell it out.

**Names that lie are worse than no names.** If `validateEmail` actually parses the email AND validates it AND sends a verification mail, the name lies. Either rename or split.

## Function size and shape

- **One reason to change.** A function that does input validation, calls a database, and formats a response has three reasons to change. Split.
- **One level of abstraction.** A function should not mix "compute tax" and "set the value of an HTML input field". Push one level down.
- **Bounded length.** Soft target: a function fits on one screen. Hard target: if you need to scroll to see both ends, it's too long.
- **Few parameters.** 0–3 is healthy. 4+ usually means: the function does too much, or the parameters should be a struct/object, or there's hidden coupling.
- **No flag parameters.** `render(data, true)` — what's `true`? Split into `renderDetail(data)` and `renderSummary(data)`.

## Comments

Default: write no comment. Only add one when the **why** is non-obvious.

**Good comments answer questions the code cannot:**

- "Why this odd ordering?" — "Must process A before B because B mutates A's state in the legacy adapter."
- "Why this seemingly arbitrary value?" — "300 ms is the threshold after which users report the UI feels laggy (see UX research 2024-Q3)."
- "Why is this here at all?" — "Workaround for upstream bug #1234, remove when library v3 ships."

**Bad comments restate the code:**

- ❌ `// increment counter` next to `counter++`
- ❌ `// loop through users` next to `for u in users:`
- ❌ JSDoc/docstring that just rephrases the function signature

**Never write:**

- Comments about who wrote the code or when ("Added by Alice 2023-04-12") — `git blame` does this better.
- Comments referencing tickets in code that's expected to outlive the ticket ("Fix for JIRA-42").
- Multi-paragraph design rationale at the top of a file — that's a doc, not a comment.

## Error handling

- **Errors at boundaries, not in the middle.** Validate input where it enters the system (HTTP handler, queue consumer, CLI). Once data is past the boundary, trust it.
- **Fail loudly, fail early.** Don't catch-and-ignore. Don't wrap an exception just to re-throw a different one. Let it surface unless you can actually recover.
- **Don't add try/catch as a vibe.** Each catch block must name what it expects to catch and what it does in response.
- **No silent fallbacks.** If a config value is missing, fail at startup — don't silently default. If a network call fails, surface it — don't return an empty list as if nothing happened.
- **Error messages are for humans.** Include what failed, why, and what to do about it. "Error: undefined" is malpractice.

## State and side effects

- **Prefer pure functions** for logic. Functions that take inputs and return outputs are trivially testable and reusable.
- **Isolate side effects** (I/O, mutation, time, randomness) at the edges of the system. The core logic should be deterministic.
- **Avoid hidden state.** Globals, singletons, and ambient context make code surprising and hard to test.
- **Mutable shared state across threads/async** is where most production bugs hide. Treat it with deep suspicion.

## Boundaries

- **Internal vs external boundaries.** Don't validate inputs from your own modules — trust internal callers. Validate aggressively at HTTP, CLI, queue, file-parsing boundaries.
- **Keep external API surface small.** A module's public API should be the minimum needed. Default everything to private/internal; widen only when forced.
- **Don't leak internal types across boundaries.** The HTTP response shape should not be your database row.

## Things to delete

Most code reviews under-delete. When in doubt, delete:

- Commented-out code (git remembers).
- "Just in case" parameters that no caller uses.
- Layers of abstraction with one implementation.
- Tests that assert framework behaviour, not your code's behaviour.
- TODOs older than three months — either do them or remove them.
- "Backward compatibility" shims for internal code with no external consumers.

If you cannot name the concrete reason a piece of code exists, that is the reason it should be deleted.
