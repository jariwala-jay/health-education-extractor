'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeftIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { getArticle, updateArticle, type HealthArticle } from '@/lib/api';
import { HEALTH_CATEGORIES } from '@/lib/constants';
import toast from 'react-hot-toast';
import Link from 'next/link';

export default function ArticleEditPage() {
  const params = useParams();
  const router = useRouter();
  const [article, setArticle] = useState<HealthArticle | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Form state
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('');
  const [content, setContent] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [medicalTags, setMedicalTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');

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
      
      // Populate form
      setTitle(articleData.title);
      setCategory(articleData.category);
      setContent(articleData.content);
      setImageUrl(articleData.image_url || '');
      setMedicalTags(articleData.medical_condition_tags);
    } catch (error) {
      console.error('Error loading article:', error);
      toast.error('Failed to load article');
      router.push('/articles');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!article || saving) return;
    
    // Validation
    if (!title.trim()) {
      toast.error('Title is required');
      return;
    }
    
    if (!content.trim()) {
      toast.error('Content is required');
      return;
    }
    
    try {
      setSaving(true);
      
      const updates = {
        title: title.trim(),
        category,
        content: content.trim(),
        image_url: imageUrl.trim() || undefined,
        medical_condition_tags: medicalTags.filter(tag => tag.trim())
      };
      
      const updatedArticle = await updateArticle(article.id, updates);
      setArticle(updatedArticle);
      
      toast.success('Article updated successfully');
      router.push(`/articles/${article.id}`);
    } catch (error) {
      console.error('Error updating article:', error);
      toast.error('Failed to update article');
    } finally {
      setSaving(false);
    }
  };

  const handleAddTag = () => {
    if (newTag.trim() && !medicalTags.includes(newTag.trim())) {
      setMedicalTags([...medicalTags, newTag.trim()]);
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setMedicalTags(medicalTags.filter(tag => tag !== tagToRemove));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="mb-8">
          <div className="h-4 bg-gray-200 rounded w-20 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="bg-white shadow rounded-lg p-6">
          <div className="space-y-6">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
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
          href={`/articles/${article.id}`}
          className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-1" />
          Back to Article
        </Link>
        
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Edit Article
          </h1>
          
          <div className="flex space-x-3">
            <Link
              href={`/articles/${article.id}`}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <XMarkIcon className="h-4 w-4 mr-2" />
              Cancel
            </Link>
            <button
              onClick={handleSave}
              disabled={saving}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CheckIcon className="h-4 w-4 mr-2" />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>

      {/* Form */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="space-y-6">
            {/* Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                Title
              </label>
              <input
                type="text"
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter article title..."
              />
            </div>

            {/* Category */}
            <div>
              <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
                Category
              </label>
              <select
                id="category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                {HEALTH_CATEGORIES.map(cat => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            {/* Image URL */}
            <div>
              <label htmlFor="imageUrl" className="block text-sm font-medium text-gray-700 mb-2">
                Image URL (optional)
              </label>
              <input
                type="url"
                id="imageUrl"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="https://example.com/image.jpg"
              />
              {imageUrl && (
                <div className="mt-2">
                  <img
                    src={imageUrl}
                    alt="Preview"
                    className="h-32 w-32 object-cover rounded-lg"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                </div>
              )}
            </div>

            {/* Content */}
            <div>
              <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-2">
                Content
              </label>
              <textarea
                id="content"
                rows={12}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter article content..."
              />
              <p className="mt-1 text-sm text-gray-500">
                Write in simple, easy-to-understand language suitable for a 6th-grade reading level.
              </p>
            </div>

            {/* Medical Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Medical Condition Tags
              </label>
              
              {/* Add new tag */}
              <div className="flex space-x-2 mb-3">
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Add a medical tag..."
                />
                <button
                  type="button"
                  onClick={handleAddTag}
                  className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Add
                </button>
              </div>

              {/* Existing tags */}
              {medicalTags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {medicalTags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 inline-flex items-center justify-center w-4 h-4 rounded-full text-blue-400 hover:bg-blue-200 hover:text-blue-600 focus:outline-none"
                      >
                        <XMarkIcon className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Character/Word Count */}
      <div className="mt-4 text-sm text-gray-500 text-right">
        Content: {content.length} characters, ~{Math.ceil(content.split(/\s+/).length)} words
      </div>
    </div>
  );
} 