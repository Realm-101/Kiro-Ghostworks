import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Start from the home page
    await page.goto('/');
  });

  test('user can register a new account', async ({ page }) => {
    // Navigate to registration page
    await page.getByRole('link', { name: 'Sign up' }).click();
    await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible();

    // Fill out registration form
    const timestamp = Date.now();
    const email = `test-${timestamp}@example.com`;
    
    await page.getByLabel('Email address').fill(email);
    await page.getByLabel('First name').fill('Test');
    await page.getByLabel('Last name').fill('User');
    await page.getByLabel('Password', { exact: true }).fill('TestPassword123!');
    await page.getByLabel('Confirm password').fill('TestPassword123!');

    // Submit registration form
    await page.getByRole('button', { name: 'Create account' }).click();

    // Should redirect to verification page or dashboard
    await expect(page).toHaveURL(/\/(verify|dashboard)/);
    
    // Check for success message or verification notice
    await expect(
      page.getByText(/account created|verification|welcome/i)
    ).toBeVisible();
  });

  test('user can login with valid credentials', async ({ page }) => {
    // First register a user (in a real test, this would use a test user)
    await page.goto('/register');
    
    const timestamp = Date.now();
    const email = `login-test-${timestamp}@example.com`;
    const password = 'TestPassword123!';
    
    // Register user
    await page.getByLabel('Email address').fill(email);
    await page.getByLabel('First name').fill('Login');
    await page.getByLabel('Last name').fill('Test');
    await page.getByLabel('Password', { exact: true }).fill(password);
    await page.getByLabel('Confirm password').fill(password);
    await page.getByRole('button', { name: 'Create account' }).click();

    // Wait for registration to complete
    await page.waitForURL(/\/(verify|dashboard)/);

    // Navigate to login page
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible();

    // Fill out login form
    await page.getByLabel('Email address').fill(email);
    await page.getByLabel('Password').fill(password);

    // Submit login form
    await page.getByRole('button', { name: 'Sign in' }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('user cannot login with invalid credentials', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');

    // Try to login with invalid credentials
    await page.getByLabel('Email address').fill('invalid@example.com');
    await page.getByLabel('Password').fill('WrongPassword123!');
    await page.getByRole('button', { name: 'Sign in' }).click();

    // Should show error message
    await expect(page.getByText(/invalid.*email.*password/i)).toBeVisible();
    
    // Should remain on login page
    await expect(page).toHaveURL('/login');
  });

  test('registration form validates password requirements', async ({ page }) => {
    await page.goto('/register');

    // Fill form with weak password
    await page.getByLabel('Email address').fill('test@example.com');
    await page.getByLabel('First name').fill('Test');
    await page.getByLabel('Last name').fill('User');
    await page.getByLabel('Password', { exact: true }).fill('weak');
    await page.getByLabel('Confirm password').fill('weak');

    // Try to submit
    await page.getByRole('button', { name: 'Create account' }).click();

    // Should show password validation errors
    await expect(
      page.getByText(/password.*must.*contain/i)
    ).toBeVisible();
  });

  test('registration form validates password confirmation', async ({ page }) => {
    await page.goto('/register');

    // Fill form with mismatched passwords
    await page.getByLabel('Email address').fill('test@example.com');
    await page.getByLabel('First name').fill('Test');
    await page.getByLabel('Last name').fill('User');
    await page.getByLabel('Password', { exact: true }).fill('TestPassword123!');
    await page.getByLabel('Confirm password').fill('DifferentPassword123!');

    // Try to submit
    await page.getByRole('button', { name: 'Create account' }).click();

    // Should show password mismatch error
    await expect(
      page.getByText(/passwords.*do not match/i)
    ).toBeVisible();
  });

  test('user can logout', async ({ page }) => {
    // First login (using a simplified approach for testing)
    await page.goto('/login');
    
    // Mock successful login by setting localStorage/cookies
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock-token');
      localStorage.setItem('user_data', JSON.stringify({
        id: 'test-user-id',
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User'
      }));
    });

    // Navigate to dashboard
    await page.goto('/dashboard');
    
    // Find and click logout button/link
    await page.getByRole('button', { name: /logout|sign out/i }).click();

    // Should redirect to home page
    await expect(page).toHaveURL('/');
    
    // Should show login link again
    await expect(page.getByRole('link', { name: 'Sign in' })).toBeVisible();
  });

  test('protected routes redirect to login', async ({ page }) => {
    // Try to access protected route without authentication
    await page.goto('/dashboard');

    // Should redirect to login page
    await expect(page).toHaveURL('/login');
    await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible();
  });

  test('authenticated user can access protected routes', async ({ page }) => {
    // Mock authentication
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock-token');
      localStorage.setItem('user_data', JSON.stringify({
        id: 'test-user-id',
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User'
      }));
    });

    // Navigate to protected route
    await page.goto('/dashboard');

    // Should be able to access the page
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
    
    // Should show user information
    await expect(page.getByText('Test User')).toBeVisible();
  });
});

test.describe('Authentication UI Components', () => {
  test('login form has proper accessibility', async ({ page }) => {
    await page.goto('/login');

    // Check form labels and inputs
    const emailInput = page.getByLabel('Email address');
    const passwordInput = page.getByLabel('Password');
    const submitButton = page.getByRole('button', { name: 'Sign in' });

    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    await expect(submitButton).toBeVisible();

    // Check input types
    await expect(emailInput).toHaveAttribute('type', 'email');
    await expect(passwordInput).toHaveAttribute('type', 'password');

    // Check required attributes
    await expect(emailInput).toHaveAttribute('required');
    await expect(passwordInput).toHaveAttribute('required');
  });

  test('registration form has proper accessibility', async ({ page }) => {
    await page.goto('/register');

    // Check all form fields
    const emailInput = page.getByLabel('Email address');
    const firstNameInput = page.getByLabel('First name');
    const lastNameInput = page.getByLabel('Last name');
    const passwordInput = page.getByLabel('Password', { exact: true });
    const confirmPasswordInput = page.getByLabel('Confirm password');
    const submitButton = page.getByRole('button', { name: 'Create account' });

    await expect(emailInput).toBeVisible();
    await expect(firstNameInput).toBeVisible();
    await expect(lastNameInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    await expect(confirmPasswordInput).toBeVisible();
    await expect(submitButton).toBeVisible();

    // Check input types
    await expect(emailInput).toHaveAttribute('type', 'email');
    await expect(passwordInput).toHaveAttribute('type', 'password');
    await expect(confirmPasswordInput).toHaveAttribute('type', 'password');

    // Check required attributes
    await expect(emailInput).toHaveAttribute('required');
    await expect(firstNameInput).toHaveAttribute('required');
    await expect(lastNameInput).toHaveAttribute('required');
    await expect(passwordInput).toHaveAttribute('required');
    await expect(confirmPasswordInput).toHaveAttribute('required');
  });

  test('form validation provides immediate feedback', async ({ page }) => {
    await page.goto('/register');

    // Fill email with invalid format
    await page.getByLabel('Email address').fill('invalid-email');
    await page.getByLabel('First name').click(); // Trigger blur event

    // Should show email validation error
    await expect(page.getByText(/valid email/i)).toBeVisible();

    // Fix email and check error disappears
    await page.getByLabel('Email address').fill('valid@example.com');
    await page.getByLabel('First name').click();

    // Email error should be gone
    await expect(page.getByText(/valid email/i)).not.toBeVisible();
  });

  test('password strength indicator works', async ({ page }) => {
    await page.goto('/register');

    const passwordInput = page.getByLabel('Password', { exact: true });

    // Type weak password
    await passwordInput.fill('weak');
    
    // Should show weak password indicator
    await expect(page.getByText(/weak|poor/i)).toBeVisible();

    // Type strong password
    await passwordInput.fill('StrongPassword123!');
    
    // Should show strong password indicator
    await expect(page.getByText(/strong|good/i)).toBeVisible();
  });
});