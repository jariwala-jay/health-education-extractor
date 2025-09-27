"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/api";
import { 
  PencilIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  MagnifyingGlassIcon,
  FunnelIcon
} from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';
import Link from 'next/link';
import { parseUTCTimestamp } from '@/lib/utils';

interface DailyTip {
  id: string;
  tip_text: string;
  category: "Hypertension" | "Obesity" | "Diabetes" | "Prediabetes" | "Nutrition" | "General";
  tags: string[];
  source_article_id?: string;
  source_article_title?: string;
  image_url?: string;
  processing_status: "draft" | "reviewed" | "approved" | "uploaded" | "rejected";
  app_tip_id?: string;
  reading_level_score?: number;
  created_at: string;
  updated_at: string;
  reviewed_at?: string;
  reviewer_notes?: string;
}

interface TipsListResponse {
  tips: DailyTip[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export default function TipsPage() {
  const { user } = useAuth();
  const [tips, setTips] = useState<DailyTip[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [perPage] = useState(10);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [tagFilter, setTagFilter] = useState<string>("");
  const [processingActions, setProcessingActions] = useState<Set<string>>(new Set());

  const fetchTips = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: perPage.toString(),
      });
      
      if (statusFilter) params.append("processing_status", statusFilter);
      if (tagFilter) params.append("tags", tagFilter);

      const response = await apiClient.get(`/api/v1/tips?${params}`);
      const data: TipsListResponse = response.data;
      
      setTips(data.tips);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error("Error fetching tips:", err);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, statusFilter, tagFilter]);

  useEffect(() => {
    if (user) {
      fetchTips();
    }
  }, [user, fetchTips]);

  const updateTipStatus = async (tipId: string, status: string, notes?: string) => {
    if (processingActions.has(tipId)) return;
    
    try {
      setProcessingActions(prev => new Set(prev).add(tipId));
      await apiClient.put(`/api/v1/tips/${tipId}`, {
        processing_status: status,
        reviewer_notes: notes,
      });
      
      // Update local state
      setTips(tips.map(tip => 
        tip.id === tipId 
          ? { ...tip, processing_status: status as "draft" | "reviewed" | "approved" | "uploaded" | "rejected", reviewer_notes: notes }
          : tip
      ));
      
      toast.success(`Tip ${status} successfully`);
    } catch (err) {
      console.error("Error updating tip:", err);
      toast.error("Failed to update tip status");
    } finally {
      setProcessingActions(prev => {
        const next = new Set(prev);
        next.delete(tipId);
        return next;
      });
    }
  };


  const getStatusColor = (status: string) => {
    switch (status) {
      case "draft": return "bg-gray-100 text-gray-800";
      case "reviewed": return "bg-blue-100 text-blue-800";
      case "approved": return "bg-green-100 text-green-800";
      case "uploaded": return "bg-purple-100 text-purple-800";
      case "rejected": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  // Filter tips based on search
  const filteredTips = tips.filter(tip => {
    const matchesSearch = searchTerm === '' || 
      tip.tip_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tip.tags.some(tag => 
        tag.toLowerCase().includes(searchTerm.toLowerCase())
      );
    
    return matchesSearch;
  });

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="mb-8">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-10 bg-gray-200 rounded w-full mb-4"></div>
          <div className="flex space-x-4">
            <div className="h-10 bg-gray-200 rounded w-40"></div>
            <div className="h-10 bg-gray-200 rounded w-40"></div>
          </div>
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-white shadow rounded-lg p-6">
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="h-20 bg-gray-200 rounded w-full"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:tracking-tight">
          Daily Tips
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          Review and manage generated daily health tips
        </p>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        {/* Search */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            placeholder="Search tips by content or tags..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex items-center space-x-2">
            <FunnelIcon className="h-5 w-5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="block pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 rounded-md"
            >
              <option value="">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="reviewed">Reviewed</option>
              <option value="approved">Approved</option>
              <option value="uploaded">Uploaded</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>

          <input
            type="text"
            placeholder="Filter by tags (e.g., diabetes, exercise)"
            value={tagFilter}
            onChange={(e) => setTagFilter(e.target.value)}
            className="block w-full pl-3 pr-3 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 rounded-md"
          />

          {(statusFilter || tagFilter || searchTerm) && (
            <button
              onClick={() => {
                setStatusFilter('');
                setTagFilter('');
                setSearchTerm('');
                setPage(1);
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Results count and active filters */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-700">
            Showing {filteredTips.length} of {total} tips
          </p>
          
          {/* Active filters */}
          {(statusFilter || tagFilter || searchTerm) && (
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-gray-500">Filters:</span>
              {searchTerm && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  Search: {searchTerm}
                </span>
              )}
              {statusFilter && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  {statusFilter}
                </span>
              )}
              {tagFilter && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                  Tags: {tagFilter}
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Tips List */}
      {filteredTips.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">
            {tips.length === 0 ? 'No tips found.' : 'No tips match your search criteria.'}
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {filteredTips.map((tip) => (
            <div key={tip.id} className="bg-white shadow rounded-lg overflow-hidden">
              <div className="px-6 py-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getStatusColor(tip.processing_status)}`}>
                        {tip.processing_status}
                      </span>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        tip.category === 'Hypertension' ? 'bg-red-100 text-red-800' :
                        tip.category === 'Diabetes' ? 'bg-orange-100 text-orange-800' :
                        tip.category === 'Obesity' ? 'bg-yellow-100 text-yellow-800' :
                        tip.category === 'Nutrition' ? 'bg-green-100 text-green-800' :
                        tip.category === 'Prediabetes' ? 'bg-amber-100 text-amber-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {tip.category}
                      </span>
                      {tip.reading_level_score && (
                        <span className="text-sm text-gray-500">
                          Reading Level: {tip.reading_level_score.toFixed(1)}
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center text-sm text-gray-500 space-x-4 mb-3">
                      <span>
                        Created {tip.created_at ? formatDistanceToNow(parseUTCTimestamp(tip.created_at), { addSuffix: true }) : 'Recently'}
                      </span>
                      {tip.source_article_title ? (
                        <span>
                          Source: {tip.source_article_title}
                        </span>
                      ) : tip.source_article_id ? (
                        <span className="text-gray-400">
                          Source: Article (deleted)
                        </span>
                      ) : null}
                    </div>

                    <p className="text-gray-700 text-sm mb-3">
                      {tip.tip_text}
                    </p>

                    {tip.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {tip.tags.slice(0, 3).map((tag, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800"
                          >
                            {tag}
                          </span>
                        ))}
                        {tip.tags.length > 3 && (
                          <span className="text-xs text-gray-500">
                            +{tip.tags.length - 3} more
                          </span>
                        )}
                      </div>
                    )}

                    {tip.reviewer_notes && (
                      <div className="mt-3 p-3 bg-gray-50 rounded-md">
                        <p className="text-sm text-gray-700">
                          <strong>Reviewer Notes:</strong> {tip.reviewer_notes}
                        </p>
                      </div>
                    )}
                  </div>

                  {tip.image_url && (
                    <div className="ml-6 flex-shrink-0">
                      <img
                        src={tip.image_url}
                        alt="Tip illustration"
                        className="h-20 w-20 object-cover rounded-lg"
                      />
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <div className="flex space-x-3">
                    <Link
                      href={`/tips/${tip.id}/edit`}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      <PencilIcon className="h-4 w-4 mr-1" />
                      Edit
                    </Link>
                  </div>

                  {tip.processing_status !== 'approved' && tip.processing_status !== 'rejected' && (
                    <div className="flex space-x-2">
                      <button
                        onClick={() => updateTipStatus(tip.id, 'approved')}
                        disabled={processingActions.has(tip.id)}
                        className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <CheckCircleIcon className="h-4 w-4 mr-1" />
                        {processingActions.has(tip.id) ? 'Approving...' : 'Approve'}
                      </button>
                      <button
                        onClick={() => {
                          const notes = prompt("Rejection reason:");
                          if (notes) updateTipStatus(tip.id, 'rejected', notes);
                        }}
                        disabled={processingActions.has(tip.id)}
                        className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <XCircleIcon className="h-4 w-4 mr-1" />
                        {processingActions.has(tip.id) ? 'Rejecting...' : 'Reject'}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-8 flex justify-center">
          <div className="flex space-x-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="px-3 py-2 text-sm text-gray-700">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
