import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Thesis → Ticker Engine',
  description: 'Turn weekly macro/investing lessons into tradable playbook cards',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html>
      <body>{children}</body>
    </html>
  )
}
