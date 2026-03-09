'use client';
import { ConfigProvider, App, theme as antdTheme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

export function AntdProvider({ children }: { children: React.ReactNode }) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const isDark = !mounted || resolvedTheme === 'dark';

  const themeConfig = {
    algorithm: isDark ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
    token: {
      colorPrimary: '#00d9a3',
      colorBgBase: isDark ? '#0d0f12' : '#f8fafc',
      colorTextBase: isDark ? '#e2e8f0' : '#1e293b',
      colorBorder: isDark ? '#2a313d' : '#e2e8f0',
      colorBgContainer: isDark ? '#131619' : '#ffffff',
      colorBgElevated: isDark ? '#1a1e24' : '#f1f5f9',
      borderRadius: 8,
      fontFamily: "'DM Sans', sans-serif",
    },
    components: {
      Table: { colorBgContainer: isDark ? '#131619' : '#ffffff' },
      Modal: { contentBg: isDark ? '#131619' : '#ffffff' },
      Drawer: { colorBgElevated: isDark ? '#131619' : '#ffffff' },
    },
  };

  return (
    <ConfigProvider theme={themeConfig} locale={zhCN}>
      <App>{children}</App>
    </ConfigProvider>
  );
}
