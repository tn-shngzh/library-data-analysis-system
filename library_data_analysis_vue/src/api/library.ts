import { get, post } from './index'

export const libraryApi = {
  getHomeData: async () => {
    const [statsRes, hotRes, recentRes, catRes] = await Promise.all([
      get('/api/borrows/stats'),
      get('/api/books/hot'),
      get('/api/borrows/recent'),
      get('/api/books/categories')
    ])

    const result = {}
    if (statsRes.ok) result.stats = await statsRes.json()
    if (hotRes.ok) result.hotBooks = await hotRes.json()
    if (recentRes.ok) result.recentBorrows = await recentRes.json()
    if (catRes.ok) result.categories = await catRes.json()
    return result
  },

  getMyBorrows: () => get('/api/borrows/my'),

  borrowBook: (bookId) => post('/api/borrows/borrow', JSON.stringify({ book_id: bookId })),
  returnBook: (bookId) => post('/api/borrows/return', JSON.stringify({ book_id: bookId })),
  renewBook: (bookId) => post('/api/borrows/renew', JSON.stringify({ book_id: bookId }))
}
