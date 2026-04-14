/** Recipe thumbnail card used in the Recipes gallery grid. */
export default function RecipeCard({ recipe, onClick }) {
  return (
    <div
      onClick={() => onClick(recipe)}
      className="recipe-card forge-card overflow-hidden hover:border-brand-blue/50 hover:shadow-forge-lg"
    >
      {/* Image */}
      <div className="aspect-square bg-brand-bg overflow-hidden">
        {recipe.local_image_path ? (
          <img
            src={recipe.local_image_path}
            alt={recipe.title}
            className="w-full h-full object-cover opacity-90 hover:opacity-100 transition-opacity"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl text-brand-border">
            🍽️
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-3">
        <h3 className="font-semibold text-sm text-brand-text line-clamp-2 leading-snug">
          {recipe.title}
        </h3>
        <div className="flex items-center gap-2 mt-1.5 text-xs text-brand-muted">
          {recipe.is_favorite && (
            <span className="text-brand-gold" title="Favourite">⭐</span>
          )}
          {recipe.rating > 0 && (
            <span className="text-brand-gold">
              {'★'.repeat(Math.round(recipe.rating))}{' '}
              <span className="text-brand-muted">{recipe.rating.toFixed(1)}</span>
            </span>
          )}
          {recipe.times_cooked > 0 && (
            <span className="ml-auto text-brand-silver">🍳 ×{recipe.times_cooked}</span>
          )}
        </div>
      </div>
    </div>
  )
}
