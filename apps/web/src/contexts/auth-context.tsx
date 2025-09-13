'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Cookies from 'js-cookie';
import { 
  AuthUser, 
  LoginRequest, 
  RegisterRequest, 
  WorkspaceSwitchRequest,
  WorkspaceMembership 
} from '@/types/auth';
import { apiClient, ApiError } from '@/lib/api-client';

interface AuthContextType {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  switchWorkspace: (workspaceId: string) => Promise<void>;
  currentWorkspace: WorkspaceMembership | null;
  workspaces: WorkspaceMembership[];
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isInitialized, setIsInitialized] = useState(false);
  const queryClient = useQueryClient();

  // Query to get current user
  const {
    data: user,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['auth', 'user'],
    queryFn: apiClient.getCurrentUser,
    enabled: isInitialized && !!Cookies.get('access_token'),
    retry: (failureCount, error) => {
      // Don't retry on 401 errors (unauthorized)
      if (error instanceof ApiError && error.status === 401) {
        return false;
      }
      return failureCount < 3;
    },
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: apiClient.login,
    onSuccess: (data) => {
      // Store tokens in cookies
      Cookies.set('access_token', data.tokens.accessToken, {
        expires: new Date(Date.now() + data.tokens.expiresIn * 1000),
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
      });
      Cookies.set('refresh_token', data.tokens.refreshToken, {
        expires: 7, // 7 days
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
      });

      // Update query cache
      queryClient.setQueryData(['auth', 'user'], {
        user: data.user,
        currentWorkspace: data.workspaces[0] || null,
        workspaces: data.workspaces,
      });
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: apiClient.register,
    onSuccess: (data) => {
      // Store tokens in cookies
      Cookies.set('access_token', data.tokens.accessToken, {
        expires: new Date(Date.now() + data.tokens.expiresIn * 1000),
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
      });
      Cookies.set('refresh_token', data.tokens.refreshToken, {
        expires: 7, // 7 days
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
      });

      // Update query cache
      queryClient.setQueryData(['auth', 'user'], {
        user: data.user,
        currentWorkspace: data.workspaces[0] || null,
        workspaces: data.workspaces,
      });
    },
  });

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: apiClient.logout,
    onSuccess: () => {
      // Clear tokens
      Cookies.remove('access_token');
      Cookies.remove('refresh_token');
      
      // Clear query cache
      queryClient.clear();
    },
    onError: () => {
      // Even if logout fails on server, clear local tokens
      Cookies.remove('access_token');
      Cookies.remove('refresh_token');
      queryClient.clear();
    },
  });

  // Switch workspace mutation
  const switchWorkspaceMutation = useMutation({
    mutationFn: (request: WorkspaceSwitchRequest) => apiClient.switchWorkspace(request),
    onSuccess: (data) => {
      queryClient.setQueryData(['auth', 'user'], data);
    },
  });

  // Initialize auth state on mount
  useEffect(() => {
    setIsInitialized(true);
  }, []);

  // Handle token refresh on 401 errors
  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) {
      const refreshToken = Cookies.get('refresh_token');
      if (refreshToken) {
        // Try to refresh token
        apiClient.refreshToken()
          .then((data) => {
            Cookies.set('access_token', data.tokens.accessToken, {
              expires: new Date(Date.now() + data.tokens.expiresIn * 1000),
              secure: process.env.NODE_ENV === 'production',
              sameSite: 'strict',
            });
            // Refetch user data
            queryClient.invalidateQueries({ queryKey: ['auth', 'user'] });
          })
          .catch(() => {
            // Refresh failed, clear tokens
            Cookies.remove('access_token');
            Cookies.remove('refresh_token');
            queryClient.clear();
          });
      } else {
        // No refresh token, clear everything
        Cookies.remove('access_token');
        queryClient.clear();
      }
    }
  }, [error, queryClient]);

  const contextValue: AuthContextType = {
    user: user || null,
    isLoading: !isInitialized || isLoading,
    isAuthenticated: !!user,
    login: async (credentials: LoginRequest) => {
      await loginMutation.mutateAsync(credentials);
    },
    register: async (userData: RegisterRequest) => {
      await registerMutation.mutateAsync(userData);
    },
    logout: async () => {
      await logoutMutation.mutateAsync();
    },
    switchWorkspace: async (workspaceId: string) => {
      await switchWorkspaceMutation.mutateAsync({ workspaceId });
    },
    currentWorkspace: user?.currentWorkspace || null,
    workspaces: user?.workspaces || [],
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}