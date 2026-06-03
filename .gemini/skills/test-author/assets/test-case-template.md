<!--
Test case template — pseudocode form. Adapt to your test framework's syntax
(Jest / Vitest / pytest / JUnit / Go testing / etc.). Structure is the
same across all: Arrange, Act, Assert.
-->

TEST: <descriptive name — describe behaviour and condition, not the function>

  // Arrange — set up the world the test needs
  <create inputs, fixtures, test doubles where required>

  // Act — exactly one call under test
  <invoke the unit under test>

  // Assert — verify the observable outcome
  expect(<actual>).toEqual(<expected>)

---

Example — unit test:

TEST: applies member discount when customer is a member

  // Arrange
  customer = aMember()
  order    = anOrder().withCustomer(customer).withItems(itemAt(100)).build()
  pricer   = newPricer()

  // Act
  total = pricer.computeTotal(order)

  // Assert
  expect(total).toEqual(90)   // 10% member discount

---

Example — integration test (HTTP boundary):

TEST: POST /dashboards rejects empty name with 400

  // Arrange
  client = httpClientFor(testServer)

  // Act
  response = client.post("/dashboards", body: { name: "" })

  // Assert
  expect(response.status).toEqual(400)
  expect(response.body.error).toMatch(/name required/)

---

Example — e2e test:

TEST: user can sign up, create a dashboard, and see it on reload

  // Arrange
  email = uniqueEmail()

  // Act — drive the UI as a user would
  page.navigate("/signup")
  page.fillForm({ email, password: "valid-password" })
  page.clickButton("Sign up")

  page.waitForUrl("/dashboards")
  page.clickButton("New dashboard")
  page.fillInput("name", "My first dashboard")
  page.clickButton("Save")

  page.reload()

  // Assert at the UI level
  page.assertTextVisible("My first dashboard")

  // Cleanup
  api.deleteUser(email)
