import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type AnalysisView = 'borrow' | 'reader'
export type DateRange = { start: string; end: string }

export const useAnalysisStore = defineStore('analysis', () => {
  const globalDateRange = ref<DateRange>({ start: '', end: '' })

  const setDateRange = (range: DateRange) => {
    globalDateRange.value = range
  }

  const granularity = computed(() => {
    const { start, end } = globalDateRange.value
    if (!start || !end) return 'month'
    const diff = (new Date(end).getTime() - new Date(start).getTime()) / (1000 * 60 * 60 * 24)
    if (diff <= 30) return 'day'
    if (diff <= 180) return 'week'
    return 'month'
  })

  const normalizeDateRange = (range: DateRange): DateRange => {
    const diff = (new Date(range.end).getTime() - new Date(range.start).getTime()) / (1000 * 60 * 60 * 24)
    if (diff < 7) {
      const endDate = new Date(range.start)
      endDate.setDate(endDate.getDate() + 6)
      return { start: range.start, end: endDate.toISOString().slice(0, 10) }
    }
    return range
  }

  return { globalDateRange, setDateRange, granularity, normalizeDateRange }
})