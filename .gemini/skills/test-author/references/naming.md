# Test Naming

A test's name is the first thing read when it fails, the only thing read in the test runner output, and the only thing read in the CI summary. Treat naming like API design.

## Contents
- [What a good test name does](#what-a-good-test-name-does)
- [Three naming styles](#three-naming-styles)
- [File and folder organization](#file-and-folder-organization)
- [Common mistakes](#common-mistakes)

## What a good test name does

A good test name lets a reader, **without opening the test body**:

1. Know **what behaviour** is being asserted.
2. Know **under what conditions** the behaviour applies.
3. Diagnose **what's broken** when the test fails — at least to the right area.

**A test name is not "the function it tests".** A test name describes **a fact about the system**. `getUser()` is a function; `returnsNullWhenUserDoesNotExist` is a fact.

## Three naming styles

Each style works. Pick one per project (or per file) and stay consistent. Mixing styles within a file makes the file hard to scan.

### Style A — `methodOrFeature_condition_outcome`

```
getUser_whenIdUnknown_returnsNull
applyDiscount_whenCustomerIsMember_appliesTenPercent
parseDate_whenInputIsEmpty_throwsValidationError
```

Pros: explicit, mechanical, easy to scan a long list.
Cons: gets ugly when conditions are complex; reads like code.

### Style B — `should_outcome_when_condition`

```
should_return_null_when_id_is_unknown
should_apply_ten_percent_discount_when_customer_is_member
should_throw_validation_error_when_input_is_empty
```

Pros: reads like English; emphasizes the behaviour.
Cons: every test starts with "should" (you tune it out); verbose.

### Style C — Behaviour-Driven (Given/When/Then in nested describe blocks)

```
describe("Order pricing")
  describe("when the customer is a member")
    it("applies a 10% discount")
    it("rounds the discount to the nearest cent")
  describe("when the customer is not a member")
    it("applies no discount")
```

Pros: hierarchical reading, mirrors the AC structure.
Cons: requires a framework that supports nesting; can sprawl; failing test output may show only the leaf without context.

### How to choose

- **Small project / flat test files** → Style A or B.
- **Behaviour-rich, well-grouped suites** → Style C.
- **Large project with mixed team backgrounds** → pick one and add it to the contributing guide.

**The wrong choice is having no convention.** Pick anything and stick to it.

## Test file naming

Match the production file, with `.test` or `.spec` (whatever the test runner expects):

```
src/dashboards/dashboard-service.ts
src/dashboards/dashboard-service.test.ts
```

For integration / e2e:

```
tests/integration/dashboards-api.test.ts
tests/e2e/dashboard-creation.test.ts
```

Folder structure:

- **Unit tests** sit next to production code OR mirror its structure in a parallel `tests/unit/` tree. Either works — pick one.
- **Integration tests** live in `tests/integration/` (separate suite, separate runner config, separate speed budget).
- **E2E tests** live in `tests/e2e/` (separate runner — Playwright / Cypress / whatever).

## File and folder organization

Within a test file:

- **One file per production unit.** `DashboardService` → `dashboard-service.test.ts`. If a test file is 1000+ lines, the production unit probably does too much.
- **Group by behaviour, not by method.** A `describe("DashboardService.save")` block that contains 20 `it`s is fine. A file with 200 unrelated `it`s at the top level is hard to navigate.
- **Order tests by importance.** Happy path first, then edge cases, then errors. Reviewers read top-down.

## Common mistakes

- **Generic names.** `it("works")`, `it("does the thing")`, `test_1`. Useless in failure output.
- **Naming the function instead of the behaviour.** `test_getUser` doesn't tell you what's being verified.
- **Long compound names that try to describe everything in one sentence.** Split into smaller tests with simpler names.
- **Restating the assertion in the name.** `it("returns 42")` paired with `expect(x).toEqual(42)` — the name should describe **why** the answer is 42 ("returns the user's age when DOB is set"), not echo the number.
- **Mixing naming styles in one file.** Eight `should_*` tests followed by three `getUser_*` tests — pick one.
- **Names that say "test"** in them (`testGetUser`). The framework already knows it's a test; the prefix wastes characters.
- **Names with implementation details.** `it("calls userRepo.findById once")` locks the test to implementation. Name the behaviour.
