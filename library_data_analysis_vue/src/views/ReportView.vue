<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { reportApi } from '@/api/reports'

const { t } = useI18n()

const loading = ref(false)
const activeReport = ref('overview')
const llmStatus = ref({ status: 'checking' })
const aiGenerating = ref(false)
const aiReport = ref(null)
const aiReportError = ref(null)
const aiReportData = ref(null)

const reportTypes = [
  { id: 'overview', i18nKey: 'report.typeOverview', icon: 'layout' },
  { id: 'reader', i18nKey: 'report.typeReader', icon: 'users' },
  { id: 'book', i18nKey: 'report.typeBook', icon: 'book' },
  { id: 'borrow', i18nKey: 'report.typeBorrow', icon: 'activity' }
]

const checkLlmStatus = async () => {
  try {
    llmStatus.value = await reportApi.checkStatus()
  } catch {
    llmStatus.value = { status: 'offline', detail: t('report.llmCheckFailed') }
  }
}

const generateAiReport = async () => {
  if (llmStatus.value.status !== 'online') {
    aiReportError.value = t('report.llmNotStarted')
    return
  }

  aiGenerating.value = true
  aiReportError.value = null
  aiReport.value = null
  
  try {
    const generateFuncs = {
      overview: reportApi.generateOverview,
      reader: reportApi.generateReader,
      book: reportApi.generateBook,
      borrow: reportApi.generateBorrow
    }
    const result = await generateFuncs[activeReport.value]()
    aiReport.value = result.content
    aiReportData.value = result.data
  } catch (e) {
    aiReportError.value = e.message || '生成失败，请检查 LLM 服务状态'
  } finally {
    aiGenerating.value = false
  }
}

const exportExcel = () => {
  reportApi.exportExcel(activeReport.value)
}

const exportWord = () => {
  if (aiReport.value) {
    reportApi.exportWord(activeReport.value, aiReport.value)
  }
}

onMounted(async () => {
  await checkLlmStatus()
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
            </div>
            <div class="rt-check" v-if="activeReport === rt.id">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <div class="report-actions">
        <div class="llm-status" :class="llmStatus.status">
          <span class="status-dot"></span>
          <span>{{ llmStatus.detail }}</span>
        </div>
        <button 
          class="btn btn-primary btn-lg" 
          @click="generateAiReport" 
          :disabled="aiGenerating || llmStatus.status !== 'online'"
        >
          <svg v-if="!aiGenerating" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/>
            <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/>
          </svg>
          <div v-else class="btn-spinner"></div>
          {{ aiGenerating ? t('report.generating') : t('report.generateAiReport') }}
        </button>
      </div>
    </div>

    <div v-if="aiReportError" class="ai-error">
      {{ aiReportError }}
    </div>

    <div v-if="aiReport" class="ai-report-content">
      <div class="ai-report-header">
        <span>{{ t('report.reportType') }}：{{ reportTypes.find(r => r.id === activeReport)?.i18nKey ? t(reportTypes.find(r => r.id === activeReport)?.i18nKey) : activeReport }}</span>
        <div class="export-actions">
          <button class="btn btn-ghost" @click="exportExcel">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            {{ t('report.exportExcel') }}
          </button>
          <button class="btn btn-ghost" @click="exportWord">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            {{ t('report.exportWord') }}
          </button>
        </div>
      </div>
      <div class="ai-report-text">{{ aiReport }}</div>
    </div>

    <div v-else-if="!aiGenerating" class="ai-empty">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="64" height="64">
        <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/>
        <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/>
      </svg>
      <h3>{{ t('report.aiReportTitle') }}</h3>
      <p>{{ t('report.aiReportDesc') }}</p>
    </div>

    <div v-if="aiGenerating" class="ai-loading">
      <div class="loading-spinner"></div>
      <span>{{ t('report.aiAnalyzing') }}</span>
    </div>
  </div>
</template>

<style scoped>
.report-view {
  max-width: 900px;
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-height) - 48px);
  overflow-y: auto;
  gap: var(--space-4);
}

.page-header {
  flex-shrink: 0;
}

.header-info h1 {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-neutral-900);
  margin: 0 0 var(--space-1) 0;
}

.header-info p {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  margin: 0;
}

.report-config {
  background: var(--chart-bg);
  border-radius: var(--radius-xl);
  padding: var(--space-4) var(--space-5);
  border: 1px solid var(--color-neutral-200);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.03);
  flex-shrink: 0;
}

.config-section {
  margin-bottom: var(--space-4);
}

.config-section h3 {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
  margin: 0 0 var(--space-3) 0;
}

.report-types {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-3);
}

.report-type-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--color-neutral-50);
  border: 2px solid var(--color-neutral-200);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.report-type-card:hover {
  border-color: var(--color-primary-400);
}

.report-type-card.active {
  border-color: var(--color-primary-500);
  background: var(--color-primary-50);
}

.rt-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-primary);
  color: white;
  flex-shrink: 0;
}

.rt-icon svg {
  width: 20px;
  height: 20px;
}

.rt-info {
  flex: 1;
}

.rt-label {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
}

.rt-check {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-primary-500);
  display: flex;
  align-items: center;
  justify-content: center;
}

.rt-check svg {
  width: 12px;
  height: 12px;
  color: white;
}

.report-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
}

.llm-status {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}

.llm-status .status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.llm-status.online {
  background: var(--color-success-50);
  color: var(--color-success-600);
}

.llm-status.online .status-dot {
  background: var(--color-success-500);
}

.llm-status.offline {
  background: var(--color-danger-50);
  color: var(--color-danger-600);
}

.llm-status.offline .status-dot {
  background: var(--color-danger-500);
}

.ai-error {
  padding: var(--space-3) var(--space-4);
  background: var(--color-danger-50);
  color: var(--color-danger-600);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
}

.ai-report-content {
  background: var(--chart-bg);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-neutral-200);
  overflow: hidden;
  flex: 1;
  min-height: 0;
}

.ai-report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  background: var(--color-neutral-50);
  border-bottom: 1px solid var(--color-neutral-200);
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
}

.export-actions {
  display: flex;
  gap: var(--space-2);
}

.ai-report-text {
  padding: var(--space-4) var(--space-5);
  font-size: var(--text-sm);
  line-height: 1.8;
  color: var(--color-neutral-700);
  white-space: pre-wrap;
}

.ai-empty, .ai-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-4);
  background: var(--chart-bg);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-neutral-200);
  text-align: center;
  color: var(--color-neutral-400);
  flex: 1;
  min-height: 0;
}

.ai-empty svg, .ai-loading svg {
  margin-bottom: var(--space-4);
  color: var(--color-primary-500);
}

.ai-empty h3 {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-500);
  margin: 0 0 var(--space-2);
}

.ai-empty p {
  font-size: var(--text-sm);
  color: var(--color-neutral-400);
  margin: 0;
  max-width: 400px;
}

.ai-loading {
  color: var(--color-neutral-500);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-neutral-200);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: var(--space-3);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@media (max-width: 768px) {
  .report-types {
    grid-template-columns: 1fr;
  }

  .report-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>