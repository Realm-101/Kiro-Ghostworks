import { MainLayout } from '@/components/layout/main-layout';
import { RegisterForm } from '@/components/auth/register-form';

export default function Register() {
  return (
    <MainLayout>
      <div className="flex min-h-full flex-1 flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="mx-auto h-12 w-12 rounded bg-indigo-600 flex items-center justify-center">
            <span className="text-white font-bold text-lg">G</span>
          </div>
          <h2 className="mt-6 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">
            Create your account
          </h2>
        </div>

        <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-[480px]">
          <div className="bg-white px-6 py-12 shadow sm:rounded-lg sm:px-12">
            <RegisterForm />
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
