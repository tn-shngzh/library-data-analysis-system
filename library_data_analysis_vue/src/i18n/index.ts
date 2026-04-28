import { createI18n } from 'vue-i18n'
import type { SupportedLocale } from './types'
import { LOCALE_CONFIG } from './types'
import zhCN from './locales/zh-CN'

const savedLocale = (localStorage.getItem('locale') || 'zh-CN') as SupportedLocale

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN
  }
})

const loadedLocales: Set<SupportedLocale> = new Set(['zh-CN'])

const localeModules: Record<string, () => Promise<{ default: Record<string, unknown> }>> = {
  'zh-TW': () => import('./locales/zh-TW'),
  'en': () => import('./locales/en'),
  'ja': () => import('./locales/ja')
}

export async function loadLocaleMessages(locale: SupportedLocale): Promise<void> {
  if (loadedLocales.has(locale)) return

  const loader = localeModules[locale]
  if (!loader) return

  const module = await loader()
  i18n.global.setLocaleMessage(locale, module.default as Record<string, unknown>)
  loadedLocales.add(locale)
}

export async function setLocale(code: SupportedLocale): Promise<void> {
  await loadLocaleMessages(code)
  i18n.global.locale.value = code
  localStorage.setItem('locale', code)
  document.documentElement.setAttribute('lang', code)
}

export const SUPPORTED_LOCALES = LOCALE_CONFIG

if (savedLocale !== 'zh-CN') {
  loadLocaleMessages(savedLocale)
}

export default i18n
