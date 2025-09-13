import { test, expect } from '@playwright/test';

test.describe('Workspace Management', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication for all tests
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock-token');
      localStorage.setItem('user_data', JSON.stringify({
        id: 'test-user-id',
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User'
      }));
    });
  });

  test('user can create a new workspace', async ({ page }) => {
    await page.goto('/dashboard');

    // Look for create workspace button or link
    await page.getByRole('button', { name: /create.*workspace|new.*workspace/i }).click();

    // Fill out workspace creation form
    const timestamp = Date.now();
    const workspaceName = `Test Workspace ${timestamp}`;
    
    await page.getByLabel(/workspace.*name|name/i).fill(workspaceName);
    await page.getByLabel(/description/i).fill('A test workspace for E2E testing');

    // Submit form
    await page.getByRole('button', { name: /create|save/i }).click();

    // Should show success message or redirect to workspace
    await expect(
      page.getByText(/workspace.*created|success/i)
    ).toBeVisible();

    // Should see the new workspace in the list
    await expect(page.getByText(workspaceName)).toBeVisible();
  });

  test('user can switch between workspaces', async ({ page }) => {
    await page.goto('/dashboard');

    // Mock multiple workspaces
    await page.evaluate(() => {
      window.mockWorkspaces = [
        { id: 'ws1', name: 'Workspace 1', role: 'owner' },
        { id: 'ws2', name: 'Workspace 2', role: 'member' }
      ];
    });

    // Find workspace selector
    const workspaceSelector = page.getByRole('combobox', { name: /workspace|select.*workspace/i });
    await workspaceSelector.click();

    // Should see workspace options
    await expect(page.getByText('Workspace 1')).toBeVisible();
    await expect(page.getByText('Workspace 2')).toBeVisible();

    // Select different workspace
    await page.getByText('Workspace 2').click();

    // Should update current workspace context
    await expect(page.getByText(/current.*workspace.*2|workspace 2/i)).toBeVisible();
  });

  test('workspace selector shows user role', async ({ page }) => {
    await page.goto('/dashboard');

    // Mock workspace with role information
    await page.evaluate(() => {
      window.mockWorkspaces = [
        { id: 'ws1', name: 'My Company', role: 'owner' },
        { id: 'ws2', name: 'Client Project', role: 'member' }
      ];
    });

    const workspaceSelector = page.getByRole('combobox', { name: /workspace/i });
    await workspaceSelector.click();

    // Should show role badges
    await expect(page.getByText(/owner/i)).toBeVisible();
    await expect(page.getByText(/member/i)).toBeVisible();
  });

  test('user can view workspace settings', async ({ page }) => {
    await page.goto('/dashboard');

    // Navigate to workspace settings
    await page.getByRole('link', { name: /settings|workspace.*settings/i }).click();

    // Should show workspace settings page
    await expect(page.getByRole('heading', { name: /workspace.*settings|settings/i })).toBeVisible();

    // Should show workspace information
    await expect(page.getByLabel(/workspace.*name/i)).toBeVisible();
    await expect(page.getByLabel(/description/i)).toBeVisible();
  });

  test('workspace owner can manage members', async ({ page }) => {
    // Mock owner role
    await page.evaluate(() => {
      localStorage.setItem('current_workspace', JSON.stringify({
        id: 'ws1',
        name: 'My Company',
        role: 'owner'
      }));
    });

    await page.goto('/workspace/settings/members');

    // Should show members management section
    await expect(page.getByRole('heading', { name: /members|team/i })).toBeVisible();

    // Should show invite member button
    await expect(page.getByRole('button', { name: /invite|add.*member/i })).toBeVisible();

    // Should show current members list
    await expect(page.getByText(/test@example\.com/)).toBeVisible();
  });

  test('workspace member cannot access admin features', async ({ page }) => {
    // Mock member role
    await page.evaluate(() => {
      localStorage.setItem('current_workspace', JSON.stringify({
        id: 'ws1',
        name: 'Client Project',
        role: 'member'
      }));
    });

    await page.goto('/workspace/settings');

    // Should not show admin-only features
    await expect(page.getByText(/delete.*workspace/i)).not.toBeVisible();
    await expect(page.getByRole('button', { name: /invite.*member/i })).not.toBeVisible();
  });

  test('user can invite members to workspace', async ({ page }) => {
    // Mock owner role
    await page.evaluate(() => {
      localStorage.setItem('current_workspace', JSON.stringify({
        id: 'ws1',
        name: 'My Company',
        role: 'owner'
      }));
    });

    await page.goto('/workspace/settings/members');

    // Click invite member button
    await page.getByRole('button', { name: /invite|add.*member/i }).click();

    // Fill out invitation form
    await page.getByLabel(/email/i).fill('newmember@example.com');
    await page.getByRole('combobox', { name: /role/i }).click();
    await page.getByText('Member').click();

    // Send invitation
    await page.getByRole('button', { name: /send.*invite|invite/i }).click();

    // Should show success message
    await expect(page.getByText(/invitation.*sent|invited/i)).toBeVisible();
  });

  test('workspace settings form validation works', async ({ page }) => {
    await page.goto('/workspace/settings');

    // Clear workspace name
    await page.getByLabel(/workspace.*name/i).clear();

    // Try to save
    await page.getByRole('button', { name: /save|update/i }).click();

    // Should show validation error
    await expect(page.getByText(/name.*required|workspace name/i)).toBeVisible();
  });

  test('user can delete workspace as owner', async ({ page }) => {
    // Mock owner role
    await page.evaluate(() => {
      localStorage.setItem('current_workspace', JSON.stringify({
        id: 'ws1',
        name: 'Test Workspace',
        role: 'owner'
      }));
    });

    await page.goto('/workspace/settings');

    // Find delete workspace section
    await page.getByRole('button', { name: /delete.*workspace/i }).click();

    // Should show confirmation dialog
    await expect(page.getByText(/are you sure|confirm.*delete/i)).toBeVisible();

    // Type workspace name to confirm
    await page.getByLabel(/type.*workspace.*name/i).fill('Test Workspace');

    // Confirm deletion
    await page.getByRole('button', { name: /delete|confirm/i }).click();

    // Should redirect to dashboard or workspace selection
    await expect(page).toHaveURL(/\/dashboard|\/workspaces/);
  });
});

test.describe('Workspace Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication and workspace
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock-token');
      localStorage.setItem('user_data', JSON.stringify({
        id: 'test-user-id',
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User'
      }));
      localStorage.setItem('current_workspace', JSON.stringify({
        id: 'ws1',
        name: 'Test Workspace',
        role: 'member'
      }));
    });
  });

  test('workspace context is maintained across navigation', async ({ page }) => {
    await page.goto('/dashboard');

    // Verify workspace is shown in header
    await expect(page.getByText('Test Workspace')).toBeVisible();

    // Navigate to artifacts page
    await page.getByRole('link', { name: 'Artifacts' }).click();

    // Workspace context should be maintained
    await expect(page.getByText('Test Workspace')).toBeVisible();
    await expect(page).toHaveURL(/\/artifacts/);
  });

  test('workspace breadcrumb navigation works', async ({ page }) => {
    await page.goto('/artifacts');

    // Should show breadcrumb navigation
    await expect(page.getByText(/test workspace.*artifacts/i)).toBeVisible();

    // Click on workspace in breadcrumb
    await page.getByRole('link', { name: 'Test Workspace' }).click();

    // Should navigate to workspace dashboard
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('workspace sidebar shows correct sections', async ({ page }) => {
    await page.goto('/dashboard');

    // Should show main navigation sections
    await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Artifacts' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Settings' })).toBeVisible();
  });

  test('workspace quick actions are accessible', async ({ page }) => {
    await page.goto('/dashboard');

    // Should show quick action buttons
    await expect(page.getByRole('button', { name: /create.*artifact/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /invite.*member/i })).toBeVisible();
  });
});

test.describe('Workspace Responsive Design', () => {
  test('workspace selector works on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock-token');
      localStorage.setItem('current_workspace', JSON.stringify({
        id: 'ws1',
        name: 'Mobile Test Workspace',
        role: 'member'
      }));
    });

    await page.goto('/dashboard');

    // Workspace selector should be accessible on mobile
    const workspaceSelector = page.getByRole('button', { name: /workspace|mobile.*workspace/i });
    await expect(workspaceSelector).toBeVisible();

    await workspaceSelector.click();

    // Should show workspace options in mobile-friendly format
    await expect(page.getByText('Mobile Test Workspace')).toBeVisible();
  });

  test('workspace navigation collapses on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock-token');
      localStorage.setItem('current_workspace', JSON.stringify({
        id: 'ws1',
        name: 'Test Workspace',
        role: 'member'
      }));
    });

    await page.goto('/dashboard');

    // Should show mobile menu button
    const mobileMenuButton = page.getByRole('button', { name: /menu|navigation/i });
    await expect(mobileMenuButton).toBeVisible();

    // Click to open mobile menu
    await mobileMenuButton.click();

    // Should show navigation items
    await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Artifacts' })).toBeVisible();
  });
});