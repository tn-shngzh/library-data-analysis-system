export const ACTION_MAP = {
  'CKO': 'overview.checkout',
  'CKI': 'overview.return',
  'REH': 'overview.libraryRenewal',
  'REI': 'overview.onlineRenewal'
}

export const DEGREE_MAP = {
  '1a': 'degree.graduate',
  '1b': 'degree.bachelor',
  '1c': 'degree.college',
  '1d': 'degree.highSchool',
  '1e': 'degree.middleSchool',
  '1f': 'degree.primary',
  '1g': 'degree.temporary',
  '1h': 'degree.preschool'
}

export const STAT_CARDS_CONFIG = [
  { i18nKey: 'overview.totalFlow', key: 'total_borrows', icon: 'book-open', accent: '#d97706' },
  { i18nKey: 'overview.registeredReaders', key: 'total_readers', icon: 'users', accent: '#059669' },
  { i18nKey: 'overview.activeReaders', key: 'active_readers', icon: 'user-check', accent: '#06b6d4' },
  { i18nKey: 'overview.registeredReaders', key: 'month_active', icon: 'activity', accent: '#14b8a6' },
  { i18nKey: 'overview.borrowedBooks', key: 'avg_borrows', icon: 'trending-up', accent: '#f97316' },
  { i18nKey: 'overview.booksInLibrary', key: 'total_books', icon: 'book', accent: '#10b981' },
  { i18nKey: 'borrow.borrowRate', key: 'borrow_rate', icon: 'percent', accent: '#ec4899' },
  { i18nKey: 'book.zeroBorrow', key: 'zero_borrow', icon: 'archive', accent: '#64748b' },
  { i18nKey: 'overview.borrowedBooks', key: 'cko_count', icon: 'arrow-up', accent: '#f59e0b' },
  { i18nKey: 'overview.returnedBooks', key: 'cki_count', icon: 'arrow-down', accent: '#ef4444' },
  { i18nKey: 'overview.libraryRenewals', key: 'reh_count', icon: 'refresh', accent: '#059669' },
  { i18nKey: 'overview.onlineRenewals', key: 'rei_count', icon: 'refresh', accent: '#06b6d4' },
  { i18nKey: 'overview.todayVisits', key: 'today_visits', icon: 'wifi', accent: '#10b981' },
  { i18nKey: 'category.categoryCount', key: 'total_categories', icon: 'tag', accent: '#d97706' }
]

export const READER_STAT_CARDS = [
  { i18nKey: 'reader.totalReaders', key: 'total_readers', accent: '#d97706' },
  { i18nKey: 'reader.monthActive', key: 'month_active', accent: '#059669' },
  { i18nKey: 'reader.monthNew', key: 'month_new', accent: '#06b6d4' },
  { i18nKey: 'reader.avgBorrows', key: 'avg_borrows', accent: '#10b981' }
]

export const BOOK_STAT_CARDS = [
  { i18nKey: 'book.totalItems', key: 'total_items', accent: '#d97706' },
  { i18nKey: 'book.monthItems', key: 'month_items', accent: '#059669' },
  { i18nKey: 'book.borrowRate', key: 'borrow_rate', accent: '#06b6d4' },
  { i18nKey: 'book.zeroBorrow', key: 'zero_borrow', accent: '#ef4444' }
]

export const BORROW_STAT_CARDS = [
  { i18nKey: 'borrow.totalActions', key: 'total_actions', accent: '#d97706' },
  { i18nKey: 'borrow.totalBorrows', key: 'total_borrows', accent: '#059669' },
  { i18nKey: 'borrow.totalReturns', key: 'total_returns', accent: '#06b6d4' },
  { i18nKey: 'borrow.totalRenewals', key: 'total_renewals', accent: '#10b981' },
  { i18nKey: 'borrow.activeBorrowers', key: 'active_borrowers', accent: '#f59e0b' },
  { i18nKey: 'borrow.borrowedBooks', key: 'borrowed_books', accent: '#ef4444' }
]

export const SETTINGS_MENU = [
  { id: 'profile', i18nKey: 'settings.profile', icon: 'user' },
  { id: 'password', i18nKey: 'settings.password', icon: 'lock' },
  { id: 'security', i18nKey: 'settings.security', icon: 'shield' }
]
