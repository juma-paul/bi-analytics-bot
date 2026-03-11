'use client'

import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Sidebar from '@/components/layout/Sidebar'
import { useAppStore } from '@/store/app'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
})

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const sidebarOpen = useAppStore((state) => state.sidebarOpen)

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className={`${inter.className} bg-white text-text-primary`}>
        <div className="flex h-screen overflow-hidden bg-bg-primary">
          {/* Sidebar */}
          <Sidebar />

          {/* Main Content */}
          <main className="flex-1 overflow-auto">
            <div className="min-h-screen">{children}</div>
          </main>
        </div>
      </body>
    </html>
  )
}
