'use client';

import { useState, useEffect } from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { ArtifactSearchQuery } from '@ghostworks/shared';
import { TagInput } from './tag-input';

interface SearchBarProps {
  searchQuery: ArtifactSearchQuery;
  onSearchChange: (query: ArtifactSearchQuery) => void;
}

export function SearchBar({ searchQuery, onSearchChange }: SearchBarProps) {
  const [localQuery, setLocalQuery] = useState(searchQuery.q || '');
  const [localTags, setLocalTags] = useState(searchQuery.tags || []);

  // Debounced search effect
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearchChange({
        ...searchQuery,
        q: localQuery || undefined,
        tags: localTags,
        offset: 0, // Reset to first page when searching
      });
    }, 300);

    return () => clearTimeout(timer);
  }, [localQuery, localTags, onSearchChange, searchQuery]);

  const handleClearSearch = () => {
    setLocalQuery('');
    setLocalTags([]);
    onSearchChange({
      ...searchQuery,
      q: undefined,
      tags: [],
      offset: 0,
    });
  };

  const hasActiveFilters = localQuery || localTags.length > 0;

  return (
    <div className="flex-1 max-w-lg">
      <div className="space-y-3">
        {/* Text Search */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            placeholder="Search artifacts..."
            value={localQuery}
            onChange={(e) => setLocalQuery(e.target.value)}
            className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
          {hasActiveFilters && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
              <button
                onClick={handleClearSearch}
                className="text-gray-400 hover:text-gray-600 transition-colors"
                title="Clear search"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
          )}
        </div>

        {/* Tag Filter */}
        <TagInput
          tags={localTags}
          onChange={setLocalTags}
          placeholder="Filter by tags..."
          className="w-full"
        />
      </div>

      {/* Active Filters Summary */}
      {hasActiveFilters && (
        <div className="mt-2 flex items-center gap-2 text-sm text-gray-600">
          <span>Filters:</span>
          {localQuery && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Text: &ldquo;{localQuery}&rdquo;
            </span>
          )}
          {localTags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
            >
              Tag: {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}