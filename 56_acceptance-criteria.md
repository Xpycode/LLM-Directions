<!--
TRIGGERS: acceptance criteria, given when then, gherkin, BDD, testable requirements, test cases
PHASE: define, plan
LOAD: on-request
-->

# Acceptance Criteria: Given/When/Then

**Write testable requirements before implementation.**

*Adapted from Behavior-Driven Development (BDD) and the fspec methodology.*

---

## Why Given/When/Then?

| Vague Criteria | Testable Criteria |
|----------------|-------------------|
| "User can log in" | Given valid credentials, when user submits login, then user sees dashboard |
| "Handle errors gracefully" | Given network failure, when user saves, then error message with retry option |
| "Fast performance" | Given 1000 items, when list loads, then render completes in <500ms |

The format forces specificity. You can't write Given/When/Then without being concrete.

---

## The Format

```gherkin
Given [precondition/context]
When [action/trigger]
Then [expected outcome]
```

### Components

| Part | Purpose | Example |
|------|---------|---------|
| **Given** | Setup state, preconditions | Given user is logged in |
| **When** | The action being tested | When user clicks "Save" |
| **Then** | Observable outcome | Then success message appears |

### Optional Extensions

```gherkin
Given [context]
  And [additional context]
When [action]
  And [additional action]
Then [outcome]
  And [additional outcome]
  But [exception to outcome]
```

---

## Examples by Category

### UI Behavior

```gherkin
Given the document has unsaved changes
When user clicks the close button
Then confirmation dialog appears with "Save", "Discard", "Cancel" options

Given user has selected 3 photos
When user clicks "Delete"
Then confirmation shows "Delete 3 photos?"
  And "Delete" button is destructive red
```

### Data Operations

```gherkin
Given user has entered valid form data
When user clicks "Submit"
Then data is saved to database
  And success toast appears
  And form resets to empty state

Given file is larger than 10MB
When user attempts upload
Then error message "File too large (max 10MB)" appears
  And upload does not start
```

### Error Handling

```gherkin
Given network connection is lost
When user attempts to sync
Then offline indicator appears
  And local changes are preserved
  And sync retries automatically when connection restored

Given API returns 500 error
When user loads dashboard
Then error message with "Retry" button appears
  But cached data is still displayed if available
```

### Edge Cases

```gherkin
Given search query is empty
When user clicks "Search"
Then all items are displayed (no filter)

Given list has 0 items
When user views list
Then empty state illustration appears
  And "Add first item" button is prominent
```

### Performance

```gherkin
Given database has 10,000 records
When user opens list view
Then first 50 items render within 200ms
  And scroll performance maintains 60fps
```

---

## Writing Good Criteria

### The SMART Test

Each criterion should be:

| Attribute | Question | Example |
|-----------|----------|---------|
| **Specific** | Is it unambiguous? | "Error appears" → "Red banner with message X appears" |
| **Measurable** | Can we verify it? | "Fast" → "Under 500ms" |
| **Achievable** | Can we implement it? | Not "AI predicts perfectly" |
| **Relevant** | Does it matter to users? | Not internal implementation details |
| **Testable** | Can we write a test? | If you can write Given/When/Then, yes |

### Common Improvements

| Weak | Strong |
|------|--------|
| "Works correctly" | Given [specific input], then [specific output] |
| "Handles errors" | Given [specific error], then [specific recovery] |
| "Is fast" | Given [load], then [metric] within [threshold] |
| "Looks good" | Given [state], then [specific visual elements] visible |
| "Is secure" | Given [attack vector], then [specific protection] |

---

## Organizing Criteria in Specs

Group by priority and type:

```markdown
## Acceptance Criteria

### Must Have (P0)
- [ ] Given valid email/password, when login submitted, then user sees dashboard
- [ ] Given invalid password, when login submitted, then "Invalid credentials" error

### Should Have (P1)
- [ ] Given 3 failed attempts, when 4th attempt fails, then account locked for 15 min
- [ ] Given locked account, when user tries login, then "Account locked" with unlock time

### Nice to Have (P2)
- [ ] Given login on new device, when successful, then email notification sent

### Edge Cases
- [ ] Given empty email field, when submit clicked, then "Email required" validation
- [ ] Given email without @, when submit clicked, then "Invalid email format" validation

### Error States
- [ ] Given server unreachable, when login attempted, then "Connection error" with retry
- [ ] Given session expired, when action attempted, then redirect to login
```

---

## From Criteria to Tests

Given/When/Then maps directly to test structure:

```swift
// Given valid credentials
func testLoginWithValidCredentials() {
    // Given
    let email = "user@example.com"
    let password = "validPassword123"

    // When
    let result = authService.login(email: email, password: password)

    // Then
    XCTAssertTrue(result.isSuccess)
    XCTAssertNotNil(result.user)
}

// Given invalid password
func testLoginWithInvalidPassword() {
    // Given
    let email = "user@example.com"
    let password = "wrongPassword"

    // When
    let result = authService.login(email: email, password: password)

    // Then
    XCTAssertTrue(result.isFailure)
    XCTAssertEqual(result.error?.message, "Invalid credentials")
}
```

---

## Integration with Directions

### During /interview
- Capture requirements as rough acceptance criteria
- Refine into Given/When/Then format during spec writing

### During /plan
- Each task should map to one or more acceptance criteria
- Task is "done" when its criteria pass

### During /execute
- Run acceptance criteria as checklist after implementation
- Mark criteria as verified in spec

### During /reflect
- Check: Are all acceptance criteria verified?
- Check: Did we discover criteria we missed?

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Implementation detail | "Database query uses index" | Focus on user-visible behavior |
| Untestable | "App is intuitive" | "Given first-time user, can complete [flow] without help" |
| Too many Ands | Criterion tests 5 things | Split into separate criteria |
| Missing Given | "When user clicks, then works" | What state? What user? |
| Vague Then | "Then it updates" | What updates? How do we verify? |

---

*If you can't write Given/When/Then, you don't understand the requirement yet.*
