'use client';

import { useState, useEffect } from 'react';
import { Ingredient, PlatformSummary, Stage } from '@/lib/types';
import { api } from '@/lib/api-client';
import { IngredientCard } from '@/components/IngredientCard';
import { PlatformCard } from '@/components/PlatformCard';
import { KeywordChips } from '@/components/KeywordChips';
import { Header } from '@/components/Header';
import { Navigation } from '@/components/Navigation';
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
    <div className="min-h-screen py-12 px-4" style={{ background: '#F5F5F5' }}>
      <div className="max-w-4xl mx-auto">
        <Header />
        <Navigation />
        
        {/* Stage 1: Recipe Search */}
        {stage === 'search' && (
          <div className="card max-w-2xl mx-auto">
            <h2 className="text-xl font-medium mb-6 text-center text-gray-700">
              What recipe or ingredients do you want to order?
            </h2>
            
            {/* Phase 3: Recommendations */}
            {preferences.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Recommended for you:</h3>
                <KeywordChips keywords={preferences} />
              </div>
            )}
            
            <div className="flex gap-3">
              <input
                type="text"
                value={recipeName}
                onChange={(e) => setRecipeName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !loading && handleSearch()}
                placeholder="e.g. Pescado Ingredients or Veggie Pizza dinner"
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#C9915C] focus:border-transparent"
              />
              <button
                onClick={handleSearch}
                disabled={loading || !recipeName}
                className="btn-primary flex items-center gap-2"
              >
                {loading ? 'Loading...' : (
                  <>
                    <span>🔍</span>
                    <span>Search</span>
                  </>
                )}
              </button>
            </div>
            {error && (
              <p className="mt-4 text-red-600 text-center">{error}</p>
            )}
          </div>
        )}
        
        {/* Stage 2: Ingredient Edit */}
        {stage === 'edit' && (
          <div className="card max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold mb-2" style={{ color: '#3E2723' }}>
              Ingredients for '{recipeName}'
            </h2>
            <p className="text-gray-600 mb-6">
              Check the ingredients you already have. We'll compare prices for the rest.
            </p>
            
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Suggested Ingredients</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {ingredients.map((ingredient, index) => (
                  <div 
                    key={ingredient.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex-1">
                      <div className="font-medium text-gray-800">
                        {ingredient.name}
                      </div>
                      <div className="text-sm text-gray-600">
                        {ingredient.quantity || '1'} {ingredient.unit || 'unit'}
                      </div>
                    </div>
                    <button
                      onClick={() => handleIngredientDelete(index)}
                      className="text-red-500 hover:text-red-700 ml-3"
                      title="Remove ingredient"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Add More Ingredients</h3>
              <div className="flex gap-3">
                <input
                  type="text"
                  placeholder="e.g. Vanilla Extract"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#C9915C]"
                />
                <input
                  type="text"
                  placeholder="e.g. 2 tsp"
                  className="w-32 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#C9915C]"
                />
                <button className="btn-primary">
                  + Add Ingredient
                </button>
              </div>
            </div>
            
            <div className="flex justify-center">
              <button
                onClick={handleSubmit}
                disabled={loading || ingredients.length === 0}
                className="btn-primary px-8"
                style={{ minWidth: '250px' }}
              >
                {loading ? 'Processing...' : 'Confirm & Compare Prices'}
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
              <div className="card text-center">
                <div className="animate-spin rounded-full h-16 w-16 border-b-4 mx-auto mb-4" style={{ borderColor: '#C9915C' }}></div>
                <h2 className="text-xl font-semibold mb-2">
                  Processing your order...
                </h2>
                <p className="text-gray-600">
                  {jobStatus?.message || 'Please wait while we compare prices across platforms'}
                </p>
              </div>
            ) : jobStatus?.status === 'success' && platforms.length > 0 ? (
              <div>
                <div className="card mb-6">
                  <div className="inline-block px-3 py-1 bg-[#C9915C] text-white text-xs font-semibold rounded mb-4">
                    Compare Ingredient Costs
                  </div>
                  <h2 className="text-2xl font-bold mb-2" style={{ color: '#3E2723' }}>
                    Price Comparison Results
                  </h2>
                  <p className="text-gray-600 mb-6">
                    Here's how the prices compare across platforms for your ingredients.
                  </p>
                  
                  <div className="grid md:grid-cols-2 gap-6">
                    {platforms.map((platform, idx) => {
                      const platformName = platform.name.toLowerCase();
                      const platformColor = platformName.includes('instacart') ? '#FF6B35' : 
                                          platformName.includes('uber') ? '#06C167' : '#C9915C';
                      const platformIcon = platformName.includes('instacart') ? '🛒' : 
                                         platformName.includes('uber') ? '🚗' : '📦';
                      
                      return (
                        <div key={idx} className="border-2 border-gray-200 rounded-lg p-5">
                          {/* Platform Header */}
                          <div className="flex items-center gap-2 mb-4 pb-3 border-b">
                            <span className="text-2xl">{platformIcon}</span>
                            <div className="flex-1">
                              <h3 className="font-bold text-lg">{platform.name}</h3>
                            </div>
                            {idx === platforms.length - 1 && (
                              <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded">
                                BEST DEAL
                              </span>
                            )}
                          </div>
                          
                          {/* Items List */}
                          <div className="space-y-2 mb-4">
                            {platform.items.slice(0, 8).map((item, itemIdx) => (
                              <div key={itemIdx} className="flex justify-between text-sm">
                                <div className="flex-1">
                                  <div className="font-medium text-gray-800">{itemIdx + 1}. {item.name}</div>
                                  <div className="text-xs text-gray-500">{item.quantity || '1'}</div>
                                </div>
                                <div className="font-semibold text-gray-700 ml-2">
                                  ${item.total_price?.toFixed(2) || '0.00'}
                                </div>
                              </div>
                            ))}
                          </div>
                          
                          {/* Total */}
                          <div className="border-t pt-3 mt-3">
                            <div className="flex justify-between font-bold text-lg mb-4">
                              <span>Total:</span>
                              <span>${platform.total?.toFixed(2) || '0.00'}</span>
                            </div>
                            
                            <button 
                              className="w-full btn-primary"
                              style={{ background: platformColor }}
                            >
                              Add to {platform.name} Cart
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  
                  {/* Savings Message */}
                  {platforms.length >= 2 && (
                    <div className="mt-6 text-center">
                      <p className="text-green-700 font-medium">
                        You can save ${Math.abs(platforms[0].total - platforms[1].total).toFixed(2)} by choosing {platforms[0].total < platforms[1].total ? platforms[0].name : platforms[1].name}!
                      </p>
                    </div>
                  )}
                </div>
                
                <div className="text-center">
                  <button
                    onClick={handleReset}
                    className="px-6 py-2 border-2 border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50"
                  >
                    ← Back to Home
                  </button>
                </div>
              </div>
            ) : jobStatus?.status === 'error' ? (
              <div className="card text-center">
                <p className="text-red-600 text-xl mb-4">Error: {jobStatus.message}</p>
                <button
                  onClick={handleReset}
                  className="btn-primary"
                >
                  Try Again
                </button>
              </div>
            ) : null}
          </div>
        )}
        
        {/* Footer */}
        <footer className="text-center mt-12 text-gray-500 text-sm">
          © 2025 MealPilot
        </footer>
      </div>
    </div>
  );
}
