import { 
  LoginRequest, 
  RegisterRequest, 
  AuthResponse, 
  AuthUser,
  WorkspaceSwitchRequest 
} from '@/types/auth';
import { ErrorResponse } from '@/types/api';
import { 
  Artifact, 
  CreateArtifactRequest, 
  UpdateArtifactRequest, 
  ArtifactSearchQuery 
} from '@ghostworks/shared';

// Paginated response type
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}
import Cookies from 'js-cookie';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  constructor(
    public status: number,
    public error: ErrorResponse,
    message?: string
  ) {
    super(message || error.message);
    this.name = 'ApiError';
  }
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Get access token from cookies
    const accessToken = Cookies.get('access_token');
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new ApiError(response.status, data);
      }

      return data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      // Network or other errors
      throw new ApiError(0, {
        error: 'network_error',
        message: 'Network error occurred',
        requestId: '',
        timestamp: new Date().toISOString(),
      });
    }
  }

  // Authentication endpoints
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await this.request<{ data: AuthResponse }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    return response.data;
  }

  async register(userData: RegisterRequest): Promise<AuthResponse> {
    const response = await this.request<{ data: AuthResponse }>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    return response.data;
  }

  async logout(): Promise<void> {
    await this.request('/api/v1/auth/logout', {
      method: 'POST',
    });
  }

  async refreshToken(): Promise<AuthResponse> {
    const refreshToken = Cookies.get('refresh_token');
    const response = await this.request<{ data: AuthResponse }>('/api/v1/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refreshToken }),
    });
    return response.data;
  }

  async getCurrentUser(): Promise<AuthUser> {
    const response = await this.request<{ data: AuthUser }>('/api/v1/auth/me');
    return response.data;
  }

  async switchWorkspace(request: WorkspaceSwitchRequest): Promise<AuthUser> {
    const response = await this.request<{ data: AuthUser }>('/api/v1/auth/switch-workspace', {
      method: 'POST',
      body: JSON.stringify(request),
    });
    return response.data;
  }

  // Artifact endpoints
  async getArtifacts(query: Partial<ArtifactSearchQuery> = {}): Promise<PaginatedResponse<Artifact>> {
    const searchParams = new URLSearchParams();
    
    if (query.q) searchParams.append('q', query.q);
    if (query.tags?.length) query.tags.forEach(tag => searchParams.append('tags', tag));
    if (query.createdAfter) searchParams.append('created_after', query.createdAfter);
    if (query.createdBefore) searchParams.append('created_before', query.createdBefore);
    if (query.limit) searchParams.append('limit', query.limit.toString());
    if (query.offset) searchParams.append('offset', query.offset.toString());

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/artifacts${queryString ? `?${queryString}` : ''}`;
    
    const response = await this.request<{ data: PaginatedResponse<Artifact> }>(endpoint);
    return response.data;
  }

  async createArtifact(artifact: CreateArtifactRequest): Promise<Artifact> {
    const response = await this.request<{ data: Artifact }>('/api/v1/artifacts', {
      method: 'POST',
      body: JSON.stringify(artifact),
    });
    return response.data;
  }

  async updateArtifact(id: string, updates: UpdateArtifactRequest): Promise<Artifact> {
    const response = await this.request<{ data: Artifact }>(`/api/v1/artifacts/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
    return response.data;
  }

  async deleteArtifact(id: string): Promise<void> {
    await this.request(`/api/v1/artifacts/${id}`, {
      method: 'DELETE',
    });
  }

  async getArtifact(id: string): Promise<Artifact> {
    const response = await this.request<{ data: Artifact }>(`/api/v1/artifacts/${id}`);
    return response.data;
  }

  // System stats endpoint
  async getSystemStats(): Promise<{
    users: number;
    workspaces: number;
    artifacts: number;
    active_artifacts: number;
    timestamp: string;
  }> {
    const response = await this.request<{
      users: number;
      workspaces: number;
      artifacts: number;
      active_artifacts: number;
      timestamp: string;
    }>('/api/v1/system/stats');
    return response;
  }

  // Prometheus metrics endpoint (for demo purposes)
  async getPrometheusMetrics(): Promise<string> {
    const response = await fetch(`${this.baseUrl}/metrics`);
    return response.text();
  }
}

export const apiClient = new ApiClient();
export { ApiError };