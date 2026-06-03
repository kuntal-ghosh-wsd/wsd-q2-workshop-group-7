---
name: test-author
description: >
  Turn Acceptance Criteria into executable tests at the right level (unit,
  integration, end-to-end), with clear names, minimal mocking, and
  reliable signals. Tool- and stack-agnostic — covers strategy, naming,
  AAA structure, mocking philosophy, fixture discipline, flake control;
  produces guidance and templates, not framework-specific code generation.
  Use when the user is about to write tests for a story or AC, asks at
  what level something should be tested, wants help with a test plan,
  asks why a test is flaky, needs a test-naming convention, or asks
  whether something is worth testing. Triggers on phrasing like "write
  tests for this", "what should I test", "unit or integration", "this
  test is flaky", "how do I structure these tests", "write a test plan
  for story X".
---

# Test Author

A guide for writing tests that catch real bugs without becoming a maintenance burden. Tool- and framework-agnostic.

## When to use this skill

| Signal phrase | Topic |
|---|---|
| "write tests for US-...", "test this story", "what tests do I need" | Test strategy → unit/integration/e2e selection |
| "unit test or integration test", "at what level" | [references/test-strategy.md](references/test-strategy.md) |
| "how do I structure this test", "name this test" | [references/unit-tests.md](references/unit-tests.md) |
| "should I mock this", "real DB or in-memory" | [references/integration-tests.md](references/integration-tests.md) |
| "this e2e is flaky", "make e2e reliable" | [references/e2e-tests.md](references/e2e-tests.md) |
| "naming convention", "what to call this test" | [references/naming.md](references/naming.md) |

**Do not use** for: running tests, debugging a specific failing test in production code, framework lookup ("how do I mock in Jest"). Those are direct coding tasks, not test-design guidance.

## Pre-flight

Before writing tests, gather:

1. **The Acceptance Criteria** for the story or feature. Every test traces back to at least one AC. If the ACs are vague or untestable, fix them first — see the AC reference in `product-spec-pipeline`.
2. **The TAD components involved** — drives whether a test goes unit / integration / e2e.
3. **Existing test patterns in the codebase** — match the style already in use unless there's a concrete reason to break.

If ACs don't exist, push back — generating tests from a story alone produces tests that pass without validating anything meaningful.

## The test design loop

```
1. Read the AC                  → understand the predicate to verify
2. Pick the level               → unit / integration / e2e (see test-strategy)
3. Name the test                → describe behaviour, not implementation
4. Write Arrange / Act / Assert → one behaviour per test
5. Run it failing first         → verify the test can catch the bug it's testing for
6. Make it pass                 → then refactor (production code or test) if needed
```

Step 5 is non-negotiable. A test you never saw fail might assert nothing.

## Topic selector

Load only the reference relevant to the current question.

| Question | Reference |
|---|---|
| "What level should I test this at? How much of each?" | [references/test-strategy.md](references/test-strategy.md) |
| "How do I structure this single test? When/what to mock?" | [references/unit-tests.md](references/unit-tests.md) |
| "Real DB? Real network? How do I handle fixtures?" | [references/integration-tests.md](references/integration-tests.md) |
| "Flaky e2e. Selectors. Page objects. Data setup." | [references/e2e-tests.md](references/e2e-tests.md) |
| "What should I call this test?" | [references/naming.md](references/naming.md) |

## The 7 rules that hold across all test levels

1. **One behaviour per test.** A test that fails should point to one cause. A test with five assertions points to five possible causes.
2. **No conditionals in tests.** If your test has `if`, you have two tests in a trench coat. Split.
3. **Tests are documentation.** A reviewer should understand the behaviour from the test name + Arrange alone.
4. **Arrange-Act-Assert, visibly separated.** Either by blank lines or explicit comments. Whatever helps the reader.
5. **Test the public surface, not the implementation.** Tests that assert internal method calls re-break every time you refactor.
6. **Independent tests.** Order should not matter. One test should not depend on side effects from another.
7. **Deterministic.** No `Date.now()`, no `Math.random()`, no network unless the test is explicitly for network behaviour. Inject clocks and randomness sources.

## Quality gates

Before declaring a test suite done for a story:

- [ ] **AC coverage** — every AC in the story is asserted by at least one test.
- [ ] **Negative cases** — for each happy path, at least one error / validation / boundary case.
- [ ] **No skip / focus left in** — no `it.only`, `xit`, `@Ignore`, `pytest.mark.skip`.
- [ ] **Runs in CI** — not just locally. New test files must be picked up by the test runner.
- [ ] **Fast enough to run on save** for unit tests. Slow tests demoralize the team and rot.
- [ ] **No flakes** — re-run 5 times; if any run fails, fix before merging.

## Common mistakes

- **Testing the framework, not your code.** Asserting "the JSON parser parsed JSON" tests nothing.
- **One giant test per story.** A 200-line test with 30 assertions is unmaintainable. Split per AC.
- **Mocking everything.** Mocks freeze in time; production drifts. Real dependencies where feasible.
- **Snapshot tests for everything.** Snapshots invite "just update the snapshot" instead of thinking. Use sparingly.
- **No failing test before the fix.** Writing the test after the fix can't prove the test catches the bug.
- **Coverage as a target.** 100% line coverage with low-quality assertions is worse than 60% with sharp ones.
- **Slow tests in the unit suite.** Unit tests must be milliseconds. If it's seconds, it's an integration test mislabeled.
