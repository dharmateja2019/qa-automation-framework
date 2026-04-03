# QA Automation Portfolio — Pytest + httpx + Playwright + GitHub Actions

A production-style test automation framework built with Python, demonstrating real-world patterns used in SDET roles at MNCs. Built progressively — API testing, UI automation with POM, fixture scopes, and factory pattern for test data.

## What this project covers

- API testing with `httpx` and `pytest`
- Parametrized test scenarios (happy path, negative cases, schema validation)
- UI automation with Playwright and Page Object Model (POM)
- Multi-page object chaining (login → inventory flow)
- Fixture scopes — session for browser, function for page
- Factory pattern for centralised test data management
- Automated CI pipeline with GitHub Actions — two parallel jobs
- HTML test reports uploaded as pipeline artifacts per job

## Tech stack

| Tool              | Purpose                                 |
| ----------------- | --------------------------------------- |
| Python 3.13       | Language                                |
| httpx             | HTTP client for API tests               |
| pytest            | Test runner and assertion framework     |
| pytest-playwright | Playwright integration for UI tests     |
| pytest-html       | HTML report generation                  |
| GitHub Actions    | CI pipeline — runs on every push and PR |

## Project structure

```
ApiTesting/
├── requirements.txt                  # UI test dependencies
├── pytest.ini                        # minimal pytest config
│
├── my-api-tests/
│   ├── conftest.py                   # session-scoped API client fixture
│   ├── requirements.txt              # API test dependencies
│   └── test_api.py                   # API test cases
│
├── pom_project/
│   ├── pages/
│   │   ├── login_page.py             # login page actions and locators
│   │   └── inventory_page.py         # inventory page actions and locators
│   ├── test_data/
│   │   ├── user_factory.py           # User dataclass + UserFactory
│   │   └── product_factory.py        # Product dataclass + ProductFactory
│   └── tests/
│       ├── conftest.py               # browser, page, login_page, inventory_page fixtures
│       ├── login_test.py             # login scenarios using UserFactory
│       ├── test_inventory.py         # inventory scenarios
│       └── test_scope_experiments.py # fixture scope demonstration
│
└── .github/
    └── workflows/
        └── tests.yml                 # CI pipeline — api-tests and ui-tests in parallel
```

## How to run locally

**1. Clone the repo**

```bash
git clone https://github.com/dharmateja2019/ApiTesting.git
cd ApiTesting
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
pip install -r my-api-tests/requirements.txt
playwright install chromium
```

**3. Run API tests**

```bash
pytest my-api-tests/test_api.py -v
```

**4. Run UI tests**

```bash
pytest pom_project/tests/ -v --browser chromium
```

**5. Run with HTML report**

```bash
# API
pytest my-api-tests/test_api.py -v --html=api-report.html --self-contained-html

# UI
pytest pom_project/tests/ -v --browser chromium --html=ui-report.html --self-contained-html
```

---

## Module 1 — API testing

Tests run against [JSONPlaceholder](https://jsonplaceholder.typicode.com) — a public fake REST API.

### What is tested

**Status code tests**

- Valid post IDs return `200`
- Non-existent post IDs return `404`
- Parametrized across multiple IDs in one test function

**Schema validation tests**

- Every field (`id`, `title`, `body`, `userId`) is present
- Field types are correct — not just values
- Response `id` matches the requested `id`

**POST tests**

- Creating a post returns `201`
- Response body reflects the submitted payload
- Multiple payload variations tested using parametrize

### Key patterns

**Session-scoped fixture** — one HTTP client shared across all tests:

```python
@pytest.fixture(scope="session")
def api_client():
    with httpx.Client(base_url="...") as client:
        yield client
```

**Parametrize** — one test function covers multiple scenarios:

```python
@pytest.mark.parametrize("post_id, expected_status", [
    (1, 200),
    (99999, 404),
])
def test_get_post_status(post_id, expected_status):
    ...
```

**Schema validation** — checking response shape, not just status code:

```python
assert isinstance(data["id"], int)
assert isinstance(data["title"], str)
assert len(data["title"]) > 0
```

---

## Module 2 — UI automation with Page Object Model

Tests run against [SauceDemo](https://www.saucedemo.com) — a demo e-commerce site built for automation practice.

### What is tested

**Login scenarios**

- Valid credentials redirect to inventory page
- Invalid password shows correct error message
- Empty username shows validation error
- Locked-out user cannot log in

**Inventory scenarios**

- Page loads exactly 6 products
- All product names are non-empty strings
- Adding first product updates cart badge to 1

### POM design decisions

**No assertions in page classes** — page objects describe what a page _can do_, not what _should be true_. Assertions live exclusively in test files. This means a page class never fails for the wrong reason.

**Locators defined once** — all selectors live in the page class constructor. If the UI changes, you update one place, not every test.

**Fixture handles navigation** — tests don't call `navigate()` or `login()` manually. The `inventory_page` fixture handles full setup so each test starts at the right state:

```python
@pytest.fixture(scope="function")
def inventory_page(page):
    user = UserFactory.standard()
    lp = LoginPage(page)
    lp.navigate()
    lp.login(user.username, user.password)
    return InventoryPage(page)
```

**Page chaining** — the same `page` object passes through multiple page objects, reflecting the real browser session.

---

## Module 3 — Fixture scopes

Demonstrates the impact of fixture scope on test isolation and suite speed.

### The four scopes

| Scope      | Created          | Destroyed                | Use for                           |
| ---------- | ---------------- | ------------------------ | --------------------------------- |
| `function` | Before each test | After each test          | Page objects, anything with state |
| `module`   | Once per file    | After last test in file  | File-level shared resources       |
| `session`  | Once per run     | After all tests finish   | Browser instance, HTTP client     |
| `class`    | Once per class   | After last test in class | OOP-heavy suites                  |

### The rule

Ask one question — _can this resource be safely shared between tests without one test affecting another?_

- Browser instance → session scope. Expensive to create, stateless between tests.
- Page object → function scope. Cheap to create, carries state (URL, cookies, cart).

Mixing these up causes state bleed — test A's actions leak into test B's starting state, causing random failures that are hard to debug in isolation.

---

## Module 4 — Factory pattern for test data

### The problem

Hardcoded credentials and test data scattered across 50 test files. One environment change = 50 files to update.

### The solution

Factories build objects with sensible defaults. Tests only specify what is _different_ for their scenario:

```python
# instead of this in every test
login.login("standard_user", "secret_sauce")

# tests now say what's different, not the whole object
user = UserFactory.build(password="wrong_password")
login.login(user.username, user.password)
```

### Factories built

**UserFactory** — standard user, locked user, slow user, and a `build()` method for custom overrides:

```python
user = UserFactory.standard()          # default valid user
user = UserFactory.locked()            # locked out user
user = UserFactory.build(username="")  # custom — only override what matters
```

**ProductFactory** — first product, and a `build()` method for custom product data:

```python
product = ProductFactory.first()                    # default first product
product = ProductFactory.build(price=9.99)          # custom price override
```

### Why this matters

Credentials and test objects are defined in one place. A environment credential change requires updating one file, not every test. Tests become more readable — they describe the scenario, not the setup.

---

## CI pipeline

Two jobs run in parallel on every push to `main` and every pull request.

### api-tests job

1. Checkout code
2. Set up Python 3.13
3. Install API dependencies
4. Run API tests
5. Upload `api-report.html` as artifact

### ui-tests job

1. Checkout code
2. Set up Python 3.13
3. Install UI dependencies
4. Install Playwright Chromium with system dependencies (`--with-deps`)
5. Run UI tests in headless Chromium
6. Upload `ui-report.html` as artifact

### Important lessons learned

- `pytest.ini` addopts must not contain Playwright-specific flags — they apply globally and break non-Playwright jobs
- `playwright install chromium --with-deps` is required on Ubuntu CI — system browser dependencies are not pre-installed
- All packages must be in `requirements.txt` — CI spins up a clean container every run

---

## Testing strategy applied

- **Test pyramid** — API tests at integration layer, UI tests only for critical E2E flows
- **Shift-left** — CI runs on every PR, not just before release
- **Risk-based** — login and cart flows automated first as highest business impact
- **POM separation of concerns** — page layer owns locators and actions, test layer owns assertions
- **Factory pattern** — test data centralised, tests declare intent not setup

---

## Author

Dharmateja Valluri — [LinkedIn](https://linkedin.com/in/) | [GitHub](https://github.com/)
