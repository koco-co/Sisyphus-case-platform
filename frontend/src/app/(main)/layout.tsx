'use client';
import {
  BookOpen,
  ClipboardList,
  FolderSearch,
  GitCompareArrows,
  LayoutDashboard,
  LayoutTemplate,
  Monitor,
  Moon,
  Settings,
  Sun,
  Trash2,
  Wand2,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { GlobalSearch, SearchTrigger } from '@/components/ui/GlobalSearch';
import { NotificationBell } from '@/components/ui/NotificationBell';
import { OnboardingGuideButton } from '@/components/ui/OnboardingGuide';
import ProgressDashboard from '@/components/ui/ProgressDashboard';
import { UserMenu } from '@/components/ui/UserMenu';

const navGroups = [
  {
    items: [
      { href: '/', label: '仪表盘', icon: LayoutDashboard },
      { href: '/analysis', label: '分析台', icon: FolderSearch },
      { href: '/workbench', label: '工作台', icon: Wand2 },
      { href: '/diff', label: '需求Diff', icon: GitCompareArrows },
      { href: '/testcases', label: '用例库', icon: ClipboardList },
    ],
  },
  {
    items: [
      { href: '/templates', label: '模板库', icon: LayoutTemplate },
      { href: '/knowledge', label: '知识库', icon: BookOpen },
      { href: '/recycle', label: '回收站', icon: Trash2 },
      { href: '/settings', label: '设置', icon: Settings },
    ],
  },
];

function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!mounted) return <div className="theme-toggle" />;

  const cycleTheme = () => {
    if (theme === 'dark') setTheme('light');
    else if (theme === 'light') setTheme('system');
    else setTheme('dark');
  };

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={cycleTheme}
      aria-label={`切换主题，当前: ${theme === 'system' ? '跟随系统' : theme === 'dark' ? '深色' : '浅色'}`}
      title={`当前: ${theme === 'system' ? '跟随系统' : theme === 'dark' ? '深色' : '浅色'}`}
    >
      {resolvedTheme === 'dark' ? <Moon /> : theme === 'system' ? <Monitor /> : <Sun />}
    </button>
  );
}

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <>
      <nav className="top-nav" aria-label="主导航">
        <span className="nav-title">Sisyphus</span>
        <span className="pill pill-green" style={{ marginRight: 8, fontSize: 10 }}>
          v2.0
        </span>

        {navGroups.map((group, gi) => {
          const groupKey = group.items[0].href;
          const items = group.items.map((t) => {
            const Icon = t.icon;
            const isActive =
              t.href === '/'
                ? pathname === '/'
                : t.href === '/analysis'
                  ? pathname.startsWith('/analysis') ||
                    pathname.startsWith('/diagnosis') ||
                    pathname.startsWith('/scene-map') ||
                    pathname.startsWith('/requirements') ||
                    pathname.startsWith('/coverage')
                  : pathname === t.href || pathname.startsWith(`${t.href}/`);
            return (
              <Link key={t.href} href={t.href} className={`tab${isActive ? ' active' : ''}`}>
                <Icon />
                {t.label}
              </Link>
            );
          });

          if (gi === 0) return items;
          return [
            <span
              key={`divider-${groupKey}`}
              style={{
                width: 1,
                height: 20,
                background: 'var(--border)',
                margin: '0 4px',
                flexShrink: 0,
              }}
            />,
            ...items,
          ];
        })}

        <div className="nav-actions">
          <SearchTrigger />
          <ThemeToggle />
          <NotificationBell />
          <UserMenu />
        </div>
      </nav>
      {children}
      <OnboardingGuideButton />
      <ProgressDashboard />
      <GlobalSearch />
    </>
  );
}
