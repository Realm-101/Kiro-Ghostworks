/**
 * Unit tests for ArtifactList component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ArtifactList } from '../artifact-list'
import { apiClient } from '@/lib/api-client'

// Mock the API client
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    getArtifacts: vi.fn(),
  },
}))

// Mock the auth context
vi.mock('@/contexts/auth-context', () => ({
  useAuth: () => ({
    user: {
      id: 'test-user-id',
      email: 'test@example.com',
    },
    currentWorkspace: {
      id: 'test-workspace-id',
      name: 'Test Workspace',
    },
  }),
}))

const mockArtifacts = [
  {
    id: '1',
    name: 'API Service Documentation',
    description: 'Documentation for the REST API service',
    tags: ['api', 'documentation', 'service'],
    metadata: { version: '1.0.0', technology: 'FastAPI' },
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-15T10:30:00Z',
  },
  {
    id: '2',
    name: 'Database Migration Tool',
    description: 'Tool for managing database schema migrations',
    tags: ['database', 'migration', 'tool'],
    metadata: { version: '2.1.0', technology: 'Alembic' },
    created_at: '2024-01-14T09:15:00Z',
    updated_at: '2024-01-14T09:15:00Z',
  },
  {
    id: '3',
    name: 'Authentication Library',
    description: 'Library for handling user authentication',
    tags: ['auth', 'library', 'security'],
    metadata: { version: '1.5.0', technology: 'Python' },
    created_at: '2024-01-13T14:45:00Z',
    updated_at: '2024-01-13T14:45:00Z',
  },
]

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  )
}

describe('ArtifactList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock successful API response
    vi.mocked(apiClient.getArtifacts).mockResolvedValue({
      items: mockArtifacts,
      total: mockArtifacts.length,
      limit: 20,
      offset: 0,
      hasMore: false,
    })
  })

  it('renders artifact list with all artifacts', async () => {
    renderWithProviders(<ArtifactList />)

    await waitFor(() => {
      expect(screen.getByText('API Service Documentation')).toBeInTheDocument()
      expect(screen.getByText('Database Migration Tool')).toBeInTheDocument()
      expect(screen.getByText('Authentication Library')).toBeInTheDocument()
    })
  })

  it('displays artifact details correctly', async () => {
    renderWithProviders(<ArtifactList />)

    await waitFor(() => {
      // Check first artifact details
      expect(screen.getByText('API Service Documentation')).toBeInTheDocument()
      expect(screen.getByText('Documentation for the REST API service')).toBeInTheDocument()
      expect(screen.getByText('api')).toBeInTheDocument()
      expect(screen.getByText('documentation')).toBeInTheDocument()
      expect(screen.getByText('service')).toBeInTheDocument()
    })
  })

  it('shows loading state initially', () => {
    // Mock pending API call
    vi.mocked(apiClient.getArtifacts).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    renderWithProviders(<ArtifactList />)

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    expect(screen.getByText(/loading artifacts/i)).toBeInTheDocument()
  })

  it('shows empty state when no artifacts exist', async () => {
    vi.mocked(apiClient.getArtifacts).mockResolvedValue({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
      hasMore: false,
    })

    renderWithProviders(<ArtifactList />)

    await waitFor(() => {
      expect(screen.getByText(/no artifacts found/i)).toBeInTheDocument()
      expect(screen.getByText(/create your first artifact/i)).toBeInTheDocument()
    })
  })

  it('handles API errors gracefully', async () => {
    vi.mocked(apiClient.getArtifacts).mockRejectedValue(
      new Error('Failed to fetch artifacts')
    )

    renderWithProviders(<ArtifactList />)

    await waitFor(() => {
      expect(screen.getByText(/error loading artifacts/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
    })
  })

  it('filters artifacts by search query', async () => {
    const user = userEvent.setup()
    
    // Mock search API
    vi.mocked(apiClient.getArtifacts).mockResolvedValue({
      items: [mockArtifacts[0]], // Only API Service Documentation
      total: 1,
      limit: 20,
      offset: 0,
      hasMore: false,
    })

    renderWithProviders(<ArtifactList />)

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('API Service Documentation')).toBeInTheDocument()
    })

    // Search for "API"
    const searchInput = screen.getByPlaceholderText(/search artifacts/i)
    await user.type(searchInput, 'API')

    await waitFor(() => {
      expect(apiClient.getArtifacts).toHaveBeenCalledWith(
        expect.objectContaining({ q: 'API' })
      )
    })
  })

  it('filters artifacts by tags', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ArtifactList />)

    await waitFor(() => {
      expect(screen.getByText('API Service Documentation')).toBeInTheDocument()
    })

    // Click on a tag to filter
    const apiTag = screen.getByText('api')
    await user.click(apiTag)

    await waitFor(() => {
      expect(apiClient.getArtifacts).toHaveBeenCalledWith(
        expect.objectContaining({
          tags: ['api']
        })
      )
    })
  })

  it('handles pagination correctly', async () => {
    const user = userEvent.setup()
    
    // Mock paginated response
    vi.mocked(apiClient.getArtifacts).mockResolvedValue({
      items: mockArtifacts,
      total: 50,
      limit: 20,
      offset: 0,
      hasMore: true,
    })

    renderWithProviders(<ArtifactList />)

    await waitFor(() => {
      expect(screen.getByText('API Service Documentation')).toBeInTheDocument()
    })

    // Check pagination controls
    expect(screen.getByRole('button', { name: /next page/i })).toBeInTheDocument()
    expect(screen.getByText(/1.*of.*3/i)).toBeInTheDocument() // 50 items, 20 per page = 3 pages

    // Click next page
    const nextButton = screen.getByRole('button', { name: /next page/i })
    await user.click(nextButton)

    await waitFor(() => {
      expect(apiClient.getArtifacts).toHaveBeenCalledWith(
        expect.objectContaining({
          offset: 20
        })
      )
    })
  })

  it('opens artifact modal on click', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ArtifactList />)

    await waitFor(() => {
      expect(screen.getByText('API Service Documentation')).toBeInTheDocument()
    })

    // Click on artifact
    const artifactCard = screen.getByText('API Service Documentation')
    await user.click(artifactCard)

    // Should open modal (assuming modal is rendered)
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })

  it('has proper accessibility attributes', async () => {
    renderWithProviders(<ArtifactList />)

    await waitFor(() => {
      expect(screen.getByText('API Service Documentation')).toBeInTheDocument()
    })

    // Check main content area
    expect(screen.getByRole('main')).toBeInTheDocument()
    
    // Check search input
    const searchInput = screen.getByRole('searchbox')
    expect(searchInput).toHaveAttribute('aria-label', expect.stringMatching(/search/i))

    // Check artifact cards are clickable
    const artifactCards = screen.getAllByRole('button')
    expect(artifactCards.length).toBeGreaterThan(0)
  })

  it('supports keyboard navigation', async () => {
    renderWithProviders(<ArtifactList />)

    await waitFor(() => {
      expect(screen.getByText('API Service Documentation')).toBeInTheDocument()
    })

    // Tab through elements
    const searchInput = screen.getByRole('searchbox')
    searchInput.focus()
    expect(searchInput).toHaveFocus()

    // Tab to first artifact
    fireEvent.keyDown(searchInput, { key: 'Tab' })
    
    const firstArtifact = screen.getAllByRole('button')[0]
    expect(firstArtifact).toHaveFocus()

    // Enter should open artifact
    fireEvent.keyDown(firstArtifact, { key: 'Enter' })
    
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })
})