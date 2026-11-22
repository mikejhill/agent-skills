# Test examples

Pseudocode. Translate to the project's language and runner.

## Example 1: Well-Structured Unit Test

```text
test "calculateDiscount_expiredCoupon_returnsZeroDiscount":
    // Arrange
    coupon = createCoupon(expirationDate: yesterday)
    cart = createCart(subtotal: 100.00)

    // Act
    discount = calculateDiscount(cart, coupon)

    // Assert
    assertEqual(discount, 0.00,
        "Expected zero discount for expired coupon, got ${discount}")
```

**Why this passes validation:**

- Name states unit (`calculateDiscount`), scenario (`expiredCoupon`), expected result (`returnsZeroDiscount`)
- Single behavior tested: expired coupon handling
- Assertion uses exact value (0.00) with diagnostic message
- No shared state, no external dependencies

## Example 2: Anti-Pattern Detection

```text
// BAD — The Tautology
test "testUserService":
    mock = createMock(UserRepository)
    mock.whenCalled("findById").thenReturn(User("Alice"))
    service = UserService(mock)

    result = service.getUser("123")

    assertEqual(result.name, "Alice")  // Only proves mock works
```

**Fix:** Assert on behavior that transforms or validates — not on passthrough of mock setup.

```text
// GOOD — Tests actual behavior
test "getUser_existingId_returnsUserWithFormattedDisplayName":
    mock = createMock(UserRepository)
    mock.whenCalled("findById").thenReturn(User(first: "alice", last: "smith"))
    service = UserService(mock)

    result = service.getUser("123")

    assertEqual(result.displayName, "Alice Smith",
        "Expected formatted display name 'Alice Smith', got '${result.displayName}'")
```

## Example 3: Boundary Value Coverage

```text
test "withdraw_exactBalance_succeeds":
    account = createAccount(balance: 100.00)
    result = withdraw(account, 100.00)
    assertEqual(result.newBalance, 0.00,
        "Withdrawing exact balance should leave zero, got ${result.newBalance}")

test "withdraw_oneAboveBalance_returnsInsufficientFunds":
    account = createAccount(balance: 100.00)
    result = withdraw(account, 100.01)
    assertEqual(result.error, "INSUFFICIENT_FUNDS",
        "Withdrawing 100.01 from 100.00 balance should fail with INSUFFICIENT_FUNDS, got '${result.error}'")

test "withdraw_zero_returnsInvalidAmount":
    account = createAccount(balance: 100.00)
    result = withdraw(account, 0.00)
    assertEqual(result.error, "INVALID_AMOUNT",
        "Withdrawing zero should fail with INVALID_AMOUNT, got '${result.error}'")
```

**Why this set passes validation:**

- Three distinct equivalence classes: exact boundary, one-above-boundary, zero (invalid)
- No overlap — each test covers a unique code path
- Specific assertions with diagnostic messages
- Names communicate the scenario and expected result

## Example 5: Regression Test for a Specific Bug

```text
test "resolveIndex_simpleIntValue_doesNotRecurseIntoIndexMap":
    // Regression: _resolve_index(55, {55: {...}}) was recursively resolving
    // the integer 55 against index_map[55], returning a dict instead of 55.
    index_map = {55: {"name": "unrelated_object"}}

    result = resolveIndex(55, index_map)

    assertEqual(result, 55,
        "Simple int 55 must not be resolved via index_map. "
        "Got ${result} — regression: recursive resolution of non-reference values")
```

**Why this passes validation:**

- Documents the exact bug in a comment
- Constructs the minimal input that triggers the bug
- Asserts on the specific incorrect behavior (returning dict instead of int)
- Failure message references the regression explicitly
