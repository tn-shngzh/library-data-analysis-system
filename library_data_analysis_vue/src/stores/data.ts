import { defineStore } from 'pinia'
import { overviewApi } from '@/api/overview'
import { readerApi } from '@/api/readers'
import { bookApi } from '@/api/books'
import { borrowApi } from '@/api/borrows'

export const useDataStore = defineStore('data', {
  state: () => ({
    loaded: false,
    overview: { stats: null, categories: null, recentBooks: null },
    readers: { stats: null, readerTypes: null, monthlyTrend: null, topReaders: null },
    books: { stats: null, categories: null, hotBooks: null },
    borrows: { stats: null, actionStats: null, degreeStats: null, topBorrowers: null, topBooks: null, recentBorrows: null }
  }),
  actions: {
    async preloadAll() {
      const loadModule = async (apiGetAll, dataKey, mappings) => {
        try {
          const result = await apiGetAll()
          for (const [resultKey, targetKey] of mappings) {
            if (result[resultKey]) this[targetKey][resultKey] = result[resultKey]
          }
        } catch (e) {
          console.error(`预加载${dataKey}数据失败`, e)
        }
      }

      await Promise.all([
        loadModule(overviewApi.getAll, 'overview', [
          ['stats', 'overview'],
          ['categories', 'overview'],
          ['recentBooks', 'overview']
        ]),
        loadModule(readerApi.getAll, 'readers', [
          ['stats', 'readers'],
          ['readerTypes', 'readers'],
          ['monthlyTrend', 'readers'],
          ['topReaders', 'readers']
        ]),
        loadModule(bookApi.getAll, 'books', [
          ['stats', 'books'],
          ['categories', 'books'],
          ['hotBooks', 'books']
        ]),
        loadModule(borrowApi.getAll, 'borrows', [
          ['stats', 'borrows'],
          ['actionStats', 'borrows'],
          ['degreeStats', 'borrows'],
          ['topBorrowers', 'borrows'],
          ['topBooks', 'borrows'],
          ['recentBorrows', 'borrows']
        ])
      ])

      this.loaded = true
    },
    async refreshModule(moduleName) {
      const moduleConfigs = {
        overview: { api: overviewApi.getAll, mappings: [['stats', 'overview'], ['categories', 'overview'], ['recentBooks', 'overview']] },
        readers: { api: readerApi.getAll, mappings: [['stats', 'readers'], ['readerTypes', 'readers'], ['monthlyTrend', 'readers'], ['topReaders', 'readers']] },
        books: { api: bookApi.getAll, mappings: [['stats', 'books'], ['categories', 'books'], ['hotBooks', 'books']] },
        borrows: { api: borrowApi.getAll, mappings: [['stats', 'borrows'], ['actionStats', 'borrows'], ['degreeStats', 'borrows'], ['topBorrowers', 'borrows'], ['topBooks', 'borrows'], ['recentBorrows', 'borrows']] }
      }

      const config = moduleConfigs[moduleName]
      if (!config) return

      try {
        const result = await config.api()
        for (const [resultKey, targetKey] of config.mappings) {
          if (result[resultKey]) this[targetKey][resultKey] = result[resultKey]
        }
      } catch (e) {
        console.error(`刷新${moduleName}数据失败`, e)
      }
    }
  }
})
