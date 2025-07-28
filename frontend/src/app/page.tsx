'use client';

import { useEffect, useState } from 'react';
import { 
  DocumentTextIcon, 
  CheckCircleIcon, 
  CloudArrowUpIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { healthCheck, listArticles, listPDFs, type HealthArticle, type PDFDocument } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';
import { parseUTCTimestamp } from '@/lib/utils';
import Link from 'next/link';
import toast from 'react-hot-toast';

export default function Dashboard() {
  const [healthStatus, setHealthStatus] = useState<'healthy' | 'unhealthy' | 'loading'>('loading');
  const [totalArticles, setTotalArticles] = useState<number>(0);
  const [approvedArticles, setApprovedArticles] = useState<number>(0);
  const [recentPDFs, setRecentPDFs] = useState<PDFDocument[]>([]);
  const [recentArticles, setRecentArticles] = useState<HealthArticle[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load health status
      try {
        await healthCheck();
        setHealthStatus('healthy');
      } catch {
        setHealthStatus('unhealthy');
      }

      // Load articles data (load more to get accurate counts)
      const articles = await listArticles(1, 100); // Load up to 100 articles for accurate counting
      setTotalArticles(articles.length);
      setApprovedArticles(articles.filter(a => a.processing_status === 'approved').length);
      setRecentArticles(articles.slice(0, 5));

      // Load recent PDFs
      const pdfData = await listPDFs(1, 5);
      setRecentPDFs(pdfData.documents);

    } catch (error) {
      console.error('Error loading dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600';
      case 'processing': return 'text-blue-600';
      case 'parsing': return 'text-yellow-600';
      case 'failed': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'processing': return <ExclamationTriangleIcon className="h-5 w-5 text-blue-500" />;
      case 'parsing': return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'failed': return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      default: return <DocumentTextIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <div className="mt-2 flex items-center space-x-2">
          <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            healthStatus === 'healthy' 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            {healthStatus === 'healthy' ? 'API Healthy' : 'API Unhealthy'}
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        {/* Total Articles */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <DocumentTextIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Articles
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {totalArticles}
                  </dd>
                </dl>
              </div>
            </div>
            <div className="mt-3">
              <Link 
                href="/articles"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
              >
                View all articles
              </Link>
            </div>
          </div>
        </div>

        {/* Approved Articles */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircleIcon className="h-6 w-6 text-green-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Approved Articles
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {approvedArticles}
                  </dd>
                </dl>
              </div>
            </div>
            <div className="mt-3">
              <Link 
                href="/export"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
              >
                Export articles
              </Link>
            </div>
          </div>
        </div>

        {/* Recent PDFs */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CloudArrowUpIcon className="h-6 w-6 text-blue-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Recent PDFs
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {recentPDFs.length}
                  </dd>
                </dl>
              </div>
            </div>
            <div className="mt-3">
              <Link 
                href="/upload"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
              >
                Upload new PDF
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Recent PDF Uploads */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Recent PDF Uploads
            </h3>
            {recentPDFs.length === 0 ? (
              <p className="text-sm text-gray-500">No PDFs uploaded yet.</p>
            ) : (
              <div className="space-y-3">
                {recentPDFs.map((pdf) => (
                  <div key={pdf.id} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(pdf.processing_status)}
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {pdf.filename}
                        </p>
                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <span className={getStatusColor(pdf.processing_status)}>
                            {pdf.processing_status}
                          </span>
                          {pdf.total_articles_generated && pdf.total_articles_generated > 0 && (
                            <span>• {pdf.total_articles_generated} articles</span>
                          )}
                        </div>
                        {pdf.total_articles_generated && pdf.total_articles_generated > 0 && (
                          <p className="text-xs mt-1">
                            <Link 
                              href={`/articles/pdf/${pdf.id}`}
                              className="text-indigo-600 hover:text-indigo-500"
                            >
                              View articles →
                            </Link>
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="text-right text-sm whitespace-nowrap text-gray-500">
                      {pdf.uploaded_at ? formatDistanceToNow(parseUTCTimestamp(pdf.uploaded_at), { addSuffix: true }) : 'Just now'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Articles */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Recent Articles
            </h3>
            {recentArticles.length === 0 ? (
              <p className="text-sm text-gray-500">No articles generated yet.</p>
            ) : (
              <div className="space-y-3">
                {recentArticles.map((article) => (
                  <div key={article.id} className="flex items-start justify-between">
                    <div className="min-w-0 flex-1">
                      <Link 
                        href={`/articles/${article.id}`}
                        className="text-sm font-medium text-gray-900 hover:text-indigo-600 block truncate"
                      >
                        {article.title}
                      </Link>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          {article.category}
                        </span>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          article.processing_status === 'approved' ? 'bg-green-100 text-green-800' :
                          article.processing_status === 'rejected' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {article.processing_status}
                        </span>
                      </div>
                    </div>
                    <div className="text-right text-sm whitespace-nowrap text-gray-500 ml-4">
                      {article.created_at ? formatDistanceToNow(parseUTCTimestamp(article.created_at), { addSuffix: true }) : 'Recently'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
