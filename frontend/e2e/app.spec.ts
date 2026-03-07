import { expect, test } from '@playwright/test'

test.describe('Workbench routes', () => {
  test('loads dashboard', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: '仪表盘' })).toBeVisible()
  })

  test('loads intake page', async ({ page }) => {
    await page.goto('/intake')
    await expect(page.getByRole('heading', { name: '需求导入' })).toBeVisible()
  })

  test('loads structure page', async ({ page }) => {
    await page.goto('/structure')
    await expect(page.getByRole('heading', { name: '需求结构化' })).toBeVisible()
  })

  test('loads test point page', async ({ page }) => {
    await page.goto('/test-points')
    await expect(page.getByRole('heading', { name: '测试点设计' })).toBeVisible()
  })

  test('loads case workbench page', async ({ page }) => {
    await page.goto('/cases')
    await expect(page.getByRole('heading', { name: '测试用例工作台' })).toBeVisible()
  })

  test('loads review page', async ({ page }) => {
    await page.goto('/review')
    await expect(page.getByRole('heading', { name: '覆盖分析与发布' })).toBeVisible()
  })

  test('loads knowledge page', async ({ page }) => {
    await page.goto('/knowledge')
    await expect(page.getByRole('heading', { name: '知识库管理' })).toBeVisible()
  })

  test('loads integrations page', async ({ page }) => {
    await page.goto('/integrations')
    await expect(page.getByRole('heading', { name: '集成与导出' })).toBeVisible()
  })
})
