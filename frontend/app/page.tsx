'use client';

import { useState, useEffect } from 'react';
import { Ingredient, PlatformSummary, Stage } from '@/lib/types';
import { api } from '@/lib/api-client';
import { IngredientCard } from '@/components/IngredientCard';
import { PlatformCard } from '@/components/PlatformCard';
import { KeywordChips } from '@/components/KeywordChips';
import { useJobStatus } from '@/hooks/useJobStatus';
import { useAuth } from '@/hooks/useAuth';
import { getPreferences } from '@/lib/api';

export default function Home() {
  const [stage, setStage] = useState<Stage>('search');
  const [recipeName, setRecipeName] = useState('');
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [platforms, setPlatforms] = useState<PlatformSummary[]>([]);
  const [preferences, setPreferences] = useState<string[]>([]);
  
  const { data: jobStatus } = useJobStatus(jobId);
  const { token } = useAuth();
  
  // Load user preferences on mount
  useEffect(() => {
    if (token) {
      getPreferences(token).then(setPreferences).catch(() => {});
    }
  }, [token]);
  
  // Stage 1: Search for recipe
  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getRecipeIngredients(recipeName);
      setIngredients(result.ingredients);
      setStage('edit');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Stage 2: Update ingredient
  const handleIngredientChange = (index: number, updated: Ingredient) => {
    const newIngredients = [...ingredients];
    newIngredients[index] = updated;
    setIngredients(newIngredients);
  };
  
  // Stage 2: Delete ingredient
  const handleIngredientDelete = (index: number) => {
    setIngredients(ingredients.filter((_, i) => i !== index));
  };
  
  // Stage 2: Submit order
  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      // Save shopping list
      await api.saveShoppingList(ingredients);
      // Start driver
      const driverResult = await api.startDriver();
      setJobId(driverResult.job_id);
      setStage('results');
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };
  
  // Stage 3: Load comparison results
  const loadComparison = async () => {
    if (!jobId) return;
    try {
      const result = await api.getComparison(jobId);
      setPlatforms(result.platforms);
    } catch (err: any) {
      console.error('Error loading comparison:', err);
    }
  };
  
  // Monitor job status
  if (jobStatus?.status === 'success' && platforms.length === 0) {
    loadComparison();
  }
  
  // Reset to stage 1
  const handleReset = () => {
    setStage('search');
    setRecipeName('');
    setIngredients([]);
    setJobId(null);
    setPlatforms([]);
    setError(null);
  };
  
  return (
    <div className="min-h-screen bg-gray-100 py-8 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Recipe Cart Optimizer
          </h1>
          <div className="flex items-center justify-center gap-2 text-sm text-gray-600">
            <span className="px-2 py-1 bg-blue-100 rounded">🔵 Knot</span>
            <span className="px-2 py-1 bg-blue-100 rounded">Y</span>
            <span className="px-2 py-1 bg-orange-100 rounded">R</span>
            <span className="px-2 py-1 bg-orange-100 rounded">O</span>
          </div>
        </div>
        
        {/* Stage 1: Recipe Search */}
        {stage === 'search' && (
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-semibold mb-4 text-center">
              What recipe or ingredients do you want to order?
            </h2>
            
            {/* Phase 3: Recommendations */}
            {preferences.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Recommended for you:</h3>
                <KeywordChips keywords={preferences} />
              </div>
            )}
            
            <div className="flex gap-4">
              <input
                type="text"
                value={recipeName}
                onChange={(e) => setRecipeName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !loading && handleSearch()}
                placeholder="Enter recipe name..."
                className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-green-500"
              />
              <button
                onClick={handleSearch}
                disabled={loading || !recipeName}
                className="px-8 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Loading...' : 'Review Ingredients'}
              </button>
            </div>
            {error && (
              <p className="mt-4 text-red-600 text-center">{error}</p>
            )}
          </div>
        )}
        
        {/* Stage 2: Ingredient Edit */}
        {stage === 'edit' && (
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-semibold mb-6">
              Edit your ingredients
            </h2>
            <div className="space-y-3 max-h-96 overflow-y-auto mb-6">
              {ingredients.map((ingredient, index) => (
                <IngredientCard
                  key={ingredient.id}
                  ingredient={ingredient}
                  onChange={(updated) => handleIngredientChange(index, updated)}
                  onDelete={() => handleIngredientDelete(index)}
                />
              ))}
            </div>
            <div className="flex gap-4">
              <button
                onClick={() => setStage('search')}
                className="px-6 py-3 border-2 border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50"
              >
                Back
              </button>
              <button
                onClick={handleSubmit}
                disabled={loading || ingredients.length === 0}
                className="flex-1 px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Submitting...' : 'Submit Order'}
              </button>
            </div>
            {error && (
              <p className="mt-4 text-red-600 text-center">{error}</p>
            )}
          </div>
        )}
        
        {/* Stage 3: Platform Comparison */}
        {stage === 'results' && (
          <div>
            {jobStatus?.status === 'running' || jobStatus?.status === 'pending' ? (
              <div className="bg-white rounded-lg shadow-lg p-12 text-center">
                <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-green-600 mx-auto mb-4"></div>
                <h2 className="text-xl font-semibold mb-2">
                  Processing your order...
                </h2>
                <p className="text-gray-600">
                  {jobStatus?.message || 'Please wait while we compare prices across platforms'}
                </p>
              </div>
            ) : jobStatus?.status === 'success' && platforms.length > 0 ? (
              <div>
                <h2 className="text-2xl font-semibold mb-6 text-center">
                  Platform Comparison
                </h2>
                <div className="grid md:grid-cols-2 gap-6 mb-6">
                  {platforms.map((platform, idx) => (
                    <PlatformCard key={idx} platform={platform} />
                  ))}
                </div>
                <div className="text-center">
                  <button
                    onClick={handleReset}
                    className="px-8 py-3 border-2 border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50"
                  >
                    Compare Again
                  </button>
                </div>
              </div>
            ) : jobStatus?.status === 'error' ? (
              <div className="bg-white rounded-lg shadow-lg p-8 text-center">
                <p className="text-red-600 text-xl mb-4">Error: {jobStatus.message}</p>
                <button
                  onClick={handleReset}
                  className="px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700"
                >
                  Try Again
                </button>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
