import { expect, mock, test } from 'bun:test';
import { renderToStaticMarkup } from 'react-dom/server';

mock.module('next/link', () => ({
  default: ({
    href,
    children,
    ...props
  }: {
    href: string;
    children: React.ReactNode;
    [key: string]: unknown;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

mock.module('next/navigation', () => ({
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

mock.module('next-themes', () => ({
  useTheme: () => ({
    theme: 'dark',
    resolvedTheme: 'dark',
    setTheme: () => {},
  }),
}));

mock.module('@/components/ui/GlobalSearch', () => ({
  GlobalSearch: () => <div>GlobalSearch</div>,
  SearchTrigger: () => <button type="button">SearchTrigger</button>,
}));

mock.module('@/components/ui/ProgressDashboard', () => ({
  default: () => <div>ProgressDashboard</div>,
}));

mock.module('@/components/ui/UserMenu', () => ({
  UserMenu: () => <div>UserMenu</div>,
}));

test('main layout renders onboarding guide entry after page content', async () => {
  const module = await import('./layout');
  const MainLayout = module.default;

  const html = renderToStaticMarkup(
    <MainLayout>
      <div>child-content</div>
    </MainLayout>,
  );

  expect(html.indexOf('child-content') < html.indexOf('aria-label="帮助与引导"')).toBe(true);
});
