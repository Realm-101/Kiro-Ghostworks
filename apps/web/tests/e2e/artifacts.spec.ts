import { test, expect } from '@playwright/test';

test.describe('Artifact Management', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication and workspace for all tests
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

  test('user can create a new artifact', async ({ page }) => {
    await page.goto('/artifacts');

    // Click create artifact button
    await page.getByRole('button', { name: /create.*artifact|new.*artifact/i }).click();

    // Fill out artifact creation form
    const timestamp = Date.now();
    const artifactName = `Test Artifact ${timestamp}`;
    
    await page.getByLabel(/name/i).fill(artifactName);
    await page.getByLabel(/description/i).fill('A test artifact for E2E testing');
    
    // Add tags
    const tagInput = page.getByLabel(/tags/i);
    await tagInput.fill('test');
    await page.keyboard.press('Enter');
    await tagInput.fill('e2e');
    await page.keyboard.press('Enter');
    await tagInput.fill('automation');
    await page.keyboard.press('Enter');

    // Submit form
    await page.getByRole('button', { name: /create|save/i }).click();

    // Should show success message
    await expect(page.getByText(/artifact.*created|success/i)).toBeVisible();

    // Should see the new artifact in the list
    await expect(page.getByText(artifactName)).toBeVisible();
  });

  test('user can view artifact details', async ({ page }) => {
    await page.goto('/artifacts');

    // Mock existing artifacts
    await page.evaluate(() => {
      window.mockArtifacts = [
        {
          id: 'artifact-1',
          name: 'API Service Documentation',
          description: 'Documentation for the REST API service',
          tags: ['api', 'documentation', 'service'],
          metadata: { version: '1.0.0', technology: 'FastAPI' }
        }
      ];
    });

    // Click on an artifact to view details
    await page.getByText('API Service Documentation').click();

    // Should show artifact details
    await expect(page.getByRole('heading', { name: 'API Service Documentation' })).toBeVisible();
    await expect(page.getByText('Documentation for the REST API service')).toBeVisible();
    await expect(page.getByText('api')).toBeVisible();
    await expect(page.getByText('documentation')).toBeVisible();
    await expect(page.getByText('service')).toBeVisible();
  });

  test('user can edit an existing artifact', async ({ page }) => {
    await page.goto('/artifacts');

    // Mock existing artifact
    await page.evaluate(() => {
      window.mockArtifacts = [
        {
          id: 'artifact-1',
          name: 'Original Name',
          description: 'Original description',
          tags: ['original'],
          metadata: { version: '1.0.0' }
        }
      ];
    });

    // Find and click edit button
    await page.getByRole('button', { name: /edit/i }).first().click();

    // Update artifact details
    await page.getByLabel(/name/i).clear();
    await page.getByLabel(/name/i).fill('Updated Artifact Name');
    
    await page.getByLabel(/description/i).clear();
    await page.getByLabel(/description/i).fill('Updated description for the artifact');

    // Update tags
    const tagInput = page.getByLabel(/tags/i);
    await tagInput.fill('updated');
    await page.keyboard.press('Enter');

    // Save changes
    await page.getByRole('button', { name: /save|update/i }).click();

    // Should show success message
    await expect(page.getByText(/artifact.*updated|changes.*saved/i)).toBeVisible();

    // Should see updated information
    await expect(page.getByText('Updated Artifact Name')).toBeVisible();
    await expect(page.getByText('Updated description for the artifact')).toBeVisible();
  });

  test('user can delete an artifact', async ({ page }) => {
    await page.goto('/artifacts');

    // Mock existing artifact
    await page.evaluate(() => {
      window.mockArtifacts = [
        {
          id: 'artifact-1',
          name: 'Artifact to Delete',
          description: 'This artifact will be deleted',
          tags: ['delete', 'test']
        }
      ];
    });

    // Find and click delete button
    await page.getByRole('button', { name: /delete/i }).first().click();

    // Should show confirmation dialog
    await expect(page.getByText(/are you sure|confirm.*delete/i)).toBeVisible();

    // Confirm deletion
    await page.getByRole('button', { name: /delete|confirm/i }).click();

    // Should show success message
    await expect(page.getByText(/artifact.*deleted|removed/i)).toBeVisible();

    // Artifact should no longer be visible
    await expect(page.getByText('Artifact to Delete')).not.toBeVisible();
  });

  test('user can search artifacts', async ({ page }) => {
    await page.goto('/artifacts');

    // Mock multiple artifacts
    await page.evaluate(() => {
      window.mockArtifacts = [
        { id: '1', name: 'API Service', description: 'REST API service', tags: ['api', 'service'] },
        { id: '2', name: 'Database Tool', description: 'Database management tool', tags: ['database', 'tool'] },
        { id: '3', name: 'API Testing Framework', description: 'Framework for API testing', tags: ['api', 'testing'] }
      ];
    });

    // Use search functionality
    const searchInput = page.getByPlaceholder(/search.*artifacts/i);
    await searchInput.fill('API');

    // Should show filtered results
    await expect(page.getByText('API Service')).toBeVisible();
    await expect(page.getByText('API Testing Framework')).toBeVisible();
    await expect(page.getByText('Database Tool')).not.toBeVisible();

    // Clear search
    await searchInput.clear();
    await searchInput.fill('database');

    // Should show different filtered results
    await expect(page.getByText('Database Tool')).toBeVisible();
    await expect(page.getByText('API Service')).not.toBeVisible();
  });

  test('user can filter artifacts by tags', async ({ page }) => {
    await page.goto('/artifacts');

    // Mock artifacts with different tags
    await page.evaluate(() => {
      window.mockArtifacts = [
        { id: '1', name: 'API Service', tags: ['api', 'service', 'backend'] },
        { id: '2', name: 'Frontend Component', tags: ['frontend', 'react', 'ui'] },
        { id: '3', name: 'Database Schema', tags: ['database', 'backend', 'schema'] }
      ];
    });

    // Click on tag filter
    await page.getByText('backend').first().click();

    // Should show only artifacts with 'backend' tag
    await expect(page.getByText('API Service')).toBeVisible();
    await expect(page.getByText('Database Schema')).toBeVisible();
    await expect(page.getByText('Frontend Component')).not.toBeVisible();

    // Click on different tag
    await page.getByText('frontend').first().click();

    // Should show only artifacts with 'frontend' tag
    await expect(page.getByText('Frontend Component')).toBeVisible();
    await expect(page.getByText('API Service')).not.toBeVisible();
  });

  test('artifact list pagination works', async ({ page }) => {
    await page.goto('/artifacts');

    // Mock many artifacts to test pagination
    await page.evaluate(() => {
      window.mockArtifacts = Array.from({ length: 25 }, (_, i) => ({
        id: `artifact-${i}`,
        name: `Artifact ${i + 1}`,
        description: `Description for artifact ${i + 1}`,
        tags: ['test', `tag${i}`]
      }));
    });

    // Should show pagination controls
    await expect(page.getByRole('button', { name: /next|page.*2/i })).toBeVisible();
    await expect(page.getByText(/1.*of.*\d+|page.*1/i)).toBeVisible();

    // Click next page
    await page.getByRole('button', { name: /next/i }).click();

    // Should show different artifacts
    await expect(page.getByText(/page.*2|2.*of/i)).toBeVisible();

    // Click previous page
    await page.getByRole('button', { name: /previous/i }).click();

    // Should be back to first page
    await expect(page.getByText(/page.*1|1.*of/i)).toBeVisible();
  });
});

test.describe('Artifact Form Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock-token');
      localStorage.setItem('current_workspace', JSON.stringify({
        id: 'ws1',
        name: 'Test Workspace',
        role: 'member'
      }));
    });
  });

  test('artifact creation form validates required fields', async ({ page }) => {
    await page.goto('/artifacts');

    // Open create artifact form
    await page.getByRole('button', { name: /create.*artifact/i }).click();

    // Try to submit without required fields
    await page.getByRole('button', { name: /create|save/i }).click();

    // Should show validation errors
    await expect(page.getByText(/name.*required|artifact name/i)).toBeVisible();
  });

  test('artifact name has character limits', async ({ page }) => {
    await page.goto('/artifacts');

    await page.getByRole('button', { name: /create.*artifact/i }).click();

    // Try very long name
    const longName = 'A'.repeat(300);
    await page.getByLabel(/name/i).fill(longName);

    await page.getByRole('button', { name: /create/i }).click();

    // Should show length validation error
    await expect(page.getByText(/name.*too long|character limit/i)).toBeVisible();
  });

  test('tag input validates format', async ({ page }) => {
    await page.goto('/artifacts');

    await page.getByRole('button', { name: /create.*artifact/i }).click();

    // Fill required fields
    await page.getByLabel(/name/i).fill('Test Artifact');

    // Try invalid tag format
    const tagInput = page.getByLabel(/tags/i);
    await tagInput.fill('invalid tag with spaces');
    await page.keyboard.press('Enter');

    // Should show tag validation error
    await expect(page.getByText(/tag.*format|no spaces/i)).toBeVisible();
  });
});

test.describe('Artifact UI Components', () => {
  test('artifact cards display all information', async ({ page }) => {
    await page.goto('/artifacts');

    // Mock artifact with complete information
    await page.evaluate(() => {
      window.mockArtifacts = [
        {
          id: 'complete-artifact',
          name: 'Complete Artifact',
          description: 'This artifact has all fields populated',
          tags: ['complete', 'test', 'example'],
          metadata: { version: '2.1.0', author: 'Test User' },
          created_at: '2024-01-15T10:30:00Z',
          updated_at: '2024-01-16T14:45:00Z'
        }
      ];
    });

    // Should display all artifact information
    await expect(page.getByText('Complete Artifact')).toBeVisible();
    await expect(page.getByText('This artifact has all fields populated')).toBeVisible();
    await expect(page.getByText('complete')).toBeVisible();
    await expect(page.getByText('test')).toBeVisible();
    await expect(page.getByText('example')).toBeVisible();
    await expect(page.getByText(/created|updated/i)).toBeVisible();
  });

  test('artifact modal shows detailed view', async ({ page }) => {
    await page.goto('/artifacts');

    // Mock artifact
    await page.evaluate(() => {
      window.mockArtifacts = [
        {
          id: 'detailed-artifact',
          name: 'Detailed Artifact',
          description: 'This artifact shows in modal view',
          tags: ['modal', 'detailed'],
          metadata: { version: '1.5.0', complexity: 'medium' }
        }
      ];
    });

    // Click to open modal
    await page.getByText('Detailed Artifact').click();

    // Should show modal with detailed information
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Detailed Artifact' })).toBeVisible();
    await expect(page.getByText('This artifact shows in modal view')).toBeVisible();

    // Should show metadata
    await expect(page.getByText('1.5.0')).toBeVisible();
    await expect(page.getByText('medium')).toBeVisible();

    // Should be able to close modal
    await page.getByRole('button', { name: /close|×/i }).click();
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });

  test('tag input component works correctly', async ({ page }) => {
    await page.goto('/artifacts');

    await page.getByRole('button', { name: /create.*artifact/i }).click();

    const tagInput = page.getByLabel(/tags/i);

    // Add multiple tags
    await tagInput.fill('first-tag');
    await page.keyboard.press('Enter');
    await tagInput.fill('second-tag');
    await page.keyboard.press('Enter');

    // Should show tag chips
    await expect(page.getByText('first-tag')).toBeVisible();
    await expect(page.getByText('second-tag')).toBeVisible();

    // Should be able to remove tags
    await page.getByRole('button', { name: /remove.*first-tag/i }).click();
    await expect(page.getByText('first-tag')).not.toBeVisible();
    await expect(page.getByText('second-tag')).toBeVisible();
  });
});

test.describe('Artifact Accessibility', () => {
  test('artifact list has proper ARIA labels', async ({ page }) => {
    await page.goto('/artifacts');

    // Check main content area
    await expect(page.getByRole('main')).toBeVisible();
    
    // Check search input accessibility
    const searchInput = page.getByRole('searchbox', { name: /search.*artifacts/i });
    await expect(searchInput).toBeVisible();

    // Check create button accessibility
    const createButton = page.getByRole('button', { name: /create.*artifact/i });
    await expect(createButton).toBeVisible();
  });

  test('artifact forms are keyboard navigable', async ({ page }) => {
    await page.goto('/artifacts');

    await page.getByRole('button', { name: /create.*artifact/i }).click();

    // Tab through form fields
    await page.keyboard.press('Tab');
    await expect(page.getByLabel(/name/i)).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.getByLabel(/description/i)).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.getByLabel(/tags/i)).toBeFocused();
  });

  test('artifact actions have proper focus management', async ({ page }) => {
    await page.goto('/artifacts');

    // Mock artifact for testing
    await page.evaluate(() => {
      window.mockArtifacts = [
        { id: '1', name: 'Focus Test Artifact', description: 'Testing focus', tags: ['focus'] }
      ];
    });

    // Use keyboard to navigate to artifact actions
    await page.keyboard.press('Tab'); // Skip to main content
    await page.keyboard.press('Tab'); // Navigate to first artifact
    await page.keyboard.press('Enter'); // Open artifact

    // Should focus on modal content
    await expect(page.getByRole('dialog')).toBeFocused();

    // Escape should close modal and return focus
    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });
});