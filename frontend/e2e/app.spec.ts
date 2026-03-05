import { test, expect } from '@playwright/test'

test.describe('Application', () => {
  test.describe('Home Page', () => {
    test('should load home page', async ({ page }) => {
      await page.goto('/')

      await expect(page).toHaveURL('/')
      const title = page.locator('h1')
      await expect(title).toBeVisible()
    })

    test('should display input area on home page', async ({ page }) => {
      await page.goto('/')

      const inputArea = page.locator('textarea')
      await expect(inputArea.first()).toBeVisible()
    })

    test('should allow text input in textarea', async ({ page }) => {
      await page.goto('/')

      const textarea = page.locator('textarea').first()
      await textarea.fill('Test requirement description')

      await expect(textarea).toHaveValue('Test requirement description')
    })

    test('should have send button', async ({ page }) => {
      await page.goto('/')

      const sendButton = page.locator('button[type="submit"], button:has-text("发送")').first()
      await expect(sendButton).toBeVisible()
    })

    test('should have file upload button', async ({ page }) => {
      await page.goto('/')

      const uploadButton = page.locator('input[type="file"]')
      await expect(uploadButton.first()).toBeVisible()
    })
  })

  test.describe('Navigation', () => {
    test('should navigate to settings', async ({ page }) => {
      await page.goto('/settings')

      await expect(page).toHaveURL('/settings')
    })

    test('should navigate to test cases', async ({ page }) => {
      await page.goto('/test-cases')

      await expect(page).toHaveURL('/test-cases')
    })

    test('should navigate to requirements', async ({ page }) => {
      await page.goto('/requirements')

      await expect(page).toHaveURL('/requirements')
    })

    test('should navigate to projects', async ({ page }) => {
      await page.goto('/projects')

      await expect(page).toHaveURL('/projects')
    })
  })

  test.describe('Layout', () => {
    test('should display sidebar navigation', async ({ page }) => {
      await page.goto('/')

      const sidebar = page.locator('nav, [class*="sidebar"], [class*="sider"]').first()
      await expect(sidebar).toBeVisible()
    })
  })
})

test.describe('Settings Page', () => {
  test('should load settings page', async ({ page }) => {
    await page.goto('/settings')

    await expect(page).toHaveURL('/settings')
  })

  test('should display form elements', async ({ page }) => {
    await page.goto('/settings')

    const form = page.locator('form')
    await expect(form.first()).toBeVisible()
  })
})
