import { MainLayout } from '@/components/layout/main-layout';
import { ProtectedRoute } from '@/components/auth/protected-route';

export default function Dashboard() {
  return (
    <ProtectedRoute>
      <MainLayout>
        <div className="py-10">
          <header>
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <h1 className="text-3xl font-bold leading-tight tracking-tight text-gray-900">
                Dashboard
              </h1>
            </div>
          </header>
          <main>
            <div className="mx-auto max-w-7xl sm:px-6 lg:px-8">
              <div className="px-4 py-8 sm:px-0">
                <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 flex items-center justify-center">
                  <div className="text-center">
                    <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                      Welcome to your Dashboard
                    </h2>
                    <p className="text-gray-600">
                      This is a protected route that requires authentication.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </main>
        </div>
      </MainLayout>
    </ProtectedRoute>
  );
}