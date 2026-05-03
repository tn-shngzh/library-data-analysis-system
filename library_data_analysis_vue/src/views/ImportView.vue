<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { importsApi } from '@/api/imports'
import { formatNumber } from '@/utils/format'
import PageHeader from '@/components/PageHeader.vue'

const { t } = useI18n()

const selectedFile = ref(null)
const isDragging = ref(false)
const uploading = ref(false)
const validating = ref(false)
const validationResult = ref(null)
const uploadResult = ref(null)
const importHistory = ref([])
const historyLoading = ref(false)

const onFileSelect = (e) => {
  const input = e.target
  if (input.files && input.files[0]) {
    selectedFile.value = input.files[0]
    validationResult.value = null
    uploadResult.value = null
  }
}

const onDrop = (e) => {
  isDragging.value = false
  if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
    selectedFile.value = e.dataTransfer.files[0]
    validationResult.value = null
    uploadResult.value = null
  }
}

const onDragOver = () => { isDragging.value = true }
const onDragLeave = () => { isDragging.value = false }

const validateFile = async () => {
  if (!selectedFile.value) return
  validating.value = true
  validationResult.value = null
  try {
    const data = await importsApi.validate(selectedFile.value)
    validationResult.value = data
  } catch (e) {
    validationResult.value = { valid: false, error: e.message || t('import.validateFailed') }
  } finally {
    validating.value = false
  }
}

const uploadFile = async () => {
  if (!selectedFile.value) return
  uploading.value = true
  uploadResult.value = null
  try {
    const data = await importsApi.upload(selectedFile.value)
    uploadResult.value = data
    fetchHistory()
  } catch (e) {
    uploadResult.value = { success: false, error: e.message || t('import.uploadFailed') }
  } finally {
    uploading.value = false
  }
}

const fetchHistory = async () => {
  historyLoading.value = true
  try {
    const data = await importsApi.getHistory()
    if (data && data.imports) importHistory.value = data.imports
  } catch (e) {
    console.error('Failed to fetch import history', e)
  } finally {
    historyLoading.value = false
  }
}

const formatTime = (t) => {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchHistory()
})
</script>

<template>
  <div class="import-view">
    <PageHeader :title="t('import.title')" :description="t('import.desc')" />

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          <span class="title-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </span>
          {{ t('import.uploadTitle') }}
        </h3>
      </div>

      <div class="upload-zone" :class="{ dragging: isDragging }" @drop.prevent="onDrop" @dragover.prevent="onDragOver" @dragleave="onDragLeave" @click="($refs.fileInput).click()">
        <input ref="fileInput" type="file" accept=".csv" class="file-input" @change="onFileSelect" />
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="upload-icon">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        <div class="upload-text">{{ selectedFile ? selectedFile.name : t('import.dropHint') }}</div>
        <div class="upload-sub">{{ t('import.formatHint') }}</div>
      </div>

      <div class="upload-actions">
        <button class="btn btn-secondary" :disabled="!selectedFile || validating" @click="validateFile">
          <span v-if="validating" class="spinner"></span>
          {{ validating ? t('import.validating') : t('import.validate') }}
        </button>
        <button class="btn btn-primary" :disabled="!selectedFile || uploading" @click="uploadFile">
          <span v-if="uploading" class="spinner"></span>
          {{ uploading ? t('import.importing') : t('import.import') }}
        </button>
      </div>

      <div v-if="validationResult" class="result-section" :class="{ 'result-success': validationResult.valid, 'result-error': !validationResult.valid }">
        <div class="result-header">{{ t('import.validateResult') }}</div>
        <div class="result-stats">
          <span>{{ t('import.totalRows') }}: <strong>{{ validationResult.total_rows }}</strong></span>
          <span>{{ t('import.validRows') }}: <strong>{{ validationResult.valid_rows }}</strong></span>
          <span v-if="validationResult.errors">{{ t('import.errorRows') }}: <strong>{{ validationResult.errors.length }}</strong></span>
        </div>
        <div v-if="validationResult.errors && validationResult.errors.length" class="error-list">
          <div v-for="err in validationResult.errors.slice(0, 10)" :key="err.row" class="error-item">
            {{ t('import.row') }} {{ err.row }}: {{ err.message }}
          </div>
          <div v-if="validationResult.errors.length > 10" class="error-more">
            {{ t('import.moreErrors', { count: validationResult.errors.length - 10 }) }}
          </div>
        </div>
      </div>

      <div v-if="uploadResult" class="result-section" :class="{ 'result-success': uploadResult.success, 'result-error': !uploadResult.success }">
        <div class="result-header">{{ t('import.importResult') }}</div>
        <div v-if="uploadResult.success" class="result-stats">
          <span>{{ t('import.imported') }}: <strong>{{ formatNumber(uploadResult.imported) }}</strong></span>
          <span>{{ t('import.skipped') }}: <strong>{{ uploadResult.skipped }}</strong></span>
          <span v-if="uploadResult.errors && uploadResult.errors.length">{{ t('import.errorRows') }}: <strong>{{ uploadResult.errors.length }}</strong></span>
        </div>
        <div v-else class="result-stats">
          <span>{{ uploadResult.error || t('import.uploadFailed') }}</span>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          <span class="title-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </span>
          {{ t('import.history') }}
        </h3>
      </div>
      <div v-if="historyLoading" class="loading-text">{{ t('common.loading') }}</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>{{ t('import.filename') }}</th>
            <th>{{ t('import.imported') }}</th>
            <th>{{ t('import.skipped') }}</th>
            <th>{{ t('import.errorCount') }}</th>
            <th>{{ t('import.importTime') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in importHistory" :key="item.id" class="table-row">
            <td>{{ item.filename }}</td>
            <td class="count-cell">{{ formatNumber(item.imported_count) }}</td>
            <td class="count-cell">{{ item.skipped_count }}</td>
            <td class="count-cell" :class="{ 'text-danger': item.error_count > 0 }">{{ item.error_count }}</td>
            <td>{{ formatTime(item.import_time) }}</td>
          </tr>
          <tr v-if="importHistory.length === 0" class="empty-row">
            <td colspan="5">{{ t('common.noData') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.import-view { padding: 0; }

.card { background: var(--color-bg-primary, #fff); border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.card-header { display: flex; align-items: center; margin-bottom: 16px; }
.card-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; color: var(--color-text-primary, #1e293b); margin: 0; }
.title-icon { display: flex; align-items: center; width: 20px; height: 20px; color: var(--chart-primary, #3b82f6); }

.upload-zone { border: 2px dashed var(--color-border, #e2e8f0); border-radius: 12px; padding: 40px 20px; text-align: center; cursor: pointer; transition: all 0.2s; background: var(--color-bg-secondary, #f8fafc); }
.upload-zone:hover, .upload-zone.dragging { border-color: var(--chart-primary, #3b82f6); background: rgba(59,130,246,0.04); }
.file-input { display: none; }
.upload-icon { width: 48px; height: 48px; color: var(--color-text-tertiary, #94a3b8); margin-bottom: 12px; }
.upload-text { font-size: 15px; color: var(--color-text-primary, #1e293b); font-weight: 500; margin-bottom: 4px; }
.upload-sub { font-size: 12px; color: var(--color-text-tertiary, #94a3b8); }

.upload-actions { display: flex; gap: 12px; margin-top: 16px; }
.btn { padding: 10px 24px; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 8px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: var(--chart-primary, #3b82f6); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--chart-primary-light, #60a5fa); }
.btn-secondary { background: var(--color-bg-secondary, #f1f5f9); color: var(--color-text-primary, #1e293b); }
.btn-secondary:hover:not(:disabled) { background: var(--color-border, #e2e8f0); }
.spinner { width: 14px; height: 14px; border: 2px solid transparent; border-top-color: currentColor; border-radius: 50%; animation: spin 0.6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.result-section { margin-top: 16px; padding: 16px; border-radius: 10px; border: 1px solid var(--color-border, #e2e8f0); }
.result-success { background: rgba(16,185,129,0.06); border-color: rgba(16,185,129,0.2); }
.result-error { background: rgba(239,68,68,0.06); border-color: rgba(239,68,68,0.2); }
.result-header { font-size: 14px; font-weight: 600; margin-bottom: 8px; color: var(--color-text-primary, #1e293b); }
.result-stats { display: flex; gap: 16px; font-size: 13px; color: var(--color-text-secondary, #64748b); flex-wrap: wrap; }
.result-stats strong { color: var(--color-text-primary, #1e293b); }
.error-list { margin-top: 8px; }
.error-item { font-size: 12px; color: var(--chart-danger, #ef4444); padding: 2px 0; }
.error-more { font-size: 12px; color: var(--color-text-tertiary, #94a3b8); margin-top: 4px; }

.data-table { width: 100%; border-collapse: collapse; }
.data-table th { padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 600; color: var(--color-text-secondary, #64748b); text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid var(--color-border, #e2e8f0); }
.data-table td { padding: 10px 12px; font-size: 14px; color: var(--color-text-primary, #1e293b); border-bottom: 1px solid var(--color-border, #f1f5f9); }
.table-row { animation: fadeInRow 0.3s ease both; }
@keyframes fadeInRow { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.empty-row td { text-align: center; color: var(--color-text-tertiary, #94a3b8); padding: 24px; }
.count-cell { font-variant-numeric: tabular-nums; font-weight: 500; }
.text-danger { color: var(--chart-danger, #ef4444); }
.loading-text { text-align: center; padding: 24px; color: var(--color-text-tertiary, #94a3b8); }
</style>
