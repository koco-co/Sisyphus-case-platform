import type { Metadata } from 'next';
import { ThemeProvider } from '@/components/providers/ThemeProvider';
import { AntdProvider } from '@/components/providers/AntdProvider';
import { QueryProvider } from '@/components/providers/QueryProvider';
import './globals.css';

export const metadata: Metadata = { title: 'Sisyphus · 智能测试用例平台' };

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <QueryProvider>
            <AntdProvider>{children}</AntdProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
