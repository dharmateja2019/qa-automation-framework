# QA Automation Portfolio — Pytest + httpx + Playwright + GitHub Actions

A production-style test automation framework built with Python, demonstrating real-world patterns used in SDET roles at MNCs. Built progressively — API testing, UI automation with POM, fixture scopes, factory pattern, and parallel execution.

## What this project covers

- API testing with `httpx` and `pytest`
- Parametrized test scenarios (happy path, negative cases, schema validation)
- UI automation with Playwright and Page Object Model (POM)
- Multi-page object chaining (login → inventory flow)
- Fixture scopes — function scope for browser and page in parallel runs
- Factory pattern for centralised test data management
- Parallel test execution with `pytest-xdist`
- Custom markers for selective test execution
- Automated CI pipeline with GitHub Actions — two parallel jobs
- HTML test reports uploaded as pipeline artifacts per job

## Tech stack

| Tool              | Purpose                                         |
| ----------------- | ----------------------------------------------- |
| Python 3.13       | Language                                        |
| httpx             | HTTP client for API tests                       |
| pytest            | Test runner and assertion framework             |
| pytest-playwright | Playwright integration for UI tests             |
| pytest-xdist      | Parallel test execution across multiple workers |
| pytest-html       | HTML report generation                          |
| GitHub Actions    | CI pipeline — runs on every push and PR         |

## Project structure

```
ApiTesting/
├── requirements.txt                  # all UI test dependencies
├── pytest.ini                        # pytest config — registered markers
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
│       └── test_scope_experiments.py # fixture scope + parallel execution demos
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

**4. Run UI tests — sequential**

```bash
pytest pom_project/tests/ -v --browser chromium
```

**5. Run UI tests — parallel**

```bash
# 2 workers
pytest pom_project/tests/ -v --browser chromium -n 2

# all available CPU cores
pytest pom_project/tests/ -v --browser chromium -n auto
```

**6. Run by marker**

```bash
# skip slow tests
pytest pom_project/tests/ -v --browser chromium -n auto -m "not slow"

# only slow tests, sequentially
pytest pom_project/tests/ -v --browser chromium -m "slow"
```

**7. Run with HTML report**

```bash
pytest pom_project/tests/ -v --browser chromium -n auto --html=ui-report.html --self-contained-html
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
- Performance glitch user eventually lands on inventory (marked `slow`)

### POM design decisions

**No assertions in page classes** — page objects describe what a page _can do_, not what _should be true_. Assertions live exclusively in test files.

**Locators defined once** — all selectors live in the page class constructor. UI changes require updating one place, not every test.

**Fixture handles navigation** — tests don't call `navigate()` or `login()` manually:

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

### The four scopes

| Scope      | Created          | Destroyed                | Use for                           |
| ---------- | ---------------- | ------------------------ | --------------------------------- |
| `function` | Before each test | After each test          | Page objects, anything with state |
| `module`   | Once per file    | After last test in file  | File-level shared resources       |
| `session`  | Once per run     | After all tests finish   | Stateless HTTP clients            |
| `class`    | Once per class   | After last test in class | OOP-heavy suites                  |

### Critical rule for parallel execution

Session scope does not cross xdist worker process boundaries. A session-scoped browser shared across workers causes failures depending on worker count and test distribution — it may pass with `-n auto` and fail with `-n 2`, making it unreliable.

Solution — use function scope for browser when running parallel:

```python
@pytest.fixture(scope="function")
def browser_instance():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()
```

Each worker gets its own browser per test. Guaranteed safe regardless of worker count.

---

## Module 4 — Factory pattern for test data

### The problem

Hardcoded credentials scattered across 50 test files. One environment change = 50 files to update.

### The solution

```python
# instead of this everywhere
login.login("standard_user", "secret_sauce")

# tests declare what's different, not the whole object
user = UserFactory.build(password="wrong_password")
login.login(user.username, user.password)
```

### Factories built

**UserFactory**

```python
UserFactory.standard()              # default valid user
UserFactory.locked()                # locked out user
UserFactory.slow()                  # performance glitch user
UserFactory.build(username="")      # custom — override only what matters
```

**ProductFactory**

```python
ProductFactory.first()              # default first product
ProductFactory.build(price=9.99)    # custom price override
```

---

## Module 5 — Parallel execution with pytest-xdist

### How it works

`pytest-xdist` spawns N worker processes and distributes tests across them. Each worker runs independently with its own browser instance.

### Observed timing (13 tests, MacBook Pro)

| Mode       | Workers | Time   |
| ---------- | ------- | ------ |
| Sequential | 1       | ~28s   |
| `-n 2`     | 2       | 15.77s |
| `-n auto`  | 16      | 13.16s |

In a real suite with 500 tests the difference is 35 minutes → under 8 minutes.

### Custom markers

Tests are tagged with markers to control parallel vs sequential execution:

```python
@pytest.mark.slow
def test_performance_glitch_user(inventory_page, page):
    ...
```

```bash
# fast tests run in parallel
pytest -n auto -m "not slow"

# slow tests run sequentially to avoid resource contention
pytest -m "slow"
```

Markers are registered in `pytest.ini` to avoid warnings:

```ini
[pytest]
markers =
    slow: marks tests as slow running
```

### Key lesson learned

Session-scoped fixtures are not safe across xdist workers. A browser shared via session scope may pass with many workers (one test per worker = no sharing) but fail with fewer workers (multiple tests per worker = shared browser across process boundary). Always use function scope for stateful resources in parallel runs.

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
3. Install UI dependencies including `pytest-xdist`
4. Install Playwright Chromium with system dependencies (`--with-deps`)
5. Run UI tests in parallel with `-n auto`
6. Upload `ui-report.html` as artifact

### Important lessons learned

- `pytest.ini` addopts must not contain Playwright-specific flags — they apply globally and break non-Playwright jobs
- `playwright install chromium --with-deps` is required on Ubuntu CI — system browser dependencies are not pre-installed
- All packages must be in `requirements.txt` — CI spins up a clean container every run
- Register custom markers in `pytest.ini` — unregistered marks produce warnings across all workers in parallel runs

---

## Testing strategy applied

- **Test pyramid** — API tests at integration layer, UI tests only for critical E2E flows
- **Shift-left** — CI runs on every PR, not just before release
- **Risk-based** — login and cart flows automated first as highest business impact
- **POM separation of concerns** — page layer owns locators and actions, test layer owns assertions
- **Factory pattern** — test data centralised, tests declare intent not setup
- **Parallel execution** — xdist with function-scoped browsers, markers to separate fast and slow tests

---

## Author

Dharmateja Valluri — [LinkedIn](https://linkedin.com/in/) | [GitHub](https://github.com/)
