'use client';

import { useState } from 'react';
import { MainLayout } from '@/components/layout/main-layout';
import { ArtifactList } from '@/components/artifacts/artifact-list';
import { ArtifactSearchQuery } from '@ghostworks/shared';

export default function Artifacts() {
  const [searchQuery, setSearchQuery] = useState<ArtifactSearchQuery>({
    limit: 20,
    offset: 0,
    tags: [],
  });

  return (
    <MainLayout>
      <div className="py-10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold leading-tight text-gray-900">
              Artifacts
            </h1>
            <p className="mt-4 text-lg text-gray-600">
              Manage your workspace artifacts. Create, search, and organize your
              SaaS entities.
            </p>
          </div>
          
          <ArtifactList 
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
          />
        </div>
      </div>
    </MainLayout>
  );
}
