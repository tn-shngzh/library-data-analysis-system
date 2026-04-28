export type SupportedLocale = 'zh-CN' | 'zh-TW' | 'en' | 'ja'

export interface LocaleConfig {
  code: SupportedLocale
  name: string
  nativeName: string
  flag: string
}

export const LOCALE_CONFIG: LocaleConfig[] = [
  { code: 'zh-CN', name: '简体中文', nativeName: 'Simplified Chinese', flag: '🇨🇳' },
  { code: 'zh-TW', name: '繁體中文', nativeName: 'Traditional Chinese', flag: '🇹🇼' },
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
  { code: 'ja', name: '日本語', nativeName: 'Japanese', flag: '🇯🇵' },
]

export type MessageSchema = {
  nav: Record<string, string | Record<string, string>>
  common: Record<string, string | Record<string, string>>
  overview: Record<string, string | Record<string, string>>
  months: Record<string, string | Record<string, string>>
  degree: Record<string, string | Record<string, string>>
  reader: Record<string, string | Record<string, string>>
  book: Record<string, string | Record<string, string>>
  borrow: Record<string, string | Record<string, string>>
  category: Record<string, string | Record<string, string>>
  trend: Record<string, string | Record<string, string>>
  predict: Record<string, string | Record<string, string>>
  report: Record<string, string | Record<string, string>>
  settings: Record<string, string | Record<string, string>>
  login: Record<string, string | Record<string, string>>
  register: Record<string, string | Record<string, string>>
  library: Record<string, string | Record<string, string>>
}
