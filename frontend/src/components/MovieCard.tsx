/**
 * MovieCard Component
 * Displays a movie with poster, title, year, genre, ratings, and content badges
 */

import { Movie } from '../types/api.types'
import ContentBadge from './ContentBadge'

interface MovieCardProps {
  movie: Movie
  sexThreshold?: number | null
  violenceThreshold?: number | null
  languageThreshold?: number | null
}

const MovieCard = ({
  movie,
  sexThreshold,
  violenceThreshold,
  languageThreshold,
}: MovieCardProps) => {
  // Format genre list
  const genreText = movie.genre?.join(', ') || 'Unknown'

  // Format ratings
  const ratings = [
    { label: 'IMDb', value: movie.imdb_rating },
    { label: 'RT', value: movie.rt_rating },
    { label: 'MC', value: movie.metacritic_rating },
  ]

  // Determine if content data is available
  const hasContentScores =
    movie.content_score &&
    movie.content_score.sex_nudity !== undefined &&
    movie.content_score.violence_gore !== undefined &&
    movie.content_score.language_profanity !== undefined

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow h-full flex flex-col">
      {/* Poster Image */}
      <div className="relative bg-gray-300 aspect-video overflow-hidden">
        {movie.poster_url ? (
          <img
            src={movie.poster_url}
            alt={movie.title}
            className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
            loading="lazy"
            onError={(e) => {
              // Fallback if image fails to load
              const img = e.target as HTMLImageElement
              img.style.display = 'none'
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gray-400 text-white text-center px-4">
            <div>
              <p className="text-sm font-semibold">{movie.title}</p>
              <p className="text-xs mt-1">No poster available</p>
            </div>
          </div>
        )}
      </div>

      {/* Movie Info */}
      <div className="p-4 flex-1 flex flex-col">
        {/* Title and Year */}
        <h3 className="text-lg font-bold text-gray-800 line-clamp-2 mb-1">
          {movie.title}
        </h3>
        <p className="text-sm text-gray-500 mb-3">
          {movie.year}
          {movie.mpaa_rating && ` • ${movie.mpaa_rating}`}
        </p>

        {/* Genre */}
        <p className="text-xs text-gray-600 mb-4 line-clamp-2">{genreText}</p>

        {/* Ratings */}
        <div className="flex gap-2 mb-4 text-xs">
          {ratings.map(
            (rating) =>
              rating.value && (
                <div
                  key={rating.label}
                  className="bg-gray-100 px-2 py-1 rounded text-gray-700 font-semibold"
                >
                  {rating.label}: {rating.value}
                </div>
              )
          )}
        </div>

        {/* Content Badges */}
        {hasContentScores && (
          <div className="flex flex-wrap gap-2 mt-auto pt-4 border-t">
            <ContentBadge
              label="Sex"
              score={movie.content_score!.sex_nudity}
              threshold={sexThreshold}
            />
            <ContentBadge
              label="Violence"
              score={movie.content_score!.violence_gore}
              threshold={violenceThreshold}
            />
            <ContentBadge
              label="Language"
              score={movie.content_score!.language_profanity}
              threshold={languageThreshold}
            />
          </div>
        )}

        {/* No Content Data */}
        {!hasContentScores && (
          <p className="text-xs text-gray-400 mt-auto pt-4 border-t">
            No content data available
          </p>
        )}
      </div>
    </div>
  )
}

export default MovieCard
