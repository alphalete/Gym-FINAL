import React from 'react';

// Basic skeleton loader component
export const SkeletonBox = ({ className = '', width = 'w-full', height = 'h-4' }) => (
  <div className={`animate-pulse bg-gray-200 rounded ${width} ${height} ${className}`}></div>
);

// Skeleton for stat cards
export const StatCardSkeleton = () => (
  <div className="bg-white rounded-xl shadow-sm p-3 md:p-4 animate-pulse">
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-full bg-gray-200"></div>
      <div className="flex-1">
        <div className="h-6 bg-gray-200 rounded mb-2 w-16"></div>
        <div className="h-3 bg-gray-200 rounded w-20"></div>
      </div>
    </div>
  </div>
);

// Skeleton for large stat cards (Reports page)
export const LargeStatCardSkeleton = () => (
  <div className="stat-card bg-gray-200 animate-pulse">
    <div className="flex items-center justify-between">
      <div className="flex-1">
        <div className="h-8 bg-gray-300 rounded mb-2 w-24"></div>
        <div className="h-4 bg-gray-300 rounded w-32"></div>
        <div className="h-3 bg-gray-300 rounded w-20 mt-2"></div>
      </div>
      <div className="w-10 h-10 bg-gray-300 rounded"></div>
    </div>
  </div>
);

// Skeleton for member cards
export const MemberCardSkeleton = () => (
  <div className="card mb-3 animate-pulse">
    <div className="card-body">
      <div className="flex items-center gap-3 mb-4">
        <div className="h-12 w-12 rounded-full bg-gray-200"></div>
        <div className="flex-1">
          <div className="h-4 bg-gray-200 rounded mb-2 w-32"></div>
          <div className="h-3 bg-gray-200 rounded w-48 mb-1"></div>
          <div className="h-3 bg-gray-200 rounded w-36"></div>
        </div>
      </div>
      <div className="flex flex-wrap gap-3 justify-center">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="w-16 h-20 bg-gray-200 rounded"></div>
        ))}
      </div>
    </div>
  </div>
);

// Skeleton for payment history items
export const PaymentItemSkeleton = () => (
  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg animate-pulse">
    <div className="flex items-center space-x-4">
      <div className="w-12 h-12 bg-gray-200 rounded-full"></div>
      <div>
        <div className="h-4 bg-gray-200 rounded mb-2 w-32"></div>
        <div className="h-3 bg-gray-200 rounded w-24"></div>
      </div>
    </div>
    <div className="text-right">
      <div className="h-5 bg-gray-200 rounded mb-1 w-16"></div>
      <div className="h-4 bg-gray-200 rounded w-12"></div>
    </div>
  </div>
);

// Skeleton for list items (like plan rankings)
export const ListItemSkeleton = ({ showRank = false }) => (
  <div className="flex justify-between items-center p-3 animate-pulse">
    <div className="flex items-center">
      {showRank && <div className="w-6 h-6 rounded-full bg-gray-200 mr-2"></div>}
      <div>
        <div className="h-4 bg-gray-200 rounded mb-1 w-24"></div>
        <div className="h-3 bg-gray-200 rounded w-16"></div>
      </div>
    </div>
    <div className="h-4 bg-gray-200 rounded w-8"></div>
  </div>
);

// Skeleton for charts/analytics sections
export const AnalyticsSkeleton = () => (
  <div className="card animate-pulse">
    <div className="card-header">
      <div className="h-6 bg-gray-200 rounded w-40"></div>
    </div>
    <div className="card-body">
      <div className="space-y-4">
        {[...Array(4)].map((_, i) => (
          <ListItemSkeleton key={i} showRank={i < 3} />
        ))}
      </div>
    </div>
  </div>
);

// Complete dashboard skeleton
export const DashboardSkeleton = () => (
  <div className="min-h-screen bg-slate-50">
    <div className="bg-card shadow-sm border-b">
      <div className="container px-4 sm:px-6 py-4 sm:py-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
          <div>
            <div className="h-8 bg-gray-200 rounded w-48 mb-2 animate-pulse"></div>
            <div className="h-4 bg-gray-200 rounded w-96 animate-pulse"></div>
          </div>
          <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
            <div className="h-10 bg-gray-200 rounded w-32 animate-pulse"></div>
            <div className="h-10 bg-gray-200 rounded w-32 animate-pulse"></div>
          </div>
        </div>
      </div>
    </div>

    <div className="container px-4 sm:px-6 py-4 sm:py-6">
      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4 mb-6">
        {[...Array(4)].map((_, i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>

      {/* Alerts Section Skeleton */}
      <div className="mb-6">
        <div className="bg-card rounded-xl shadow-sm">
          <div className="p-4 border-b border-gray-200 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-40"></div>
          </div>
          <div className="p-4">
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="bg-card rounded-xl shadow-sm px-3 py-2 md:p-3 flex items-center justify-between animate-pulse">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-full bg-gray-200"></div>
                    <div>
                      <div className="h-4 bg-gray-200 rounded mb-1 w-32"></div>
                      <div className="h-3 bg-gray-200 rounded w-48"></div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="h-5 bg-gray-200 rounded w-16"></div>
                    <div className="h-8 w-8 bg-gray-200 rounded-lg"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <AnalyticsSkeleton />
        <AnalyticsSkeleton />
      </div>
    </div>
  </div>
);

// Complete reports skeleton
export const ReportsSkeleton = () => (
  <div className="min-h-screen bg-gray-50">
    <div className="bg-white shadow-sm border-b">
      <div className="px-6 py-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="h-8 bg-gray-200 rounded w-64 mb-2 animate-pulse"></div>
            <div className="h-4 bg-gray-200 rounded w-96 animate-pulse"></div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="h-4 bg-gray-200 rounded w-20 animate-pulse"></div>
            <div className="h-8 bg-gray-200 rounded w-32 animate-pulse"></div>
          </div>
        </div>
      </div>
    </div>

    <div className="px-6 py-6">
      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
        {[...Array(4)].map((_, i) => (
          <LargeStatCardSkeleton key={i} />
        ))}
      </div>

      {/* Detailed Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
        {[...Array(3)].map((_, i) => (
          <AnalyticsSkeleton key={i} />
        ))}
      </div>

      {/* Recent Activity */}
      <div className="card">
        <div className="card-header animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-48"></div>
        </div>
        <div className="card-body">
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <PaymentItemSkeleton key={i} />
            ))}
          </div>
        </div>
      </div>
    </div>
  </div>
);

export default {
  SkeletonBox,
  StatCardSkeleton,
  LargeStatCardSkeleton,
  MemberCardSkeleton,
  PaymentItemSkeleton,
  ListItemSkeleton,
  AnalyticsSkeleton,
  DashboardSkeleton,
  ReportsSkeleton
};