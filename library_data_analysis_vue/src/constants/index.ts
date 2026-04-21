export const ACTION_MAP = {
  'CKO': '借出',
  'CKI': '归还',
  'REH': '到馆续借',
  'REI': '网上续借'
}

export const DEGREE_MAP = {
  '1a': '研究生',
  '1b': '本科',
  '1c': '大专',
  '1d': '高中',
  '1e': '初中',
  '1f': '小学',
  '1g': '临时',
  '1h': '学龄前'
}

export const STAT_CARDS_CONFIG = [
  { label: '总流通量', key: 'total_borrows', icon: 'book-open', accent: '#6366f1' },
  { label: '注册读者', key: 'total_readers', icon: 'users', accent: '#8b5cf6' },
  { label: '活跃读者', key: 'active_readers', icon: 'user-check', accent: '#06b6d4' },
  { label: '月活跃读者', key: 'month_active', icon: 'activity', accent: '#14b8a6' },
  { label: '人均借阅', key: 'avg_borrows', icon: 'trending-up', accent: '#f97316' },
  { label: '流通图书', key: 'total_books', icon: 'book', accent: '#10b981' },
  { label: '图书流通率', key: 'borrow_rate', icon: 'percent', accent: '#ec4899' },
  { label: '零借阅图书', key: 'zero_borrow', icon: 'archive', accent: '#64748b' },
  { label: '常规借书', key: 'cko_count', icon: 'arrow-up', accent: '#f59e0b' },
  { label: '归还', key: 'cki_count', icon: 'arrow-down', accent: '#ef4444' },
  { label: '到馆续借', key: 'reh_count', icon: 'refresh', accent: '#8b5cf6' },
  { label: '网上续借', key: 'rei_count', icon: 'refresh', accent: '#06b6d4' },
  { label: '今日到馆', key: 'today_visits', icon: 'wifi', accent: '#10b981' },
  { label: '图书分类', key: 'total_categories', icon: 'tag', accent: '#6366f1' }
]

export const READER_STAT_CARDS = [
  { label: '总读者数', key: 'total_readers', accent: '#6366f1' },
  { label: '月活跃', key: 'month_active', accent: '#8b5cf6' },
  { label: '月新增', key: 'month_new', accent: '#06b6d4' },
  { label: '人均借阅', key: 'avg_borrows', accent: '#10b981' }
]

export const BOOK_STAT_CARDS = [
  { label: '馆藏总量', key: 'total_items', accent: '#6366f1' },
  { label: '本月入库', key: 'month_items', accent: '#8b5cf6' },
  { label: '流通率', key: 'borrow_rate', accent: '#06b6d4' },
  { label: '零借阅', key: 'zero_borrow', accent: '#ef4444' }
]

export const BORROW_STAT_CARDS = [
  { label: '总操作数', key: 'total_actions', accent: '#6366f1' },
  { label: '总借出', key: 'total_borrows', accent: '#8b5cf6' },
  { label: '总归还', key: 'total_returns', accent: '#06b6d4' },
  { label: '总续借', key: 'total_renewals', accent: '#10b981' },
  { label: '活跃借阅者', key: 'active_borrowers', accent: '#f59e0b' },
  { label: '在借图书', key: 'borrowed_books', accent: '#ef4444' }
]

export const SETTINGS_MENU = [
  { id: 'profile', label: '个人信息', icon: 'user' },
  { id: 'password', label: '修改密码', icon: 'lock' },
  { id: 'security', label: '安全设置', icon: 'shield' }
]
