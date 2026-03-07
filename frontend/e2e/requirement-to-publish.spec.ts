import { expect, test } from '@playwright/test'

test('navigates through the workbench stages', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: '仪表盘' })).toBeVisible()

  await page.goto('/intake')
  await expect(page.getByRole('heading', { name: '需求导入' })).toBeVisible()

  await page.goto('/structure')
  await expect(page.getByRole('heading', { name: '需求结构化' })).toBeVisible()

  await page.goto('/test-points')
  await expect(page.getByRole('heading', { name: '测试点设计' })).toBeVisible()

  await page.goto('/cases')
  await expect(page.getByRole('heading', { name: '测试用例工作台' })).toBeVisible()

  await page.goto('/review')
  await expect(page.getByRole('heading', { name: '覆盖分析与发布' })).toBeVisible()

  await page.goto('/knowledge')
  await expect(page.getByRole('heading', { name: '知识库管理' })).toBeVisible()

  await page.goto('/integrations')
  await expect(page.getByRole('heading', { name: '集成与导出' })).toBeVisible()
})
