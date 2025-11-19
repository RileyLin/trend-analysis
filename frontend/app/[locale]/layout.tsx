import Link from 'next/link'
import { Locale, t } from '@/lib/translations'

export default function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: { locale: Locale }
}) {
  const locale = params.locale

  return (
    <html lang={locale}>
      <body>
        <div className="min-h-screen bg-gray-50">
          {/* Navigation */}
          <nav className="border-b border-gray-200 bg-white">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <div className="flex h-16 justify-between">
                <div className="flex">
                  <div className="flex flex-shrink-0 items-center">
                    <h1 className="text-xl font-bold text-primary-600">
                      Thesis → Ticker
                    </h1>
                  </div>
                  <div className="ml-10 flex space-x-8">
                    <Link
                      href={`/${locale}/ingest`}
                      className="inline-flex items-center border-b-2 border-transparent px-1 pt-1 text-sm font-medium text-gray-900 hover:border-gray-300"
                    >
                      {t(locale, 'nav.ingest')}
                    </Link>
                    <Link
                      href={`/${locale}/playbook`}
                      className="inline-flex items-center border-b-2 border-transparent px-1 pt-1 text-sm font-medium text-gray-900 hover:border-gray-300"
                    >
                      {t(locale, 'nav.playbook')}
                    </Link>
                    <Link
                      href={`/${locale}/alerts`}
                      className="inline-flex items-center border-b-2 border-transparent px-1 pt-1 text-sm font-medium text-gray-900 hover:border-gray-300"
                    >
                      {t(locale, 'nav.alerts')}
                    </Link>
                    <Link
                      href={`/${locale}/scoreboard`}
                      className="inline-flex items-center border-b-2 border-transparent px-1 pt-1 text-sm font-medium text-gray-900 hover:border-gray-300"
                    >
                      {t(locale, 'nav.scoreboard')}
                    </Link>
                  </div>
                </div>

                {/* Language switcher */}
                <div className="flex items-center">
                  <Link
                    href={locale === 'en-US' ? '/zh-CN' : '/en-US'}
                    className="text-sm text-gray-500 hover:text-gray-900"
                  >
                    {locale === 'en-US' ? '中文' : 'English'}
                  </Link>
                </div>
              </div>
            </div>
          </nav>

          {/* Main content */}
          <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
