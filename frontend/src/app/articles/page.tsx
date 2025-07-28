'use client';

import { useEffect, useState } from 'react';
import { 
  EyeIcon, 
  PencilIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  MagnifyingGlassIcon,
  FunnelIcon
} from '@heroicons/react/24/outline';
import { listArticles, approveArticle, rejectArticle, listPDFs, type HealthArticle, type PDFDocument } from '@/lib/api';
import { HEALTH_CATEGORIES, getCategoryColor, getStatusColor } from '@/lib/constants';
import { formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';
import Link from 'next/link';
import { parseUTCTimestamp } from '@/lib/utils';

export default function ArticlesPage() {
  const [articles, setArticles] = useState<HealthArticle[]>([]);
  const [pdfs, setPdfs] = useState<PDFDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedPdf, setSelectedPdf] = useState('');
  const [processingActions, setProcessingActions] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadArticles();
    loadPDFs();
  }, []);

  const loadPDFs = async () => {
    try {
      const pdfData = await listPDFs(1, 100); // Get up to 100 PDFs
      setPdfs(pdfData.documents);
    } catch (error) {
      console.error('Error loading PDFs:', error);
      toast.error('Failed to load PDFs');
    }
  };

  const loadArticles = async () => {
    try {
      setLoading(true);
      const articles = await listArticles(1, 100); // Load more articles to include approved ones
      setArticles(articles);
    } catch (error) {
      console.error('Error loading articles:', error);
      toast.error('Failed to load articles');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (articleId: string) => {
    if (processingActions.has(articleId)) return;
    
    try {
      setProcessingActions(prev => new Set(prev).add(articleId));
      await approveArticle(articleId);
      
      // Update local state
      setArticles(articles.map(article => 
        article.id === articleId 
          ? { ...article, processing_status: 'approved' }
          : article
      ));
      
      toast.success('Article approved');
    } catch (error) {
      console.error('Error approving article:', error);
      toast.error('Failed to approve article');
    } finally {
      setProcessingActions(prev => {
        const next = new Set(prev);
        next.delete(articleId);
        return next;
      });
    }
  };

  const handleReject = async (articleId: string) => {
    if (processingActions.has(articleId)) return;
    
    try {
      setProcessingActions(prev => new Set(prev).add(articleId));
      await rejectArticle(articleId);
      
      // Update local state
      setArticles(articles.map(article => 
        article.id === articleId 
          ? { ...article, processing_status: 'rejected' }
          : article
      ));
      
      toast.success('Article rejected');
    } catch (error) {
      console.error('Error rejecting article:', error);
      toast.error('Failed to reject article');
    } finally {
      setProcessingActions(prev => {
        const next = new Set(prev);
        next.delete(articleId);
        return next;
      });
    }
  };

  // Filter articles based on search and filters
  const filteredArticles = articles.filter(article => {
    const matchesSearch = searchTerm === '' || 
      article.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      article.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      article.medical_condition_tags.some(tag => 
        tag.toLowerCase().includes(searchTerm.toLowerCase())
      );
    
    const matchesCategory = selectedCategory === '' || article.category === selectedCategory;
    const matchesStatus = selectedStatus === '' || article.processing_status === selectedStatus;
    const matchesPdf = selectedPdf === '' || article.source_pdf_id === selectedPdf;
    
    return matchesSearch && matchesCategory && matchesStatus && matchesPdf;
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
          Health Articles
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          Review and manage generated health education articles
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
            placeholder="Search articles by title, content, or tags..."
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
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="block pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 rounded-md"
            >
              <option value="">All Categories</option>
              {HEALTH_CATEGORIES.map(category => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 rounded-md"
          >
            <option value="">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="reviewed">Reviewed</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>

          <select
            value={selectedPdf}
            onChange={(e) => setSelectedPdf(e.target.value)}
            className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 rounded-md"
          >
            <option value="">All PDFs</option>
            {pdfs.map(pdf => (
              <option key={pdf.id} value={pdf.id}>
                {pdf.filename}
              </option>
            ))}
          </select>

          {(selectedCategory || selectedStatus || selectedPdf || searchTerm) && (
            <button
              onClick={() => {
                setSelectedCategory('');
                setSelectedStatus('');
                setSelectedPdf('');
                setSearchTerm('');
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
            Showing {filteredArticles.length} of {articles.length} articles
          </p>
          
          {/* Active filters */}
          {(selectedCategory || selectedStatus || selectedPdf || searchTerm) && (
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-gray-500">Filters:</span>
              {searchTerm && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  Search: {searchTerm}
                </span>
              )}
              {selectedCategory && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  {selectedCategory}
                </span>
              )}
              {selectedStatus && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  {selectedStatus}
                </span>
              )}
              {selectedPdf && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                  PDF: {pdfs.find(p => p.id === selectedPdf)?.filename || 'Unknown'}
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Articles List */}
      {filteredArticles.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">
            {articles.length === 0 ? 'No articles found.' : 'No articles match your search criteria.'}
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {filteredArticles.map((article) => (
            <div key={article.id} className="bg-white shadow rounded-lg overflow-hidden">
              <div className="px-6 py-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-medium text-gray-900 truncate">
                        {article.title}
                      </h3>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(article.category)}`}>
                        {article.category}
                      </span>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getStatusColor(article.processing_status)}`}>
                        {article.processing_status}
                      </span>
                    </div>
                    
                    <div className="flex items-center text-sm text-gray-500 space-x-4 mb-3">
                      <span>
                        Created {article.created_at ? formatDistanceToNow(parseUTCTimestamp(article.created_at), { addSuffix: true }) : 'Recently'}
                      </span>
                      {article.reading_level_score && (
                        <span>
                          Reading Level: {article.reading_level_score.toFixed(1)}
                        </span>
                      )}
                    </div>

                    <p className="text-gray-700 text-sm line-clamp-3 mb-3">
                      {article.content.substring(0, 200)}...
                    </p>

                    {article.medical_condition_tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {article.medical_condition_tags.slice(0, 3).map((tag, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800"
                          >
                            {tag}
                          </span>
                        ))}
                        {article.medical_condition_tags.length > 3 && (
                          <span className="text-xs text-gray-500">
                            +{article.medical_condition_tags.length - 3} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {article.image_url && (
                    <div className="ml-6 flex-shrink-0">
                      <img
                        src={article.image_url}
                        alt={article.title}
                        className="h-20 w-20 object-cover rounded-lg"
                      />
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <div className="flex space-x-3">
                    <Link
                      href={`/articles/${article.id}`}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      <EyeIcon className="h-4 w-4 mr-1" />
                      View
                    </Link>
                    <Link
                      href={`/articles/${article.id}/edit`}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      <PencilIcon className="h-4 w-4 mr-1" />
                      Edit
                    </Link>
                  </div>

                  {article.processing_status !== 'approved' && article.processing_status !== 'rejected' && (
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleApprove(article.id)}
                        disabled={processingActions.has(article.id)}
                        className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <CheckCircleIcon className="h-4 w-4 mr-1" />
                        {processingActions.has(article.id) ? 'Approving...' : 'Approve'}
                      </button>
                      <button
                        onClick={() => handleReject(article.id)}
                        disabled={processingActions.has(article.id)}
                        className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <XCircleIcon className="h-4 w-4 mr-1" />
                        {processingActions.has(article.id) ? 'Rejecting...' : 'Reject'}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
} 