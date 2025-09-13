import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');

  // Expect a title to contain Ghostworks
  await expect(page).toHaveTitle(/Ghostworks/);
});

test('navigation links work', async ({ page }) => {
  await page.goto('/');

  // Test navigation to tour page
  await page.getByRole('link', { name: 'Take the Tour' }).click();
  await expect(
    page.getByRole('heading', { name: 'Platform Tour' })
  ).toBeVisible();

  // Test navigation to dashboard (use header navigation specifically)
  await page.getByRole('navigation').getByRole('link', { name: 'Dashboard' }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

  // Test navigation to artifacts (use header navigation specifically)
  await page.getByRole('navigation').getByRole('link', { name: 'Artifacts' }).click();
  await expect(page.getByRole('heading', { name: 'Artifacts' })).toBeVisible();
});

test('authentication pages load', async ({ page }) => {
  await page.goto('/');

  // Test login page
  await page.getByRole('link', { name: 'Sign in' }).click();
  await expect(
    page.getByRole('heading', { name: 'Sign in to your account' })
  ).toBeVisible();

  // Test register page
  await page.goto('/');
  await page.getByRole('link', { name: 'Sign up' }).click();
  await expect(
    page.getByRole('heading', { name: 'Create your account' })
  ).toBeVisible();
});
