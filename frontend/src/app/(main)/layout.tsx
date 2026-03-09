'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { SidebarItem, SidebarSection } from '@/components/ui';

type NavLink = { href: string; icon: string; label: string };
type NavSection = { section: string };
type NavItem = NavLink | NavSection;

const navItems: NavItem[] = [
  { href: '/', icon: '🏠', label: '项目总览' },
  { section: '测试流程' },
  { href: '/requirements', icon: '📄', label: '需求管理' },
  { href: '/diagnosis', icon: '🩺', label: '健康诊断' },
  { href: '/scene-map', icon: '🌳', label: '测试点确认' },
  { href: '/workbench', icon: '⚡', label: '生成工作台' },
  { href: '/testcases', icon: '📋', label: '用例管理' },
  { section: '分析' },
  { href: '/analytics', icon: '📊', label: '质量看板' },
  { href: '/knowledge', icon: '🧠', label: '知识库' },
];

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen">
      <aside className="w-[220px] bg-bg1 border-r border-border min-h-screen fixed top-0 left-0 flex flex-col">
        <div className="p-4 border-b border-border">
          <div className="font-display font-bold text-[15px] text-accent tracking-wide">TestGen Pro</div>
        </div>
        <nav className="flex-1 py-4 overflow-y-auto">
          {navItems.map((item, i) =>
            'section' in item ? (
              <SidebarSection key={item.section} label={item.section}>{null}</SidebarSection>
            ) : (
              <div key={item.href} className="px-3">
                <Link href={item.href}>
                  <SidebarItem
                    icon={item.icon}
                    label={item.label}
                    active={pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href))}
                  />
                </Link>
              </div>
            )
          )}
        </nav>
      </aside>
      <main className="ml-[220px] flex-1 min-h-screen bg-bg">
        {children}
      </main>
    </div>
  );
}
