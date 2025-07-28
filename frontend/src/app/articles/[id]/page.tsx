'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeftIcon,
  CheckCircleIcon,
  XCircleIcon,
  PencilIcon,
  TagIcon,
  CalendarIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import { getArticle, approveArticle, rejectArticle, type HealthArticle } from '@/lib/api';
import { getCategoryColor, getStatusColor } from '@/lib/constants';
import { formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';
import Link from 'next/link';
import { parseUTCTimestamp } from '@/lib/utils';

export default function ArticleDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [article, setArticle] = useState<HealthArticle | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  const articleId = params.id as string;

  useEffect(() => {
    if (articleId) {
      loadArticle();
    }
  }, [articleId]);

  const loadArticle = async () => {
    try {
      setLoading(true);
      const articleData = await getArticle(articleId);
      setArticle(articleData);
    } catch (error) {
      console.error('Error loading article:', error);
      toast.error('Failed to load article');
      router.push('/articles');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!article || processing) return;
    
    try {
      setProcessing(true);
      await approveArticle(article.id);
      setArticle({ ...article, processing_status: 'approved' });
      toast.success('Article approved successfully');
    } catch (error) {
      console.error('Error approving article:', error);
      toast.error('Failed to approve article');
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!article || processing) return;
    
    try {
      setProcessing(true);
      await rejectArticle(article.id);
      setArticle({ ...article, processing_status: 'rejected' });
      toast.success('Article rejected');
    } catch (error) {
      console.error('Error rejecting article:', error);
      toast.error('Failed to reject article');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="mb-8">
          <div className="h-4 bg-gray-200 rounded w-20 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="bg-white shadow rounded-lg p-6">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Article not found</p>
        <Link href="/articles" className="text-indigo-600 hover:text-indigo-500 mt-2 inline-block">
          ← Back to Articles
        </Link>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <Link
          href="/articles"
          className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-1" />
          Back to Articles
        </Link>
        
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
              {article.title}
            </h1>
            <div className="mt-2 flex items-center space-x-3">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(article.category)}`}>
                {article.category}
              </span>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getStatusColor(article.processing_status)}`}>
                {article.processing_status}
              </span>
              {article.reading_level_score && (
                <span className="text-xs text-gray-500">
                  Reading Level: {article.reading_level_score.toFixed(1)}
                </span>
              )}
            </div>
          </div>
          
          {article.image_url && (
            <div className="ml-6 flex-shrink-0">
              <img
                src={article.image_url}
                alt={article.title}
                className="h-32 w-32 object-cover rounded-lg shadow-md"
              />
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2">
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Article Content
              </h3>
              <div className="prose max-w-none">
                <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                  {article.content}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Actions */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Actions
              </h3>
              <div className="space-y-3">
                <Link
                  href={`/articles/${article.id}/edit`}
                  className="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <PencilIcon className="h-4 w-4 mr-2" />
                  Edit Article
                </Link>
                
                {article.processing_status !== 'approved' && article.processing_status !== 'rejected' && (
                  <>
                    <button
                      onClick={handleApprove}
                      disabled={processing}
                      className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <CheckCircleIcon className="h-4 w-4 mr-2" />
                      {processing ? 'Approving...' : 'Approve'}
                    </button>
                    <button
                      onClick={handleReject}
                      disabled={processing}
                      className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <XCircleIcon className="h-4 w-4 mr-2" />
                      {processing ? 'Rejecting...' : 'Reject'}
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Metadata */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Metadata
              </h3>
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm font-medium text-gray-500 flex items-center">
                    <CalendarIcon className="h-4 w-4 mr-1" />
                    Created
                  </dt>
                  <dd className="text-sm text-gray-900">
                    {article.created_at ? formatDistanceToNow(parseUTCTimestamp(article.created_at), { addSuffix: true }) : 'Recently'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500 flex items-center">
                    <CalendarIcon className="h-4 w-4 mr-1" />
                    Last Updated
                  </dt>
                  <dd className="text-sm text-gray-900">
                    {article.updated_at ? formatDistanceToNow(parseUTCTimestamp(article.updated_at), { addSuffix: true }) : 'Recently'}
                  </dd>
                </div>
                {article.reading_level_score && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500 flex items-center">
                      <EyeIcon className="h-4 w-4 mr-1" />
                      Reading Level
                    </dt>
                    <dd className="text-sm text-gray-900">
                      Grade {article.reading_level_score.toFixed(1)}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          </div>

          {/* Medical Tags */}
          {article.medical_condition_tags.length > 0 && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4 flex items-center">
                  <TagIcon className="h-5 w-5 mr-2" />
                  Medical Tags
                </h3>
                <div className="flex flex-wrap gap-2">
                  {article.medical_condition_tags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 