import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import zhTW from './locales/zh-TW'
import en from './locales/en'
import ja from './locales/ja'

const savedLocale = localStorage.getItem('locale') || 'zh-CN'

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'zh-TW': zhTW,
    'en': en,
    'ja': ja
  }
})

export default i18n

export const SUPPORTED_LOCALES = [
  { code: 'zh-CN', name: '简体中文', nativeName: 'Simplified Chinese', flag: '🇨🇳' },
  { code: 'zh-TW', name: '繁體中文', nativeName: 'Traditional Chinese', flag: '🇹🇼' },
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
  { code: 'ja', name: '日本語', nativeName: 'Japanese', flag: '🇯🇵' }
]

export function setLocale(code: string) {
  i18n.global.locale.value = code
  localStorage.setItem('locale', code)
  document.documentElement.setAttribute('lang', code)
}
