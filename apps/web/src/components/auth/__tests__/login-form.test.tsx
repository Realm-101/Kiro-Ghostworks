/**
 * Unit tests for LoginForm component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import LoginForm from '../login-form'

// Mock the auth context
const mockUseAuth = vi.fn()
vi.mock('@/contexts/auth-context', () => ({
  useAuth: mockUseAuth,
}))

// Mock the API client
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    login: vi.fn(),
  },
}))

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

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Default mock implementation
    mockUseAuth.mockReturnValue({
      login: vi.fn(),
      isLoading: false,
      error: null,
    })
  })

  it('renders login form with all required fields', () => {
    renderWithProviders(<LoginForm />)

    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('validates email format', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginForm />)

    const emailInput = screen.getByLabelText(/email address/i)
    
    await user.type(emailInput, 'invalid-email')
    await user.tab() // Trigger blur event

    await waitFor(() => {
      expect(screen.getByText(/valid email address/i)).toBeInTheDocument()
    })
  })

  it('validates required fields', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginForm />)

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      expect(screen.getByText(/password is required/i)).toBeInTheDocument()
    })
  })

  it('submits form with valid data', async () => {
    const user = userEvent.setup()
    const mockLogin = vi.fn().mockResolvedValue({ success: true })
    
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      isLoading: false,
      error: null,
    })

    renderWithProviders(<LoginForm />)

    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'TestPassword123!')
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'TestPassword123!',
      })
    })
  })

  it('displays loading state during submission', async () => {
    mockUseAuth.mockReturnValue({
      login: vi.fn(),
      isLoading: true,
      error: null,
    })

    renderWithProviders(<LoginForm />)

    const submitButton = screen.getByRole('button', { name: /signing in/i })
    expect(submitButton).toBeDisabled()
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })

  it('displays error message on login failure', async () => {
    const errorMessage = 'Invalid email or password'
    
    mockUseAuth.mockReturnValue({
      login: vi.fn(),
      isLoading: false,
      error: errorMessage,
    })

    renderWithProviders(<LoginForm />)

    expect(screen.getByText(errorMessage)).toBeInTheDocument()
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('has proper accessibility attributes', () => {
    renderWithProviders(<LoginForm />)

    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/password/i)

    expect(emailInput).toHaveAttribute('type', 'email')
    expect(emailInput).toHaveAttribute('required')
    expect(emailInput).toHaveAttribute('autocomplete', 'email')

    expect(passwordInput).toHaveAttribute('type', 'password')
    expect(passwordInput).toHaveAttribute('required')
    expect(passwordInput).toHaveAttribute('autocomplete', 'current-password')
  })

  it('toggles password visibility', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginForm />)

    const passwordInput = screen.getByLabelText(/password/i)
    const toggleButton = screen.getByRole('button', { name: /show password/i })

    expect(passwordInput).toHaveAttribute('type', 'password')

    await user.click(toggleButton)

    expect(passwordInput).toHaveAttribute('type', 'text')
    expect(screen.getByRole('button', { name: /hide password/i })).toBeInTheDocument()
  })

  it('prevents multiple submissions', async () => {
    const user = userEvent.setup()
    const mockLogin = vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)))
    
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      isLoading: false,
      error: null,
    })

    renderWithProviders(<LoginForm />)

    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'TestPassword123!')
    
    // Click submit multiple times rapidly
    await user.click(submitButton)
    await user.click(submitButton)
    await user.click(submitButton)

    // Should only call login once
    expect(mockLogin).toHaveBeenCalledTimes(1)
  })
})