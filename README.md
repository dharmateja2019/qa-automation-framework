# QA Automation Framework

![CI](https://github.com/dharmateja2019/qa-automation-framework/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.13-blue)
![Playwright](https://img.shields.io/badge/playwright-1.58.0-green)
![K6](https://img.shields.io/badge/k6-performance-orange)
![Docker](https://img.shields.io/badge/docker-containerised-blue)
![Allure](https://img.shields.io/badge/allure-reporting-yellow)

A production-style test automation framework covering API testing, UI automation, and performance testing — built with real-world SDET patterns: Page Object Model, Factory pattern, parallel execution, Docker containerisation, and a three-job CI/CD pipeline.

---

## What this framework covers

| Layer               | Tool             | Target                                   |
| ------------------- | ---------------- | ---------------------------------------- |
| API testing         | httpx + pytest   | JSONPlaceholder REST API                 |
| UI automation       | Playwright + POM | SauceDemo e-commerce app                 |
| Performance testing | K6 + thresholds  | JSONPlaceholder under load               |
| Reporting           | Allure           | Interactive dashboard with screenshots   |
| CI/CD               | GitHub Actions   | Three parallel jobs on every push and PR |
| Environment         | Docker           | Pinned image, identical on every machine |

---

## Architecture overview

```
qa-automation-framework/
│
├── config/                        # Shared env config across all layers
│   ├── __init__.py
│   └── config.py                  # BASE_URL, API_URL, timeouts via env vars
│
├── conftest.py                    # Root fixtures — shared by API and UI tests
│
├── api_tests/                     # API layer — httpx + pytest
│   ├── __init__.py
│   └── test_api.py
│
├── ui_tests/                      # UI layer — Playwright + POM
│   ├── core/
│   │   ├── __init__.py
│   │   └── base_page.py           # Shared page behaviour (waits, nav, screenshots)
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── login_page.py
│   │   └── inventory_page.py
│   ├── test_data/
│   │   ├── __init__.py
│   │   ├── user_factory.py
│   │   └── product_factory.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── login_test.py
│       ├── test_inventory.py
│       └── test_fixture_scopes.py
│
├── performance/
│   └── api_load_test.js           # K6 — mirrors functional API tests
│
├── Dockerfile                     # Playwright base image v1.58.0-noble (pinned)
├── pytest.ini
├── requirements.txt               # Unified dependency file
├── README.md
└── ARCHITECTURE.md
```

Full architecture diagrams — component view, CI flow, class hierarchy, Docker flow, K6 ramp flow — are in [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## Quick start

### Prerequisites

- Python 3.12+ (tested on 3.13.3)
- Node.js (for K6 — install from [k6.io](https://k6.io/docs/get-started/installation/))
- Docker (optional, for containerised runs)

### Install

```bash
git clone https://github.com/dharmateja2019/qa-automation-framework.git
cd qa-automation-framework
pip install -r requirements.txt
playwright install chromium
```

---

## How to run

### API tests

```bash
pytest api_tests/test_api.py -v
```

### UI tests

```bash
# Sequential
pytest ui_tests/tests/ -v --browser chromium

# Parallel (recommended)
pytest ui_tests/tests/ -v --browser chromium -n auto

# With Allure report
pytest ui_tests/tests/ -v --browser chromium -n 2 --alluredir=allure-results
allure serve allure-results
```

### Performance tests

```bash
k6 run performance/api_load_test.js
```

### By marker

```bash
pytest -n auto -m "not slow"   # fast tests only, in parallel
pytest -m "slow"               # slow tests sequentially
```

---

## Docker

```bash
# Build
docker build -t qa-automation .

# Run (default — UI tests)
docker run qa-automation

# Run with Allure results exported to host
docker run -v $(pwd)/allure-results:/app/allure-results qa-automation
```

---

## Configuration

All configuration is environment-variable driven. No hardcoding.

| Variable   | Default                                | Purpose         |
| ---------- | -------------------------------------- | --------------- |
| `BASE_URL` | `https://www.saucedemo.com`            | UI test target  |
| `API_URL`  | `https://jsonplaceholder.typicode.com` | API test target |

| `TIMEOUT` | `30000` | Element wait timeout in ms |

### Override for different environments

```bash
# Staging
BASE_URL=https://staging.example.com pytest ui_tests/tests/ -v --browser chromium

# Docker with staging
docker run -e BASE_URL=https://staging.example.com qa-automation
```

Same test code runs across local, staging, and production — no commits required to switch environments.

---

## Viewing Allure reports from CI

1. Go to **Actions** → select a run → **Artifacts** → download `allure-report`
2. Unzip the archive
3. Run: `allure open allure-report/`

> Do not open `index.html` directly — the `file://` protocol blocks Allure's JavaScript. Always use `allure open` or `python3 -m http.server`.

---

## CI pipeline

Three jobs run in parallel on every push and pull request:

```
git push / pull request
        │
        ├── api-tests ──────────► api-report.html   (artifact)
        │   httpx + pytest
        │
        ├── ui-tests ───────────► allure-report/     (artifact)
        │   Playwright + xdist + Allure
        │
        └── performance-tests ──► pass / fail
            K6 + thresholds
```

Separate jobs mean a flaky UI test does not hide a passing API suite. Each job installs only what it needs.

---

## Test results

### API — JSONPlaceholder (`pytest api_tests/test_api.py -v`)

14 tests, 14 passed in 17.75s on macOS / Python 3.13.3

| Test                             | Parametrized cases                              | Result     |
| -------------------------------- | ----------------------------------------------- | ---------- |
| `test_get_post_status`           | IDs 1, 50, 100 → 200 OK; IDs 101, 99999 → 404   | ✓ 5 passed |
| `test_post_schema_is_consistent` | IDs 1, 25, 50, 75, 100 — field presence + types | ✓ 5 passed |
| `test_create_post_variations`    | 4 payload variations → 201 Created              | ✓ 4 passed |

### UI — SauceDemo (`pytest ui_tests/tests/ -v --browser chromium -n 2`)

12 tests, 12 passed in 23.70s — 2 workers, parallel execution

| File                     | Tests                                                      | Result     |
| ------------------------ | ---------------------------------------------------------- | ---------- |
| `login_test.py`          | valid login, invalid password, empty username, locked user | ✓ 4 passed |
| `test_fixture_scopes.py` | scope isolation, cart state, add to cart                   | ✓ 4 passed |
| `test_inventory.py`      | product count (6), names not empty, cart badge update      | ✓ 3 passed |

### Performance — JSONPlaceholder (`k6 run performance/api_load_test.js`)

10 VUs, 40s run, 169 complete iterations, 338 total requests — all thresholds met

| Metric            | Result             | Threshold | Status |
| ----------------- | ------------------ | --------- | ------ |
| GET /posts — p95  | 67ms               | < 400ms   | ✓ Pass |
| POST /posts — p95 | 326ms              | < 600ms   | ✓ Pass |
| Failure rate      | 0.00%              | < 1%      | ✓ Pass |
| Checks passed     | 1014 / 1014 (100%) | —         | ✓ Pass |

**K6 check breakdown:** status 200 ✓, has `id` field ✓, has `title` field ✓, response under 400ms ✓, status 201 ✓, title matches ✓

---

## Parallel execution timing

| Mode       | Workers | Time | Environment          |
| ---------- | ------- | ---- | -------------------- |
| Sequential | 1       | ~30s | Local Mac            |
| `-n 2`     | 2       | ~24s | Local Mac (measured) |
| `-n auto`  | 16      | ~13s | Local Mac            |
| `-n auto`  | 4       | ~12s | GitHub Actions       |
| `-n auto`  | 4       | ~19s | Docker               |

At 500 tests this difference scales from ~35 minutes sequential to under 8 minutes parallel.

---

## Testing strategy

| Principle          | How it's applied                                                       |
| ------------------ | ---------------------------------------------------------------------- |
| Test pyramid       | More API tests at integration layer, UI only for critical E2E flows    |
| Shift-left         | CI runs on every PR — not just before release                          |
| Risk-based         | Login and cart flows first — highest business impact                   |
| POM                | Page layer owns locators, test layer owns assertions only              |
| BasePage           | Shared behaviour (waits, navigation, screenshots) inherited everywhere |
| Factory pattern    | Test data centralised — tests declare intent, not setup detail         |
| Parallel execution | xdist with function-scoped browser fixtures for isolation              |
| Environment config | BASE_URL via env vars — same code for all environments                 |
| Allure             | Interactive reports with severity labels and embedded screenshots      |
| Docker             | Pinned image — identical environment on every machine                  |
| K6 thresholds      | Performance regressions caught automatically in CI                     |

---

## Key lessons learned

- Pin Docker image versions — `latest` causes silent Playwright/browser version mismatches
- `pytest.ini` addopts must not contain Playwright flags — breaks non-Playwright jobs
- `playwright install chromium --with-deps` is required on Ubuntu CI (not just `chromium`)
- `allure serve` must not run in CI — it starts a web server with no browser to open it
- Session scope does not cross xdist worker process boundaries — use function scope for browser fixtures
- `-n auto` adapts to the machine: 16 workers locally, 4 in CI and Docker

---

## Contributing

1. Fork the repo and create a branch: `git checkout -b feature/your-change`
2. Make your changes and add tests where relevant
3. Run the full suite locally before pushing: `pytest -n auto --browser chromium`
4. Open a pull request — CI will run all three jobs automatically
5. For bugs or suggestions, open an [issue](https://github.com/dharmateja2019/qa-automation-framework/issues)

---

## Support

- Open an [issue](https://github.com/dharmateja2019/qa-automation-framework/issues) for bugs or questions
- See [ARCHITECTURE.md](./ARCHITECTURE.md) for design decisions and trade-offs

---

## Author

Dharmateja Valluri — [LinkedIn](https://linkedin.com/in/dharmateja-valluri) | [GitHub](https://github.com/dharmateja2019)

---

## License

MIT
