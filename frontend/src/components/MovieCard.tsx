/**
 * MovieCard Component
 * Displays a movie with poster, title, year, genre, ratings from all sources,
 * and content badges. Clickable to navigate to movie detail page.
 */

import { useNavigate } from 'react-router-dom'
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
  const navigate = useNavigate()

  // Format genre list
  const genreText = movie.genre?.slice(0, 3).join(', ') || 'Unknown'

  // Determine if content data is available
  const hasContentScores =
    movie.content_score &&
    movie.content_score.sex_nudity !== undefined &&
    movie.content_score.violence_gore !== undefined &&
    movie.content_score.language_profanity !== undefined

  const handleClick = () => {
    navigate(`/movies/${movie.id}`)
  }

  return (
    <div
      onClick={handleClick}
      className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-all duration-200
                 h-full flex flex-col cursor-pointer group"
      role="article"
      aria-label={`${movie.title} (${movie.year})`}
    >
      {/* Poster Image */}
      <div className="relative bg-gray-200 aspect-[2/3] overflow-hidden">
        {movie.poster_url ? (
          <img
            src={movie.poster_url}
            alt={`${movie.title} poster`}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
            onError={(e) => {
              const img = e.target as HTMLImageElement
              img.style.display = 'none'
              const fallback = img.nextElementSibling as HTMLElement
              if (fallback) fallback.style.display = 'flex'
            }}
          />
        ) : null}
        {/* Placeholder fallback - shown when no poster or image error */}
        <div
          className={`absolute inset-0 ${movie.poster_url ? 'hidden' : 'flex'} items-center justify-center bg-gray-300 text-gray-500`}
        >
          <div className="text-center px-4">
            <svg className="w-12 h-12 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
            </svg>
            <p className="text-xs font-medium line-clamp-2">{movie.title}</p>
          </div>
        </div>

        {/* MPAA Badge */}
        {movie.mpaa_rating && (
          <div className="absolute top-2 right-2 bg-black/70 text-white text-xs font-bold px-2 py-1 rounded">
            {movie.mpaa_rating}
          </div>
        )}
      </div>

      {/* Movie Info */}
      <div className="p-3 sm:p-4 flex-1 flex flex-col">
        {/* Title and Year */}
        <h3 className="text-base font-bold text-gray-800 line-clamp-2 mb-1 group-hover:text-brand-primary transition-colors">
          {movie.title}
        </h3>
        <p className="text-sm text-gray-500 mb-2">
          {movie.year}
          {movie.runtime && ` • ${movie.runtime} min`}
        </p>

        {/* Genre */}
        <p className="text-xs text-gray-500 mb-3">{genreText}</p>

        {/* Ratings Row */}
        <div className="flex flex-wrap gap-1.5 mb-3 text-xs">
          {movie.imdb_rating && (
            <div className="flex items-center gap-1 bg-yellow-50 text-yellow-700 px-2 py-1 rounded font-semibold">
              <span>⭐</span>
              <span>{Number(movie.imdb_rating).toFixed(1)}</span>
            </div>
          )}
          {movie.rt_rating !== null && movie.rt_rating !== undefined && (
            <div className="flex items-center gap-1 bg-red-50 text-red-700 px-2 py-1 rounded font-semibold">
              <span>🍅</span>
              <span>{movie.rt_rating}%</span>
            </div>
          )}
          {movie.metacritic_rating !== null && movie.metacritic_rating !== undefined && (
            <div className={`flex items-center gap-1 px-2 py-1 rounded font-semibold
              ${movie.metacritic_rating >= 61 ? 'bg-green-50 text-green-700' :
                movie.metacritic_rating >= 40 ? 'bg-yellow-50 text-yellow-700' :
                'bg-red-50 text-red-700'}`}
            >
              <span>MC</span>
              <span>{movie.metacritic_rating}</span>
            </div>
          )}
        </div>

        {/* Awards (if notable) */}
        {movie.awards_count > 0 && (
          <p className="text-xs text-amber-600 mb-3 font-medium">
            🏆 {movie.awards_count} award{movie.awards_count !== 1 ? 's' : ''}
          </p>
        )}

        {/* Content Badges */}
        {hasContentScores && (
          <div className="flex flex-wrap gap-1.5 mt-auto pt-3 border-t border-gray-100">
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

        {/* No Content Data - N/A indicator */}
        {!hasContentScores && (
          <div className="flex items-center gap-1.5 mt-auto pt-3 border-t border-gray-100">
            <span
              className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-500"
              title="Content ratings not available for this movie"
            >
              Content ratings N/A
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export default MovieCard
