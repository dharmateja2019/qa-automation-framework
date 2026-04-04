# QA Automation Portfolio — Pytest + httpx + Playwright + Allure + Docker + K6 + GitHub Actions

A production-style test automation framework built with Python and JavaScript, demonstrating real-world patterns used in SDET roles at MNCs. Built progressively across 9 modules — API testing, UI automation with POM, fixture scopes, factory pattern, parallel execution, BasePage inheritance, Allure reporting, Docker containerisation, and K6 performance testing.

## What this project covers

- API testing with `httpx` and `pytest`
- Parametrized test scenarios (happy path, negative cases, schema validation)
- UI automation with Playwright and Page Object Model (POM)
- BasePage inheritance — shared behaviour across all page objects
- Centralised config with environment variable support
- Multi-page object chaining (login → inventory flow)
- Fixture scopes — function scope for browser and page in parallel runs
- Factory pattern for centralised test data management
- Parallel test execution with `pytest-xdist`
- Custom markers for selective test execution
- Screenshot on failure — embedded directly in Allure report
- Allure reporting — interactive dashboard with steps, severity, feature grouping
- Docker containerisation — consistent environment across all machines
- K6 performance testing — load tests with thresholds, ramp-up stages, and CI integration
- Automated CI pipeline with GitHub Actions — three parallel jobs
- Allure results and report uploaded as CI artifacts

## Tech stack

| Tool              | Purpose                                         |
| ----------------- | ----------------------------------------------- |
| Python 3.12       | Language (pinned via Docker base image)         |
| httpx             | HTTP client for API tests                       |
| pytest            | Test runner and assertion framework             |
| pytest-playwright | Playwright integration for UI tests             |
| pytest-xdist      | Parallel test execution across multiple workers |
| allure-pytest     | Allure reporting integration                    |
| Docker            | Containerised test environment                  |
| K6                | Performance and load testing                    |
| GitHub Actions    | CI pipeline — runs on every push and PR         |

## Project structure

```
ApiTesting/
├── Dockerfile                        # container definition — Playwright base image
├── .dockerignore                     # excludes cache, venv, results from image
├── requirements.txt                  # all UI test dependencies
├── pytest.ini                        # pytest config — pythonpath, registered markers
│
├── my-api-tests/
│   ├── conftest.py                   # session-scoped API client fixture
│   ├── requirements.txt              # API test dependencies
│   └── test_api.py                   # API test cases
│
├── performance/
│   └── api_load_test.js              # K6 load test — mirrors functional API tests
│
├── pom_project/
│   ├── core/
│   │   ├── base_page.py              # shared behaviour — wait, navigate, screenshot, title
│   │   └── config.py                 # centralised config — BASE_URL, timeout, headless
│   ├── pages/
│   │   ├── login_page.py             # inherits BasePage
│   │   └── inventory_page.py         # inherits BasePage
│   ├── test_data/
│   │   ├── user_factory.py           # User dataclass + UserFactory
│   │   └── product_factory.py        # Product dataclass + ProductFactory
│   ├── screenshots/                  # auto-populated on test failure (local)
│   └── tests/
│       ├── conftest.py               # fixtures + screenshot_on_failure hook
│       ├── login_test.py             # login scenarios with Allure steps
│       ├── test_inventory.py         # inventory scenarios with Allure severity
│       └── test_scope_experiments.py # fixture scope + parallel demos
│
└── .github/
    └── workflows/
        └── tests.yml                 # CI — api-tests, ui-tests, performance-tests
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
brew install k6
```

**3. Run API tests**

```bash
pytest my-api-tests/test_api.py -v
```

**4. Run UI tests**

```bash
pytest pom_project/tests/ -v --browser chromium -n auto
```

**5. Run with Allure reporting**

```bash
pytest pom_project/tests/ -v --browser chromium -n 2 --alluredir=allure-results
allure serve allure-results
```

**6. Run performance tests**

```bash
k6 run performance/api_load_test.js
```

**7. Run with Docker**

```bash
docker build -t qa-automation .
docker run qa-automation
docker run -v $(pwd)/allure-results:/app/allure-results qa-automation
```

**8. Run against a different environment**

```bash
BASE_URL=https://staging.saucedemo.com pytest pom_project/tests/ -v --browser chromium
docker run -e BASE_URL=https://staging.example.com qa-automation
```

---

## Viewing Allure reports from CI

1. Go to **Actions** → select the run → scroll to **Artifacts**
2. Download the `allure-report` artifact
3. Unzip the downloaded file
4. Run: `allure open allure-report/`

**Important:** do not open `index.html` directly — use `allure open` or `python3 -m http.server`. The `file://` protocol blocks Allure's JavaScript.

---

## Module 1 — API testing

Tests run against [JSONPlaceholder](https://jsonplaceholder.typicode.com) — a public fake REST API.

### What is tested

**Status code tests**

- Valid post IDs return `200`, non-existent IDs return `404`
- Parametrized across multiple IDs in one test function

**Schema validation tests**

- Every field (`id`, `title`, `body`, `userId`) present and correctly typed
- Response `id` matches the requested `id`

**POST tests**

- Creating a post returns `201` with correct response body
- Multiple payload variations via parametrize

### Key patterns

```python
@pytest.fixture(scope="session")
def api_client():
    with httpx.Client(base_url="...") as client:
        yield client

@pytest.mark.parametrize("post_id, expected_status", [
    (1, 200), (99999, 404),
])
def test_get_post_status(post_id, expected_status):
    ...
```

---

## Module 2 — UI automation with Page Object Model

Tests run against [SauceDemo](https://www.saucedemo.com).

### What is tested

- Valid/invalid login scenarios
- Locked-out user behaviour
- Inventory page load, product count, cart badge
- Page title and URL via BasePage methods

### POM design decisions

- No assertions in page classes — pages describe _what can be done_, tests decide _what should be true_
- Locators defined once — UI changes require updating one place
- Fixtures handle navigation — tests start at the right state automatically
- Page chaining — same `page` object flows through multiple page objects

---

## Module 3 — Fixture scopes

| Scope      | Use for                            |
| ---------- | ---------------------------------- |
| `function` | Browser, page, anything with state |
| `session`  | Stateless HTTP clients             |
| `module`   | File-level shared resources        |

Session scope does not cross xdist worker boundaries — always use function scope for browser in parallel runs.

---

## Module 4 — Factory pattern for test data

```python
UserFactory.standard()               # default valid user
UserFactory.locked()                 # locked out user
UserFactory.build(password="wrong")  # override only what matters
```

Credentials in one place. Tests declare intent, not setup.

---

## Module 5 — Parallel execution with pytest-xdist

| Mode       | Workers | Time | Environment    |
| ---------- | ------- | ---- | -------------- |
| Sequential | 1       | ~30s | Local Mac      |
| `-n 2`     | 2       | ~15s | Local Mac      |
| `-n auto`  | 16      | ~13s | Local Mac      |
| `-n auto`  | 4       | ~12s | GitHub Actions |
| `-n auto`  | 4       | ~19s | Docker         |

```bash
pytest -n auto -m "not slow"   # fast tests in parallel
pytest -m "slow"               # slow tests sequentially
```

---

## Module 6 — BasePage inheritance and framework design

```python
class BasePage:
    def wait_for_element(self, locator): ...
    def navigate_to(self, url: str): ...
    def get_page_title(self) -> str: ...
    def get_current_url(self) -> str: ...

class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # login-specific locators only
```

---

## Module 7 — Allure reporting

| Feature          | pytest-html     | Allure                     |
| ---------------- | --------------- | -------------------------- |
| Report type      | Static HTML     | Interactive dashboard      |
| Test grouping    | None            | Feature / story / severity |
| Step breakdown   | No              | Yes                        |
| Screenshot embed | Separate folder | Inline in failing test     |
| Trend history    | No              | Yes                        |

---

## Module 8 — Docker containerisation

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.58.0-noble
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["pytest", "pom_project/tests/", "-v", "--browser", "chromium", "-n", "auto", "--alluredir=allure-results"]
```

Key decisions: pin image version (not `latest`), copy `requirements.txt` before source for layer caching, `.dockerignore` excludes cache and results.

---

## Module 9 — K6 performance testing

### How K6 relates to pytest

Pytest asks: _does it work correctly?_ — one request, one assertion.
K6 asks: _does it work correctly under load?_ — same endpoints, hundreds of concurrent requests, with thresholds that fail the build on regression.

### Script structure

```javascript
export const options = {
  stages: [
    { duration: "10s", target: 5 }, // ramp up
    { duration: "20s", target: 10 }, // sustain
    { duration: "10s", target: 0 }, // ramp down
  ],
  thresholds: {
    "http_req_duration{name:get_post}": ["p(95)<400"],
    "http_req_duration{name:create_post}": ["p(95)<600"],
    http_req_failed: ["rate<0.01"],
  },
};
```

### Results observed (JSONPlaceholder)

| Metric            | Result     | Threshold |
| ----------------- | ---------- | --------- |
| get_post p(95)    | 41ms       | < 400ms ✓ |
| create_post p(95) | 45ms       | < 600ms ✓ |
| failure rate      | 0.00%      | < 1% ✓    |
| throughput        | 14.5 req/s | —         |

### Key concepts

`p(95)` — 95th percentile response time. Industry standard metric — not average, which hides outliers.

`thresholds` — pass/fail criteria. K6 exits non-zero when breached — CI pipeline fails automatically, same as a failing unit test.

`stages` — ramp-up pattern simulates realistic traffic. Instant spikes skew results.

`groups + tags` — separate thresholds per endpoint. List endpoint can be slower than single-item endpoint.

`sleep(1)` — think time between requests. Simulates real user behaviour, prevents unrealistic hammering.

### Mirrors functional tests

```
pytest: test_get_post_returns_200    → K6: GET /posts/1, check status 200
pytest: test_create_post_returns_201 → K6: POST /posts, check status 201
pytest: test_post_schema_is_correct  → K6: GET /posts/1, check title exists
```

---

## CI pipeline

Three jobs run in parallel on every push to `main` and every pull request.

### api-tests job

1. Install dependencies → run API tests → upload report

### ui-tests job

1. Install dependencies + Playwright → run tests with `-n auto` → generate Allure report → upload artifacts

### performance-tests job

1. Install K6 → run `api_load_test.js` → fail pipeline if thresholds breached

### Important lessons learned

- K6 uses its own Go-based runtime — not Node.js, can't import Python fixtures
- Pin Docker image versions — `latest` causes silent Playwright/browser version mismatches
- `allure serve` must not be run in CI — hangs with no browser
- Allure report must be served via HTTP — `file://` blocks JavaScript
- `pytest.ini` addopts must not contain Playwright flags
- `playwright install chromium --with-deps` required on Ubuntu CI
- `-n auto` adapts to environment — 16 workers locally, 4 in CI and Docker

---

## Testing strategy applied

- **Test pyramid** — API tests at integration layer, UI tests for critical E2E flows, performance tests for load validation
- **Shift-left** — CI runs on every PR, not just before release
- **Risk-based** — login and cart flows automated first as highest business impact
- **POM separation of concerns** — page layer owns locators, test layer owns assertions
- **BasePage inheritance** — shared behaviour defined once, inherited everywhere
- **Factory pattern** — test data centralised, tests declare intent not setup
- **Parallel execution** — xdist with function-scoped browsers, markers for fast vs slow
- **Environment config** — BASE_URL driven by env vars, no hardcoded URLs
- **Allure reporting** — interactive dashboard with severity filtering and embedded screenshots
- **Docker** — pinned base image guarantees identical environment on every machine
- **K6 thresholds** — performance regressions caught automatically in CI

---

## Author

Dharmateja Valluri — [LinkedIn](https://linkedin.com/in/) | [GitHub](https://github.com/)
