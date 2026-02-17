/**
 * MovieDetail Page
 * Comprehensive movie details: poster, metadata, ratings, awards, content scores
 * With back navigation and responsive layout
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Movie } from '../types/api.types'
import apiClient from '../services/api'

// Score level labels for content scores
const getScoreLabel = (score: number): string => {
  if (score === 0) return 'None'
  if (score <= 2) return 'Mild'
  if (score <= 4) return 'Moderate'
  if (score <= 6) return 'Strong'
  if (score <= 8) return 'Intense'
  return 'Extreme'
}

const getScoreColor = (score: number): string => {
  if (score <= 2) return 'bg-green-500'
  if (score <= 4) return 'bg-yellow-500'
  if (score <= 6) return 'bg-orange-500'
  if (score <= 8) return 'bg-red-500'
  return 'bg-red-700'
}

const MovieDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [movie, setMovie] = useState<Movie | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchMovie = async () => {
      if (!id) return
      try {
        setLoading(true)
        setError(null)
        const response = await apiClient.get<Movie>(`/movies/${id}`)
        setMovie(response.data)
      } catch (err: unknown) {
        const axiosErr = err as { response?: { status?: number } }
        if (axiosErr.response?.status === 404) {
          setError('Movie not found')
        } else {
          setError('Failed to load movie details. Please try again.')
        }
      } finally {
        setLoading(false)
      }
    }
    fetchMovie()
  }, [id])

  const handleBack = () => {
    if (window.history.length > 1) {
      navigate(-1)
    } else {
      navigate('/')
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-200 border-t-brand-primary mx-auto"></div>
          <p className="text-gray-500 mt-4">Loading movie details...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error || !movie) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-5xl mb-4">😞</div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">{error || 'Movie not found'}</h2>
          <p className="text-gray-500 mb-6">The movie you&apos;re looking for doesn&apos;t exist or couldn&apos;t be loaded.</p>
          <button
            onClick={handleBack}
            className="px-6 py-3 bg-brand-primary text-white font-semibold rounded-lg
                       hover:bg-blue-600 transition min-h-[44px]"
          >
            ← Back to Search
          </button>
        </div>
      </div>
    )
  }

  const hasContentScores = movie.content_score &&
    movie.content_score.sex_nudity !== undefined &&
    movie.content_score.violence_gore !== undefined &&
    movie.content_score.language_profanity !== undefined

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Back Navigation Bar */}
      <div className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-30">
        <div className="container mx-auto px-4 py-3">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium
                       transition min-h-[44px] -ml-2 px-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span>Back to Search</span>
          </button>
        </div>
      </div>

      {/* Movie Content */}
      <div className="container mx-auto px-4 py-6 md:py-8">
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          {/* Hero Section: Poster + Basic Info */}
          <div className="md:flex">
            {/* Poster */}
            <div className="md:w-80 lg:w-96 flex-shrink-0">
              <div className="aspect-[2/3] bg-gray-200 relative">
                {movie.poster_url ? (
                  <img
                    src={movie.poster_url}
                    alt={`${movie.title} poster`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      const img = e.target as HTMLImageElement
                      img.style.display = 'none'
                    }}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gray-300 text-gray-500">
                    <div className="text-center px-6">
                      <svg className="w-16 h-16 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                          d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
                      </svg>
                      <p className="text-sm font-medium">No poster available</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Basic Info */}
            <div className="flex-1 p-5 md:p-8">
              {/* Title */}
              <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold text-gray-900 mb-2">
                {movie.title}
              </h1>

              {/* Meta line */}
              <div className="flex flex-wrap items-center gap-2 text-sm text-gray-500 mb-4">
                <span className="font-semibold">{movie.year}</span>
                {movie.mpaa_rating && (
                  <>
                    <span>•</span>
                    <span className="px-2 py-0.5 border border-gray-300 rounded text-xs font-bold">
                      {movie.mpaa_rating}
                    </span>
                  </>
                )}
                {movie.runtime && (
                  <>
                    <span>•</span>
                    <span>{Math.floor(movie.runtime / 60)}h {movie.runtime % 60}m</span>
                  </>
                )}
              </div>

              {/* Genres */}
              {movie.genre && movie.genre.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-5">
                  {movie.genre.map((g) => (
                    <span
                      key={g}
                      className="px-3 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full"
                    >
                      {g}
                    </span>
                  ))}
                </div>
              )}

              {/* Director & Cast */}
              {movie.director && (
                <div className="mb-3">
                  <span className="text-sm font-semibold text-gray-600">Director: </span>
                  <span className="text-sm text-gray-800">{movie.director}</span>
                </div>
              )}
              {movie.cast && movie.cast.length > 0 && (
                <div className="mb-5">
                  <span className="text-sm font-semibold text-gray-600">Cast: </span>
                  <span className="text-sm text-gray-800">{movie.cast.join(', ')}</span>
                </div>
              )}

              {/* Plot */}
              {movie.plot && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-600 mb-1">Plot</h3>
                  <p className="text-gray-700 leading-relaxed">{movie.plot}</p>
                </div>
              )}

              {/* Ratings Section */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-600 mb-3">Ratings</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {/* IMDb */}
                  {movie.imdb_rating && (
                    <div className="flex items-center gap-3 bg-yellow-50 rounded-lg p-3">
                      <div className="text-2xl">⭐</div>
                      <div>
                        <div className="text-lg font-bold text-yellow-700">
                          {Number(movie.imdb_rating).toFixed(1)}/10
                        </div>
                        <div className="text-xs text-yellow-600 font-medium">IMDb</div>
                      </div>
                    </div>
                  )}

                  {/* Rotten Tomatoes */}
                  {movie.rt_rating !== null && movie.rt_rating !== undefined && (
                    <div className="flex items-center gap-3 bg-red-50 rounded-lg p-3">
                      <div className="text-2xl">🍅</div>
                      <div>
                        <div className="text-lg font-bold text-red-700">{movie.rt_rating}%</div>
                        <div className="text-xs text-red-600 font-medium">Rotten Tomatoes</div>
                      </div>
                    </div>
                  )}

                  {/* Metacritic */}
                  {movie.metacritic_rating !== null && movie.metacritic_rating !== undefined && (
                    <div className={`flex items-center gap-3 rounded-lg p-3 ${
                      movie.metacritic_rating >= 61 ? 'bg-green-50' :
                      movie.metacritic_rating >= 40 ? 'bg-yellow-50' : 'bg-red-50'
                    }`}>
                      <div className={`w-10 h-10 rounded flex items-center justify-center text-white font-bold text-sm ${
                        movie.metacritic_rating >= 61 ? 'bg-green-600' :
                        movie.metacritic_rating >= 40 ? 'bg-yellow-600' : 'bg-red-600'
                      }`}>
                        {movie.metacritic_rating}
                      </div>
                      <div>
                        <div className="text-lg font-bold text-gray-800">{movie.metacritic_rating}/100</div>
                        <div className="text-xs text-gray-600 font-medium">Metacritic</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Awards Section */}
              {(movie.awards_summary || movie.awards_count > 0) && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-600 mb-2">Awards</h3>
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">🏆</span>
                      <div>
                        {movie.awards_summary && (
                          <p className="text-sm text-amber-800 font-medium">{movie.awards_summary}</p>
                        )}
                        <div className="flex gap-4 mt-2 text-xs text-amber-700">
                          {movie.awards_count > 0 && (
                            <span>{movie.awards_count} win{movie.awards_count !== 1 ? 's' : ''}</span>
                          )}
                          {movie.nominations_count > 0 && (
                            <span>{movie.nominations_count} nomination{movie.nominations_count !== 1 ? 's' : ''}</span>
                          )}
                        </div>
                        {/* Awards metadata (specific awards) */}
                        {movie.awards_metadata && Object.keys(movie.awards_metadata).length > 0 && (
                          <div className="mt-3 space-y-1">
                            {Object.entries(movie.awards_metadata).map(([category, awards]) => (
                              <div key={category} className="text-xs text-amber-700">
                                <span className="font-semibold capitalize">{category}: </span>
                                <span>{Array.isArray(awards) ? (awards as string[]).join(', ') : String(awards)}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Content Scores Section */}
          <div className="border-t border-gray-200 p-5 md:p-8">
            <h3 className="text-lg font-bold text-gray-800 mb-4">Content Ratings</h3>

            {hasContentScores ? (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* Sex/Nudity */}
                <ContentScoreCard
                  label="Sex & Nudity"
                  score={movie.content_score!.sex_nudity}
                  icon="🔞"
                />
                {/* Violence/Gore */}
                <ContentScoreCard
                  label="Violence & Gore"
                  score={movie.content_score!.violence_gore}
                  icon="⚔️"
                />
                {/* Language/Profanity */}
                <ContentScoreCard
                  label="Language & Profanity"
                  score={movie.content_score!.language_profanity}
                  icon="🗣️"
                />
              </div>
            ) : (
              <div className="bg-gray-50 rounded-lg p-6 text-center">
                <p className="text-gray-500">
                  Content ratings are not available for this movie.
                </p>
                <p className="text-gray-400 text-sm mt-1">
                  Ratings are sourced from Kids-in-Mind and may not cover all movies.
                </p>
              </div>
            )}

            {/* Score Legend */}
            {hasContentScores && (
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Score Legend
                </h4>
                <div className="flex flex-wrap gap-3 text-xs text-gray-600">
                  <span><strong>0</strong> = None</span>
                  <span><strong>1–2</strong> = Mild</span>
                  <span><strong>3–4</strong> = Moderate</span>
                  <span><strong>5–6</strong> = Strong</span>
                  <span><strong>7–8</strong> = Intense</span>
                  <span><strong>9–10</strong> = Extreme</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Individual content score card with visual bar
 */
const ContentScoreCard = ({
  label,
  score,
  icon,
}: {
  label: string
  score: number
  icon: string
}) => (
  <div className="bg-gray-50 rounded-lg p-4">
    <div className="flex items-center gap-2 mb-2">
      <span className="text-lg">{icon}</span>
      <span className="text-sm font-semibold text-gray-700">{label}</span>
    </div>
    <div className="flex items-end gap-2 mb-2">
      <span className="text-3xl font-bold text-gray-900">{score}</span>
      <span className="text-sm text-gray-500 pb-1">/10</span>
    </div>
    <div className="text-xs font-medium text-gray-600 mb-2">{getScoreLabel(score)}</div>
    {/* Score bar */}
    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full transition-all ${getScoreColor(score)}`}
        style={{ width: `${score * 10}%` }}
      />
    </div>
  </div>
)

export default MovieDetail
