# Library User Borrowing Behavior Analysis System

## Version

**v0.27.2** - Full UI optimization, unified ChartCard component, heatmap refinement, prediction improvements

## Changelog

### v0.27.2 (2026-05-17) - UI Optimization & ChartCard Unification
- Removed signal-card component entirely, unified to ChartCard with `stats` prop for inline metrics
- All pages now use flex layout with `calc(100vh - header)` to fill viewport, eliminating bottom whitespace
- Heatmap: 1-hour granularity (was 2-hour), 9-level blue color scale, 6-22h time range, filtered out "unknown" degree
- Prediction chart: smooth connection between historical and predicted curves, removed model comparison feature
- Unified design tokens across TrendView, AnalysisView, IntelligenceView, ReportView
- Deleted `signal-card.css` global stylesheet
- Updated system design document to v0.27.0

### v0.27.0 (2026-05-17) - Backend Optimization & New Modules
- New backend modules: statistics analysis, intelligence analysis, AI report generation
- Optimized `historical-stats` API from 24.5s to ~100ms by using `monthly_history_cache` table
- Added `degree_hour_cache` table for heatmap data, regenerated with 6-22h data
- Fixed PostgreSQL modulo operator (`%` → `mod()`) for historical stats queries
- Added `book_categories(bib_id)` index for query performance
- LLM integration service with configurable API endpoint

### v0.26.0 (2026-05-17) - Historical Analysis Upgrade
- New HistoricalAnalysisView with yearly trend, yearly comparison (radar chart), monthly detail
- Fixed 2022 data anomaly by regenerating `monthly_history_cache` from `circulations` table
- Year-over-year comparison using YoY change rate dimensions for better differentiation
- Historical detail API with monthly breakdown (borrows/returns/active readers)

### v0.25.0 (2026-05-12) - Cleanup
- Removed temporary scripts and debug files

### v0.24.0 (2026-05-12) - Repository Cleanup
- Deleted dpo-data-generator directory

### v0.23.0 (2026-05-03) - Login Fix
- Fixed LoginView to use parsed API data instead of raw Response

### v0.22.0 (2026-05-03) - Port Configuration
- Changed backend port from 8001 to 8000
- Updated frontend proxy configuration

### v0.21.0 (2026-05-03) - Data Flow Fix
- Fixed overview card display property names
- Completed i18n translations
- Fixed API data flow issues

### v0.20.0 (2026-05-03) - New Analysis Modules
- Added data analysis module (AnalysisView)
- Added data import module (ImportView)
- Added intelligent insights module (InsightsPanel)

### v0.19.0 (2026-05-03) - Component Fix
- Removed non-existent component references (AnalysisView/ImportView/InsightsPanel)

### v0.18.0 (2026-05-02) - Script Cleanup
- Deleted test scripts and data analysis scripts

### v0.17.0 (2026-05-02) - Security Cleanup
- Removed sensitive information and test script files

### v0.16.0 (2026-04-30) - Authentication & UI Fix
- Fixed CAPTCHA functionality
- Fixed architecture issues
- Modernized button styles

### v0.15.0 (2026-04-28) - Security & i18n
- Fixed system security vulnerabilities
- Fixed data interfaces
- Restructured i18n architecture

### v0.14.0 (2026-04-25) - Update
- System updates

### v0.13.0 (2026-04-22) - Backend Modular Architecture
- Refactored backend into modular architecture (11 router modules, 61 API endpoints)
- Fixed frontend data mapping and chart rendering
- Added LLM service, export service

### v0.12.0 (2026-04-21) - System Upgrade
- Overall system upgrade and optimization

### v0.11.0 (2026-04-21) - Code Reorganization
- Tidied code and reorganized structure

### v0.10.0 (2026-04-20) - Borrowing API Fixes
- Fixed `/api/borrows/my` SQL query error
- Fixed `/api/borrows/borrow` and `/api/borrows/return` SQL errors
- Corrected borrowers table field name query

### v0.9.0 (2026-04-20) - Security Fix
- Fixed admin password storage (plaintext → bcrypt 12-round encryption)

### v0.8.0 (2026-04-20) - Standalone Settings Page
- Added SettingsView with profile, password, security modules

### v0.7.0 (2026-04-20) - User Registration
- Added user registration with bcrypt encryption
- Implemented borrowing system UI

### v0.6.0 (2026-04-20) - Data Preloading
- Added data preloading for sub-second page switching
- Removed unused columns and scripts

### v0.5.0 (2026-04-19) - Dashboard & Performance
- Added four core dashboard pages
- Introduced materialized views for query performance

### v0.4.0 (2026-04-19) - Login Verification
- Added CAPTCHA verification
- Optimized login page style

### v0.3.0 (2026-04-19) - JWT Authentication
- Implemented JWT authentication with RBAC
- Admin/user permission separation

### v0.2.0 (2026-04-19) - Architecture Refactoring
- Frontend-backend separation (FastAPI + Vue 3)
- Poetry dependency management

### v0.1.0 (2026-04-18) - Initial Release
- Project initialization

## Features

- JWT login authentication with CAPTCHA
- Role-based access control (admin/user)
- User registration with bcrypt encryption
- Dual-system design (Borrowing System + Data Analysis System)
- 102,237 user account management
- 8,420,000+ circulation record analysis
- Data preloading with sub-second response
- Multi-dimensional data analysis (Overview, Readers, Books, Borrows, Categories)
- Historical analysis with yearly trend and comparison
- Intelligent prediction with multiple models
- Statistical analysis (frequency, descriptive, crosstab, clustering)
- AI-powered report generation (LLM integration)
- Data import (CSV upload)
- Excel/Word report export
- i18n support (Simplified Chinese, Traditional Chinese, English, Japanese)
- Unified ChartCard component with inline stats
- Responsive layout filling viewport

## Project Structure

- `library_data_analysis_fastapi/` - FastAPI backend (11 router modules, 61 API endpoints)
- `library_data_analysis_vue/` - Vue 3 frontend
- `data/` - Exported CSV datasets
- `docs/` - System design documentation

## Getting Started

### Quick Start
```bash
start.bat
```

### Backend
```bash
cd library_data_analysis_fastapi
pip install poetry
poetry install
poetry run uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd library_data_analysis_vue
npm install
npm run dev
```

## Default Accounts

- Admin: `admin` / `admin123` (data analysis system)
- Regular user: Register a new account (borrowing system)
- Test user: `user` / `user123` (borrowing system)

## API (61 Endpoints)

### Authentication `/api`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/captcha` | Get CAPTCHA |
| POST | `/api/login` | User login |
| POST | `/api/register` | User registration |
| GET | `/api/me` | Current user info |
| POST | `/api/logout` | Logout |

### Overview `/api/overview`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/stats` | Core metrics |
| GET | `/historical-stats` | Historical statistics |
| GET | `/historical-detail` | Monthly detail |
| GET | `/recent-books` | Recent borrows |
| GET | `/top-books` | Top books |
| GET | `/book-categories` | Category stats |
| GET | `/monthly-borrows` | Monthly trend |
| GET | `/trend-7d` | 7-day trend |
| GET | `/collection-health` | Collection health |
| GET | `/reader-activity-heatmap` | Activity heatmap |

### Readers `/api/readers`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/stats` | Reader statistics |
| GET | `/types` | Degree distribution |
| GET | `/monthly-trend` | Monthly trend |
| GET | `/top` | Top readers |
| GET | `/degree-stats` | Degree stats |
| GET | `/degree-hour-heatmap` | Degree-hour heatmap |
| GET | `/frequency-distribution` | Frequency distribution |

### Books `/api/books`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/stats` | Book statistics |
| GET | `/categories` | Category stats |
| GET | `/hot` | Hot books |
| GET | `/search` | Book search |
| GET | `/categories-list` | Category list |

### Borrows `/api/borrows`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/stats` | Borrow statistics |
| GET | `/action-stats` | Action type stats |
| GET | `/degree-stats` | Degree-borrow stats |
| GET | `/daily-trend` | Daily trend |
| GET | `/top-borrowers` | Top borrowers |
| GET | `/top-books` | Top books |
| GET | `/recent` | Recent borrows |
| GET | `/monthly-trend` | Monthly borrows |
| GET | `/monthly-returns` | Monthly returns |

### Analysis `/api/analysis`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/correlation` | Correlation analysis |
| GET | `/period-comparison` | Period comparison |
| GET | `/category-heatmap` | Category heatmap |
| GET | `/degree-monthly-trend` | Degree monthly trend |
| GET | `/daily-trend` | Daily trend |
| GET | `/category-period-comparison` | Category period comparison |

### Statistics `/api/stats`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/frequency` | Frequency analysis |
| GET | `/descriptive` | Descriptive statistics |
| GET | `/crosstab` | Cross-tabulation |
| GET | `/correlation-matrix` | Correlation matrix |
| GET | `/clustering/reader` | Reader clustering |
| GET | `/regression/forecast` | Regression forecast |

### Intelligence `/api/intelligence`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/correlation` | Book correlation |
| GET | `/collection-optimization` | Collection optimization |

### Reports `/api/reports`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/status` | LLM service status |
| GET | `/overview\|reader\|book\|borrow` | AI-generated reports |
| GET | `/export/excel/{type}` | Export Excel |
| GET | `/export/word` | Export Word |

### Other
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/insights/auto` | Auto insights |
| POST | `/api/imports/upload` | CSV upload |
| GET | `/api/imports/history` | Import history |
| POST | `/api/imports/validate` | CSV validation |
