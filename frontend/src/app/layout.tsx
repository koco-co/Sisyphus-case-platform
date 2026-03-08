import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Sisyphus Case Platform',
  description: 'AI 驱动的企业级测试用例生成平台',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
