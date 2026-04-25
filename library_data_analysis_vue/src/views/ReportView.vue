<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  allData: {
    type: Object,
    default: null
  }
})

const loading = ref(false)
const activeReport = ref('overview')
const reportPeriod = ref('month')
const generating = ref(false)
const generatedReport = ref(null)

const formatNumber = (num) => {
  if (!num && num !== 0) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const overviewStats = computed(() => props.allData?.overview?.stats || {})
const readerStats = computed(() => props.allData?.readers?.stats || {})
const bookStats = computed(() => props.allData?.books?.stats || {})
const borrowStats = computed(() => props.allData?.borrows?.stats || {})

const reportTypes = [
  { id: 'overview', i18nKey: 'report.typeOverview', icon: 'layout', i18nDesc: 'report.typeOverviewDesc' },
  { id: 'reader', i18nKey: 'report.typeReader', icon: 'users', i18nDesc: 'report.typeReaderDesc' },
  { id: 'book', i18nKey: 'report.typeBook', icon: 'book', i18nDesc: 'report.typeBookDesc' },
  { id: 'borrow', i18nKey: 'report.typeBorrow', icon: 'activity', i18nDesc: 'report.typeBorrowDesc' }
]

const generateReport = () => {
  generating.value = true
  setTimeout(() => {
    const s = overviewStats.value
    const rs = readerStats.value
    const bs = bookStats.value
    const bws = borrowStats.value

    generatedReport.value = {
      title: activeReport.value === 'overview' ? t('report.comprehensiveReport') :
             activeReport.value === 'reader' ? t('report.readerReport') :
             activeReport.value === 'book' ? t('report.bookReport') : t('report.borrowReport'),
      date: new Date().toLocaleDateString('zh-CN'),
      period: reportPeriod.value === 'month' ? t('report.monthly') : reportPeriod.value === 'quarter' ? t('report.quarterly') : t('report.yearly'),
      sections: activeReport.value === 'overview' ? [
        {
          title: t('report.coreIndicators'),
          items: [
            { label: t('report.totalCirculation'), value: formatNumber(s.total_borrows || 0) },
            { label: t('report.registeredReaders'), value: formatNumber(s.total_readers || 0) },
            { label: t('report.activeReaders'), value: formatNumber(s.active_readers || 0) },
            { label: t('report.collectionBooks'), value: formatNumber(s.total_books || 0) }
          ]
        },
        {
          title: t('report.borrowStatistics'),
          items: [
            { label: t('report.checkoutCount'), value: formatNumber(s.cko_count || 0) },
            { label: t('report.checkinCount'), value: formatNumber(s.cki_count || 0) },
            { label: t('report.onSiteRenewal'), value: formatNumber(s.reh_count || 0) },
            { label: t('report.onlineRenewal'), value: formatNumber(s.rei_count || 0) }
          ]
        }
      ] : activeReport.value === 'reader' ? [
        {
          title: t('report.readerOverview'),
          items: [
            { label: t('report.totalReaders'), value: formatNumber(rs.total_readers || 0) },
            { label: t('report.monthlyActive'), value: formatNumber(rs.month_active || 0) },
            { label: t('report.monthlyNew'), value: formatNumber(rs.month_new || 0) },
            { label: t('report.avgBorrows'), value: (rs.avg_borrows || 0) + ' ' + t('common.times') }
          ]
        }
      ] : activeReport.value === 'book' ? [
        {
          title: t('report.bookOverview'),
          items: [
            { label: t('report.totalCollection'), value: formatNumber(bs.total_items || 0) },
            { label: t('report.monthlyNew'), value: formatNumber(bs.month_items || 0) },
            { label: t('report.borrowRate'), value: (bs.borrow_rate || 0) + '%' },
            { label: t('report.zeroBorrow'), value: formatNumber(bs.zero_borrow || 0) }
          ]
        }
      ] : [
        {
          title: t('report.borrowOverview'),
          items: [
            { label: t('report.totalActions'), value: formatNumber(bws.total_actions || 0) },
            { label: t('report.totalCheckouts'), value: formatNumber(bws.total_borrows || 0) },
            { label: t('report.totalReturns'), value: formatNumber(bws.total_returns || 0) },
            { label: t('report.totalRenewals'), value: formatNumber(bws.total_renewals || 0) }
          ]
        }
      ]
    }
    generating.value = false
  }, 800)
}

const exportReport = (format) => {
  if (!generatedReport.value) return
  const report = generatedReport.value
  let content = `${report.title}\n`
  content += `${t('report.reportDate')}: ${report.date}\n`
  content += `${t('report.statisticsPeriod')}: ${report.period}\n\n`
  report.sections.forEach(section => {
    content += `【${section.title}】\n`
    section.items.forEach(item => {
      content += `  ${item.label}: ${item.value}\n`
    })
    content += '\n'
  })

  if (format === 'txt') {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.title}_${report.date}.txt`
    a.click()
    URL.revokeObjectURL(url)
  } else if (format === 'csv') {
    let csv = `${t('report.csvCategory')},${t('report.csvMetric')},${t('report.csvValue')}\n`
    report.sections.forEach(section => {
      section.items.forEach(item => {
        csv += `${section.title},${item.label},${item.value}\n`
      })
    })
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.title}_${report.date}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }
}

watch(() => props.allData, (data) => {
  if (data) loading.value = false
}, { immediate: true, deep: true })

onMounted(() => {
  if (props.allData) loading.value = false
})
</script>

<template>
  <div class="report-view">
    <div class="page-header">
      <div class="header-info">
        <h1>{{ t('report.title') }}</h1>
        <p>{{ t('report.desc') }}</p>
      </div>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <span>{{ t('common.loading') }}</span>
    </div>

    <template v-else>
      <div class="report-config">
        <div class="config-section">
          <h3>{{ t('report.selectReportType') }}</h3>
          <div class="report-types">
            <div
              v-for="rt in reportTypes"
              :key="rt.id"
              class="report-type-card"
              :class="{ active: activeReport === rt.id }"
              @click="activeReport = rt.id"
            >
              <div class="rt-icon">
                <svg v-if="rt.icon === 'layout'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="7" height="7"/>
                  <rect x="14" y="3" width="7" height="7"/>
                  <rect x="14" y="14" width="7" height="7"/>
                  <rect x="3" y="14" width="7" height="7"/>
                </svg>
                <svg v-else-if="rt.icon === 'users'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
                <svg v-else-if="rt.icon === 'book'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
              </div>
              <div class="rt-info">
                <span class="rt-label">{{ t(rt.i18nKey) }}</span>
                <span class="rt-desc">{{ t(rt.i18nDesc) }}</span>
              </div>
              <div class="rt-check" v-if="activeReport === rt.id">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
            </div>
          </div>
        </div>

        <div class="config-section">
          <h3>{{ t('report.statisticsPeriod') }}</h3>
          <div class="period-options">
            <button class="period-btn" :class="{ active: reportPeriod === 'month' }" @click="reportPeriod = 'month'">{{ t('report.monthly') }}</button>
            <button class="period-btn" :class="{ active: reportPeriod === 'quarter' }" @click="reportPeriod = 'quarter'">{{ t('report.quarterly') }}</button>
            <button class="period-btn" :class="{ active: reportPeriod === 'year' }" @click="reportPeriod = 'year'">{{ t('report.yearly') }}</button>
          </div>
        </div>

        <button class="generate-btn" @click="generateReport" :disabled="generating">
          <svg v-if="!generating" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
          <div v-else class="btn-spinner"></div>
          <span>{{ generating ? t('report.generating') : t('report.generateReport') }}</span>
        </button>
      </div>

      <div v-if="generatedReport" class="report-preview">
        <div class="preview-header">
          <div>
            <h2>{{ generatedReport.title }}</h2>
            <div class="preview-meta">
              <span>{{ t('report.reportDate') }}: {{ generatedReport.date }}</span>
              <span>{{ t('report.statisticsPeriod') }}: {{ generatedReport.period }}</span>
            </div>
          </div>
          <div class="export-actions">
            <button class="export-btn" @click="exportReport('csv')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              <span>{{ t('report.exportCSV') }}</span>
            </button>
            <button class="export-btn" @click="exportReport('txt')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              <span>{{ t('report.exportTXT') }}</span>
            </button>
          </div>
        </div>

        <div class="preview-body">
          <div v-for="section in generatedReport.sections" :key="section.title" class="report-section">
            <h3>{{ section.title }}</h3>
            <div class="report-items">
              <div v-for="item in section.items" :key="item.label" class="report-item">
                <span class="item-label">{{ item.label }}</span>
                <span class="item-value">{{ item.value }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-report">
        <svg viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" width="64" height="64">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <polyline points="10 9 9 9 8 9"/>
        </svg>
        <h3>{{ t('report.noReportTitle') }}</h3>
        <p>{{ t('report.noReportDesc') }}</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.report-view {
  max-width: 1200px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-info h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px 0;
}

.header-info p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px;
  color: #94a3b8;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.report-config {
  background: white;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e2e8f0;
  margin-bottom: 24px;
}

.config-section {
  margin-bottom: 24px;
}

.config-section h3 {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 14px 0;
}

.report-types {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.report-type-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.report-type-card:hover {
  border-color: #a5b4fc;
  background: #eef2ff;
}

.report-type-card.active {
  border-color: #6366f1;
  background: #eef2ff;
  box-shadow: 0 0 0 1px #6366f1;
}

.rt-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #818cf8);
  color: white;
  flex-shrink: 0;
}

.rt-icon svg {
  width: 22px;
  height: 22px;
}

.rt-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.rt-label {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.rt-desc {
  font-size: 12px;
  color: #94a3b8;
}

.rt-check {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #6366f1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.rt-check svg {
  width: 14px;
  height: 14px;
  color: white;
}

.period-options {
  display: flex;
  gap: 8px;
}

.period-btn {
  padding: 10px 24px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
}

.period-btn:hover {
  border-color: #a5b4fc;
}

.period-btn.active {
  border-color: #6366f1;
  background: #6366f1;
  color: white;
}

.generate-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #6366f1, #818cf8);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.generate-btn svg {
  width: 18px;
  height: 18px;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.report-preview {
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px;
  background: linear-gradient(135deg, #6366f1, #818cf8);
  color: white;
}

.preview-header h2 {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 8px;
}

.preview-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  opacity: 0.85;
}

.export-actions {
  display: flex;
  gap: 8px;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.export-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.export-btn svg {
  width: 16px;
  height: 16px;
}

.preview-body {
  padding: 24px;
}

.report-section {
  margin-bottom: 24px;
}

.report-section:last-child {
  margin-bottom: 0;
}

.report-section h3 {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 14px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #f1f5f9;
}

.report-items {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.report-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #f1f5f9;
}

.item-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.item-value {
  font-size: 15px;
  font-weight: 700;
  color: #6366f1;
}

.empty-report {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #94a3b8;
}

.empty-report h3 {
  font-size: 18px;
  font-weight: 600;
  color: #64748b;
  margin: 16px 0 4px;
}

.empty-report p {
  font-size: 14px;
  color: #94a3b8;
}

@media (max-width: 1024px) {
  .report-types {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .preview-header {
    flex-direction: column;
    gap: 16px;
  }

  .export-actions {
    width: 100%;
  }

  .export-btn {
    flex: 1;
    justify-content: center;
  }

  .report-items {
    grid-template-columns: 1fr;
  }
}
</style>
