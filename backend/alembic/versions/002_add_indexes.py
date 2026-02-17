"""Add database indexes for search and filtering performance

Revision ID: 002_add_indexes
Revises: 001_initial_schema
Create Date: 2025-01-23 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_indexes'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Movies table indexes
    
    # Primary key index (automatically created, but explicit for clarity)
    # op.create_index('idx_movies_id', 'movies', ['id'], unique=True)
    
    # Title full-text search (GIN index with tsvector)
    op.execute("""
    CREATE INDEX idx_movies_title_fts 
    ON movies 
    USING GIN (to_tsvector('english', title))
    """)
    
    # Genre array search (GIN index)
    op.create_index('idx_movies_genre', 'movies', ['genre'], postgresql_using='gin')
    
    # Individual filter fields (B-tree indexes)
    op.create_index('idx_movies_year', 'movies', ['year'])
    op.create_index('idx_movies_mpaa_rating', 'movies', ['mpaa_rating'])
    op.create_index('idx_movies_imdb_rating', 'movies', ['imdb_rating'])
    op.create_index('idx_movies_rt_rating', 'movies', ['rt_rating'])
    op.create_index('idx_movies_metacritic_rating', 'movies', ['metacritic_rating'])
    
    # Composite index for common filter combinations
    op.create_index(
        'idx_movies_filters_composite',
        'movies',
        ['mpaa_rating', 'year', 'imdb_rating']
    )
    
    # Partial index for rated movies
    op.execute("""
    CREATE INDEX idx_movies_rated 
    ON movies (imdb_rating) 
    WHERE imdb_rating > 0
    """)
    
    # Awards filtering
    op.create_index('idx_movies_awards', 'movies', ['awards_count', 'nominations_count'])
    
    # OMDb ID for lookups (unique constraint creates index automatically)
    # op.create_index('idx_movies_omdb_id', 'movies', ['omdb_id'], unique=True)
    
    # Content scores table indexes
    
    # Primary key index (automatically created)
    # op.create_index('idx_content_scores_id', 'content_scores', ['id'], unique=True)
    
    # Foreign key to movies (unique constraint creates index automatically)
    # op.create_index('idx_content_scores_movie_id', 'content_scores', ['movie_id'], unique=True)
    
    # Individual content score indexes (for range filtering)
    op.create_index('idx_content_scores_sex', 'content_scores', ['sex_nudity'])
    op.create_index('idx_content_scores_violence', 'content_scores', ['violence_gore'])
    op.create_index('idx_content_scores_language', 'content_scores', ['language_profanity'])
    
    # Composite index for all three content scores (frequently filtered together)
    op.create_index(
        'idx_content_scores_composite',
        'content_scores',
        ['sex_nudity', 'violence_gore', 'language_profanity']
    )
    
    # Partial index for available content scores (optimize content filtering queries)
    op.execute("""
    CREATE INDEX idx_content_scores_available 
    ON content_scores (sex_nudity, violence_gore, language_profanity)
    WHERE sex_nudity IS NOT NULL
    """)
    
    # Data refresh logs table indexes
    
    # Primary key index (automatically created)
    # op.create_index('idx_data_refresh_logs_id', 'data_refresh_logs', ['id'], unique=True)
    
    # Query by date range (DESC for most recent first)
    op.create_index('idx_data_refresh_logs_date', 'data_refresh_logs', ['refresh_date'], postgresql_ops={'refresh_date': 'DESC'})
    
    # Filter by source and status
    op.create_index('idx_data_refresh_logs_source_status', 'data_refresh_logs', ['source', 'status'])
    
    # Performance monitoring (find slow jobs)
    op.create_index('idx_data_refresh_logs_duration', 'data_refresh_logs', ['duration_seconds'], postgresql_ops={'duration_seconds': 'DESC'})


def downgrade() -> None:
    # Drop data_refresh_logs indexes
    op.drop_index('idx_data_refresh_logs_duration', 'data_refresh_logs')
    op.drop_index('idx_data_refresh_logs_source_status', 'data_refresh_logs')
    op.drop_index('idx_data_refresh_logs_date', 'data_refresh_logs')
    
    # Drop content_scores indexes
    op.drop_index('idx_content_scores_available', 'content_scores')
    op.drop_index('idx_content_scores_composite', 'content_scores')
    op.drop_index('idx_content_scores_language', 'content_scores')
    op.drop_index('idx_content_scores_violence', 'content_scores')
    op.drop_index('idx_content_scores_sex', 'content_scores')
    
    # Drop movies indexes
    op.drop_index('idx_movies_awards', 'movies')
    op.drop_index('idx_movies_rated', 'movies')
    op.drop_index('idx_movies_filters_composite', 'movies')
    op.drop_index('idx_movies_metacritic_rating', 'movies')
    op.drop_index('idx_movies_rt_rating', 'movies')
    op.drop_index('idx_movies_imdb_rating', 'movies')
    op.drop_index('idx_movies_mpaa_rating', 'movies')
    op.drop_index('idx_movies_year', 'movies')
    op.drop_index('idx_movies_genre', 'movies')
    op.drop_index('idx_movies_title_fts', 'movies')
