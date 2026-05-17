import { defineStore } from 'pinia'
import { overviewApi } from '@/api/overview'
import { readerApi } from '@/api/readers'
import { bookApi } from '@/api/books'
import { borrowApi } from '@/api/borrows'

export const useDataStore = defineStore('data', {
  state: () => ({
    loaded: false,
    overview: { stats: null, historicalStats: null, categories: null, recentBooks: null, monthlyBorrows: null, trend7d: null, collectionHealth: null, readerActivityHeatmap: null },
    readers: { stats: null, readerTypes: null, monthlyTrend: null, topReaders: null, degreeStats: null, degreeHourHeatmap: null, frequencyDistribution: null },
    books: { stats: null, categories: null, hotBooks: null },
    borrows: { stats: null, actionStats: null, degreeStats: null, topBorrowers: null, topBooks: null, recentBorrows: null, monthlyBorrows: null, monthlyReturns: null }
  }),
  actions: {
    async preloadAll() {
      const loadModule = async (apiGetAll, dataKey, mappings) => {
        try {
          const result = await apiGetAll()
          for (const [resultKey, targetKey] of mappings) {
            if (result[resultKey] !== undefined && result[resultKey] !== null && this[targetKey]) {
              this[targetKey][resultKey] = result[resultKey]
            }
          }
        } catch (e) {
          console.error(`预加载${dataKey}数据失败`, e)
        }
      }

      await Promise.all([
        loadModule(overviewApi.getAll, 'overview', [
          ['stats', 'overview'],
          ['historicalStats', 'overview'],
          ['categories', 'overview'],
          ['recentBooks', 'overview'],
          ['monthlyBorrows', 'overview'],
          ['trend7d', 'overview'],
          ['collectionHealth', 'overview'],
          ['readerActivityHeatmap', 'overview']
        ]),
        loadModule(readerApi.getAll, 'readers', [
          ['stats', 'readers'],
          ['readerTypes', 'readers'],
          ['monthlyTrend', 'readers'],
          ['topReaders', 'readers'],
          ['degreeStats', 'readers'],
          ['degreeHourHeatmap', 'readers'],
          ['frequencyDistribution', 'readers']
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
          ['recentBorrows', 'borrows'],
          ['monthlyBorrows', 'borrows'],
          ['monthlyReturns', 'borrows']
        ])
      ])

      this.loaded = true
    },
    async refreshModule(moduleName) {
      const moduleConfigs = {
        overview: { api: overviewApi.getAll, mappings: [['stats', 'overview'], ['historicalStats', 'overview'], ['categories', 'overview'], ['recentBooks', 'overview'], ['monthlyBorrows', 'overview'], ['trend7d', 'overview'], ['collectionHealth', 'overview'], ['readerActivityHeatmap', 'overview']] },
        readers: { api: readerApi.getAll, mappings: [['stats', 'readers'], ['readerTypes', 'readers'], ['monthlyTrend', 'readers'], ['topReaders', 'readers'], ['degreeStats', 'readers'], ['degreeHourHeatmap', 'readers'], ['frequencyDistribution', 'readers']] },
        books: { api: bookApi.getAll, mappings: [['stats', 'books'], ['categories', 'books'], ['hotBooks', 'books']] },
        borrows: { api: borrowApi.getAll, mappings: [['stats', 'borrows'], ['actionStats', 'borrows'], ['degreeStats', 'borrows'], ['topBorrowers', 'borrows'], ['topBooks', 'borrows'], ['recentBorrows', 'borrows'], ['monthlyBorrows', 'borrows'], ['monthlyReturns', 'borrows']] }
      }

      const config = moduleConfigs[moduleName]
      if (!config) return

      try {
        const result = await config.api()
        for (const [resultKey, targetKey] of config.mappings) {
          if (result[resultKey] !== undefined && result[resultKey] !== null && this[targetKey]) {
            this[targetKey][resultKey] = result[resultKey]
          }
        }
      } catch (e) {
        console.error(`刷新${moduleName}数据失败`, e)
      }
    }
  }
})
