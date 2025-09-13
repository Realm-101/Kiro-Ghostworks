'use client';

import { Fragment, useState } from 'react';
import { Listbox, Transition } from '@headlessui/react';
import { CheckIcon, ChevronUpDownIcon } from '@heroicons/react/20/solid';
import { useAuth } from '@/contexts/auth-context';
import { WorkspaceMembership } from '@/types/auth';

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

export function WorkspaceSelector() {
  const { currentWorkspace, workspaces, switchWorkspace } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const handleWorkspaceChange = async (workspace: WorkspaceMembership) => {
    if (workspace.id === currentWorkspace?.id) return;
    
    setIsLoading(true);
    try {
      await switchWorkspace(workspace.tenantId);
    } catch (error) {
      console.error('Failed to switch workspace:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!currentWorkspace || workspaces.length <= 1) {
    return (
      <div className="flex items-center space-x-2">
        <div className="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center">
          <span className="text-white text-sm font-semibold">
            {currentWorkspace?.tenant.name.charAt(0).toUpperCase() || 'W'}
          </span>
        </div>
        <div className="text-sm font-medium text-gray-900">
          {currentWorkspace?.tenant.name || 'Workspace'}
        </div>
      </div>
    );
  }

  return (
    <Listbox value={currentWorkspace} onChange={handleWorkspaceChange}>
      {({ open }) => (
        <>
          <div className="relative">
            <Listbox.Button className="relative w-full cursor-default rounded-md bg-white py-1.5 pl-3 pr-10 text-left text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-600 sm:text-sm sm:leading-6">
              <div className="flex items-center space-x-2">
                <div className="h-6 w-6 rounded bg-indigo-600 flex items-center justify-center flex-shrink-0">
                  <span className="text-white text-xs font-semibold">
                    {currentWorkspace.tenant.name.charAt(0).toUpperCase()}
                  </span>
                </div>
                <span className="block truncate font-medium">
                  {currentWorkspace.tenant.name}
                </span>
                <span className="text-xs text-gray-500 capitalize">
                  ({currentWorkspace.role})
                </span>
              </div>
              <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                {isLoading ? (
                  <svg
                    className="animate-spin h-4 w-4 text-gray-400"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                ) : (
                  <ChevronUpDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                )}
              </span>
            </Listbox.Button>

            <Transition
              show={open}
              as={Fragment}
              leave="transition ease-in duration-100"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                {workspaces.map((workspace) => (
                  <Listbox.Option
                    key={workspace.id}
                    className={({ active }) =>
                      classNames(
                        active ? 'bg-indigo-600 text-white' : 'text-gray-900',
                        'relative cursor-default select-none py-2 pl-3 pr-9'
                      )
                    }
                    value={workspace}
                  >
                    {({ selected, active }) => (
                      <>
                        <div className="flex items-center space-x-2">
                          <div className={classNames(
                            active ? 'bg-white' : 'bg-indigo-600',
                            'h-6 w-6 rounded flex items-center justify-center flex-shrink-0'
                          )}>
                            <span className={classNames(
                              active ? 'text-indigo-600' : 'text-white',
                              'text-xs font-semibold'
                            )}>
                              {workspace.tenant.name.charAt(0).toUpperCase()}
                            </span>
                          </div>
                          <div className="flex flex-col">
                            <span className={classNames(
                              selected ? 'font-semibold' : 'font-normal',
                              'block truncate'
                            )}>
                              {workspace.tenant.name}
                            </span>
                            <span className={classNames(
                              active ? 'text-indigo-200' : 'text-gray-500',
                              'text-xs capitalize'
                            )}>
                              {workspace.role}
                            </span>
                          </div>
                        </div>

                        {selected ? (
                          <span
                            className={classNames(
                              active ? 'text-white' : 'text-indigo-600',
                              'absolute inset-y-0 right-0 flex items-center pr-4'
                            )}
                          >
                            <CheckIcon className="h-5 w-5" aria-hidden="true" />
                          </span>
                        ) : null}
                      </>
                    )}
                  </Listbox.Option>
                ))}
              </Listbox.Options>
            </Transition>
          </div>
        </>
      )}
    </Listbox>
  );
}