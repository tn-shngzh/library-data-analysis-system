# Library User Borrowing Behavior Analysis System

## Version

**v0.10.0** - Borrowing feature improvements, system stability enhancements, standalone settings page

## Changelog

### v0.10.0 (2026-04-20) - Borrowing API Fixes & Data Improvements
- Fixed `/api/borrows/my` SQL query error, resolving blank page issue
- Fixed `/api/borrows/borrow` SQL query error, ensuring borrowing works correctly
- Fixed `/api/borrows/return` SQL query error, ensuring return works correctly
- Corrected borrowers table field name query (`WHERE username = %s` → `WHERE name = %s`)
- Created corresponding borrowers record for admin account (id: 102236)

### v0.9.0 (2026-04-20) - Security Fix & Password Encryption
- Fixed admin password storage (from plaintext `admin123` to bcrypt 12-round encryption)
- Used `bcrypt.hashpw()` for password hashing, following security best practices
- Verified login endpoint `/api/login` password verification logic with bcrypt
- Updated README default account notes, marking password as encrypted

### v0.8.0 (2026-04-20) - Standalone Settings Page
- Added `SettingsView.vue` standalone settings page with three modules: Profile, Change Password, Security Settings
- Dedicated sidebar navigation with menu items: Personal Info, Change Password, Security Settings
- Removed settings tab from `LibraryView.vue`
- Added route configuration `/settings` for standalone access
- Improved navigation: user menu now includes "User Settings" option, quick links to My Books and Hot Books
- Optimized UI design: replaced card-based layout with modern panel layout
- Added real-time clock display, updating every minute

### v0.7.0 (2026-04-20) - User Registration & Borrowing System UI
- Added user registration feature with online account creation (`/api/register`)
- Optimized password encryption using bcrypt directly (12-round encryption)
- Implemented borrowing system UI with consistent sidebar navigation style
- Improved input validation (username 3-20 chars, password 6-50 chars)
- Implemented user ID auto-increment mechanism
- Removed passlib, added python-multipart

### v0.6.0 (2026-04-20) - Data Preloading & Architecture Simplification
- Added data preloading, automatically fetching all data on system entry
- Removed branch-related features and data columns, simplifying architecture
- Cleaned up unused `imported_at` column from database
- Exported complete dataset to CSV format (9.8M+ records)
- Optimized page switching experience with sub-second response
- Updated version to 0.6.0

### v0.5.0 (2026-04-19) - Dashboard & Performance Optimization
- Added four core dashboard pages (Overview, Readers, Books, Borrows)
- Implemented tab navigation for quick switching
- Introduced materialized views for query performance (~1000x improvement)
- Achieved millisecond-level response speed
- Enhanced data visualization with multi-dimensional analysis

### v0.4.0 (2026-04-19) - Login Verification
- Added CAPTCHA verification for improved security
- Optimized login page style with modern design
- Enhanced user experience with error prompts and feedback
- Implemented one-time CAPTCHA usage mechanism

### v0.3.0 (2026-04-19) - JWT Authentication
- Implemented JWT authentication mechanism
- Introduced role-based access control (RBAC)
- Implemented admin/user permission separation
- Added login guards for route protection
- Token validity management (7 days)

### v0.2.0 (2026-04-19) - Architecture Refactoring
- Implemented frontend-backend separation architecture
- Adopted FastAPI as backend framework
- Used Vue 3 for frontend interface
- Introduced Poetry for dependency management
- Restructured codebase for improved maintainability

### v0.1.0 (2026-04-18) - Initial Release
- Project initialization complete
- Set up basic project structure
- Configured development environment and toolchain
- Wrote project documentation

## Features

- JWT login authentication
- Role-based access control (admin/user)
- User registration
- Dual-system design (Borrowing System + Data Analysis System)
- Admin access to data analysis system
- Regular user access to borrowing system
- 102,237 user account management
- 6,232,387 circulation record analysis
- Data preloading with sub-second response
- Multi-dimensional data analysis (Overview, Readers, Books, Borrows)
- i18n support (Simplified Chinese, Traditional Chinese, English, Japanese)

## Project Structure

- `library_data_analysis_fastapi/` - FastAPI backend
- `library_data_analysis_vue/` - Vue 3 frontend
- `data/` - Exported CSV datasets

## Getting Started

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

- Admin: `admin` / `admin123` (login to data analysis system)
- Regular user: Register a new account (login to borrowing system)
- Test user: `user` / `user123` (borrowing system)

## API

### Authentication
- `GET /api/captcha` - Get CAPTCHA
- `POST /api/login` - User login
- `POST /api/register` - User registration
- `GET /api/me` - Get current user info

### Overview
- `GET /api/overview/stats` - Overview statistics
- `GET /api/overview/categories` - Category statistics
- `GET /api/overview/recent-books` - Recent borrowing records

### Readers
- `GET /api/readers/stats` - Reader statistics
- `GET /api/readers/types` - Reader type distribution
- `GET /api/readers/monthly-trend` - Monthly registration trend
- `GET /api/readers/top` - Top active readers

### Books
- `GET /api/books/stats` - Book statistics
- `GET /api/books/categories` - Book category statistics
- `GET /api/books/hot` - Hot books ranking

### Borrows
- `GET /api/borrows/stats` - Borrowing statistics
- `GET /api/borrows/action-stats` - Circulation type statistics
- `GET /api/borrows/degree-stats` - Reader education distribution
- `GET /api/borrows/daily-trend` - Daily borrowing trend
- `GET /api/borrows/top-borrowers` - Top borrowers ranking
- `GET /api/borrows/top-books` - Top borrowed books
- `GET /api/borrows/recent` - Recent borrowing records
