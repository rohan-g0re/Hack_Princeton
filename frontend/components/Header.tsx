export function Header() {
  return (
    <header className="text-center mb-8">
      {/* Logo */}
      <div className="mb-4">
        <div className="text-5xl mb-2">🥘</div>
        <div className="text-sm text-gray-500 font-medium">MealPilot</div>
      </div>
      
      {/* Main Title */}
      <h1 className="text-4xl font-bold mb-3" style={{ color: '#8B6F47' }}>
        MealPilot: AutoCart
      </h1>
      
      {/* Platform Badges */}
      <div className="flex items-center justify-center gap-3 mb-3">
        <div className="text-2xl">📦</div>
        <span className="text-sm font-medium text-gray-600">Amazon</span>
        <div className="text-2xl">🛒</div>
        <span className="text-sm font-medium text-gray-600">Knot</span>
        <div className="text-2xl">🚗</div>
        <span className="text-sm font-medium text-gray-600">Uber Eats</span>
      </div>
      
      {/* Tagline */}
      <p className="text-gray-600 text-base">
        Compare ingredient costs to save time and money.
      </p>
    </header>
  );
}

