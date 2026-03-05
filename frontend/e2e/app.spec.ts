import { test, expect } from '@playwright/test'

test.describe('Application', () => {
  test('should load home page', async ({ page }) => {
    await page.goto('/')

    // 检查页面加载成功
    await expect(page).toHaveURL('/')

    // 检查标题存在
    const title = page.locator('h1')
    await expect(title).toBeVisible()
  })

  test('should navigate to settings', async ({ page }) => {
    await page.goto('/settings')

    // 检查 URL 正确
    await expect(page).toHaveURL('/settings')
  })

  test('should display input area on home page', async ({ page }) => {
    await page.goto('/')

    // 检查输入区域存在
    const inputArea = page.locator('textarea')
    await expect(inputArea.first()).toBeVisible()
  })
})
