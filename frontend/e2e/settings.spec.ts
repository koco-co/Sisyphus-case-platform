import { test, expect } from '@playwright/test'

test.describe('Settings Page', () => {
  test('should load settings page', async ({ page }) => {
    await page.goto('/settings')

    // 检查 URL 正确
    await expect(page).toHaveURL('/settings')
  })

  test('should display form elements', async ({ page }) => {
    await page.goto('/settings')

    // 检查表单存在
    const form = page.locator('form')
    await expect(form.first()).toBeVisible()
  })
})
