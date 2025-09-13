'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PencilIcon, TrashIcon, TagIcon } from '@heroicons/react/24/outline';
import { apiClient, PaginatedResponse } from '@/lib/api-client';
import { Artifact, ArtifactSearchQuery } from '@ghostworks/shared';
import { ArtifactModal } from './artifact-modal';
import { SearchBar } from './search-bar';
import { Pagination } from './pagination';

interface ArtifactListProps {
  searchQuery: ArtifactSearchQuery;
  onSearchChange: (query: ArtifactSearchQuery) => void;
}

export function ArtifactList({ searchQuery, onSearchChange }: ArtifactListProps) {
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  
  const queryClient = useQueryClient();

  // Fetch artifacts with React Query
  const { data, isLoading, error } = useQuery({
    queryKey: ['artifacts', searchQuery],
    queryFn: () => apiClient.getArtifacts(searchQuery),
    staleTime: 30000, // 30 seconds
  });

  // Delete mutation with optimistic updates
  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.deleteArtifact(id),
    onMutate: async (deletedId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['artifacts'] });

      // Snapshot previous value
      const previousData = queryClient.getQueryData<PaginatedResponse<Artifact>>(['artifacts', searchQuery]);

      // Optimistically update
      if (previousData) {
        queryClient.setQueryData(['artifacts', searchQuery], {
          ...previousData,
          items: previousData.items.filter(artifact => artifact.id !== deletedId),
          total: previousData.total - 1,
        });
      }

      return { previousData };
    },
    onError: (err, deletedId, context) => {
      // Rollback on error
      if (context?.previousData) {
        queryClient.setQueryData(['artifacts', searchQuery], context.previousData);
      }
    },
    onSettled: () => {
      // Refetch after mutation
      queryClient.invalidateQueries({ queryKey: ['artifacts'] });
    },
  });

  const handleEdit = (artifact: Artifact) => {
    setSelectedArtifact(artifact);
    setModalMode('edit');
    setIsModalOpen(true);
  };

  const handleCreate = () => {
    setSelectedArtifact(null);
    setModalMode('create');
    setIsModalOpen(true);
  };

  const handleDelete = async (artifact: Artifact) => {
    if (window.confirm(`Are you sure you want to delete "${artifact.name}"?`)) {
      deleteMutation.mutate(artifact.id);
    }
  };

  const handlePageChange = (newOffset: number) => {
    onSearchChange({ ...searchQuery, offset: newOffset });
  };

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-2">Error loading artifacts</div>
        <div className="text-sm text-gray-500">
          {error instanceof Error ? error.message : 'An unexpected error occurred'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search and Create */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
        <SearchBar 
          searchQuery={searchQuery} 
          onSearchChange={onSearchChange}
        />
        <button
          onClick={handleCreate}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Create Artifact
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <div className="mt-2 text-sm text-gray-500">Loading artifacts...</div>
        </div>
      )}

      {/* Empty State */}
      {data && data.items.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <TagIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No artifacts</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchQuery.q || searchQuery.tags?.length 
              ? 'No artifacts match your search criteria.' 
              : 'Get started by creating your first artifact.'
            }
          </p>
          <div className="mt-6">
            <button
              onClick={handleCreate}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Create Artifact
            </button>
          </div>
        </div>
      )}

      {/* Artifact Grid */}
      {data && data.items.length > 0 && (
        <>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((artifact) => (
              <div
                key={artifact.id}
                className="bg-white overflow-hidden shadow rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
              >
                <div className="p-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-medium text-gray-900 truncate">
                      {artifact.name}
                    </h3>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleEdit(artifact)}
                        className="text-gray-400 hover:text-indigo-600 transition-colors"
                        title="Edit artifact"
                      >
                        <PencilIcon className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => handleDelete(artifact)}
                        className="text-gray-400 hover:text-red-600 transition-colors"
                        title="Delete artifact"
                        disabled={deleteMutation.isPending}
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                  
                  {artifact.description && (
                    <p className="mt-2 text-sm text-gray-600 line-clamp-3">
                      {artifact.description}
                    </p>
                  )}
                  
                  {artifact.tags.length > 0 && (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {artifact.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
                        >
                          {tag}
                        </span>
                      ))}
                      {artifact.tags.length > 3 && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          +{artifact.tags.length - 3} more
                        </span>
                      )}
                    </div>
                  )}
                  
                  <div className="mt-4 text-xs text-gray-500">
                    Created {new Date(artifact.createdAt).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          <Pagination
            total={data.total}
            limit={searchQuery.limit || 20}
            offset={searchQuery.offset || 0}
            onPageChange={handlePageChange}
          />
        </>
      )}

      {/* Modal */}
      <ArtifactModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        mode={modalMode}
        artifact={selectedArtifact}
        onSuccess={() => {
          setIsModalOpen(false);
          queryClient.invalidateQueries({ queryKey: ['artifacts'] });
        }}
      />
    </div>
  );
}