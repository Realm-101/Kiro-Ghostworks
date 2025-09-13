'use client';

import { useState } from 'react';
import { LoginForm } from '@/components/auth/login-form';
import { RegisterForm } from '@/components/auth/register-form';
import { WorkspaceSelector } from '@/components/auth/workspace-selector';
import { useAuth } from '@/contexts/auth-context';

export default function AuthTest() {
  const [activeForm, setActiveForm] = useState<'login' | 'register'>('login');
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-md mx-auto">
        <div className="bg-white shadow rounded-lg p-6">
          <h1 className="text-2xl font-bold mb-6 text-center">Auth Components Test</h1>
          
          {isAuthenticated ? (
            <div className="space-y-4">
              <div className="p-4 bg-green-50 rounded-md">
                <h2 className="text-lg font-semibold text-green-800">Authenticated!</h2>
                <p className="text-green-600">Email: {user?.user.email}</p>
                <p className="text-green-600">
                  Workspace: {user?.currentWorkspace?.tenant.name || 'None'}
                </p>
              </div>
              
              <div>
                <h3 className="text-sm font-medium mb-2">Workspace Selector:</h3>
                <WorkspaceSelector />
              </div>
            </div>
          ) : (
            <div>
              <div className="flex mb-4">
                <button
                  onClick={() => setActiveForm('login')}
                  className={`flex-1 py-2 px-4 text-sm font-medium rounded-l-md ${
                    activeForm === 'login'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-200 text-gray-700'
                  }`}
                >
                  Login
                </button>
                <button
                  onClick={() => setActiveForm('register')}
                  className={`flex-1 py-2 px-4 text-sm font-medium rounded-r-md ${
                    activeForm === 'register'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-200 text-gray-700'
                  }`}
                >
                  Register
                </button>
              </div>
              
              {activeForm === 'login' ? <LoginForm /> : <RegisterForm />}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}