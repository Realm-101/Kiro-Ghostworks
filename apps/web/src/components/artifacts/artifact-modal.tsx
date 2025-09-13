'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Dialog, DialogPanel, DialogTitle } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { apiClient } from '@/lib/api-client';
import { Artifact, CreateArtifactRequest, UpdateArtifactRequest } from '@ghostworks/shared';
import { TagInput } from './tag-input';

type ArtifactFormData = {
  name: string;
  description?: string;
};

interface ArtifactModalProps {
  isOpen: boolean;
  onClose: () => void;
  mode: 'create' | 'edit';
  artifact?: Artifact | null;
  onSuccess: () => void;
}

export function ArtifactModal({ isOpen, onClose, mode, artifact, onSuccess }: ArtifactModalProps) {
  const [tags, setTags] = useState<string[]>([]);
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
    setValue,
  } = useForm<ArtifactFormData>({
    defaultValues: {
      name: '',
      description: '',
    },
  });

  // Reset form when modal opens/closes or artifact changes
  useEffect(() => {
    if (isOpen) {
      if (mode === 'edit' && artifact) {
        setValue('name', artifact.name);
        setValue('description', artifact.description || '');
        setTags(artifact.tags);
      } else {
        reset();
        setTags([]);
      }
    }
  }, [isOpen, mode, artifact, setValue, reset]);

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: CreateArtifactRequest) => apiClient.createArtifact(data),
    onSuccess: (newArtifact) => {
      // Optimistically add to cache
      queryClient.setQueryData(['artifacts'], (oldData: unknown) => {
        if (oldData && typeof oldData === 'object' && 'items' in oldData && 'total' in oldData) {
          const data = oldData as { items: Artifact[]; total: number };
          return {
            ...data,
            items: [newArtifact, ...data.items],
            total: data.total + 1,
          };
        }
        return oldData;
      });
      
      onSuccess();
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateArtifactRequest }) =>
      apiClient.updateArtifact(id, data),
    onSuccess: (updatedArtifact) => {
      // Optimistically update cache
      queryClient.setQueryData(['artifacts'], (oldData: unknown) => {
        if (oldData && typeof oldData === 'object' && 'items' in oldData) {
          const data = oldData as { items: Artifact[] };
          return {
            ...data,
            items: data.items.map((item: Artifact) =>
              item.id === updatedArtifact.id ? updatedArtifact : item
            ),
          };
        }
        return oldData;
      });
      
      onSuccess();
    },
  });

  const onSubmit = async (data: ArtifactFormData) => {
    // Basic validation
    if (!data.name.trim()) {
      return;
    }

    const formData = {
      name: data.name.trim(),
      description: data.description?.trim() || null,
      tags,
      metadata: {},
    };

    if (mode === 'create') {
      await createMutation.mutateAsync(formData);
    } else if (mode === 'edit' && artifact) {
      await updateMutation.mutateAsync({
        id: artifact.id,
        data: formData,
      });
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      onClose();
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;
  const error = createMutation.error || updateMutation.error;

  return (
    <Dialog open={isOpen} onClose={handleClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/25" />
      
      <div className="fixed inset-0 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center p-4 text-center">
          <DialogPanel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
            <div className="flex items-center justify-between mb-4">
              <DialogTitle as="h3" className="text-lg font-medium leading-6 text-gray-900">
                {mode === 'create' ? 'Create Artifact' : 'Edit Artifact'}
              </DialogTitle>
              <button
                onClick={handleClose}
                disabled={isSubmitting}
                className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">
                  {error instanceof Error ? error.message : 'An error occurred'}
                </p>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {/* Name Field */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Name *
                </label>
                <input
                  {...register('name', { 
                    required: 'Name is required',
                    maxLength: { value: 255, message: 'Name must be less than 255 characters' }
                  })}
                  type="text"
                  id="name"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  placeholder="Enter artifact name"
                />
                {errors.name && (
                  <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                )}
              </div>

              {/* Description Field */}
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  {...register('description')}
                  id="description"
                  rows={3}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  placeholder="Enter artifact description"
                />
                {errors.description && (
                  <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
                )}
              </div>

              {/* Tags Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tags
                </label>
                <TagInput
                  tags={tags}
                  onChange={setTags}
                  placeholder="Add tags..."
                  className="w-full"
                />
              </div>

              {/* Actions */}
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={isSubmitting}
                  className="inline-flex justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      {mode === 'create' ? 'Creating...' : 'Updating...'}
                    </>
                  ) : (
                    mode === 'create' ? 'Create' : 'Update'
                  )}
                </button>
              </div>
            </form>
          </DialogPanel>
        </div>
      </div>
    </Dialog>
  );
}