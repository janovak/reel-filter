"""Initial schema with movies, content_scores, and data_refresh_logs tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-01-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create movies table
    op.create_table(
        'movies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('runtime', sa.Integer(), nullable=True),
        sa.Column('genre', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('mpaa_rating', sa.String(10), nullable=True),
        sa.Column('plot', sa.Text(), nullable=True),
        sa.Column('director', sa.String(255), nullable=True),
        sa.Column('cast', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('poster_url', sa.String(500), nullable=True),
        sa.Column('imdb_rating', sa.Numeric(3, 1), nullable=True),
        sa.Column('rt_rating', sa.Integer(), nullable=True),
        sa.Column('metacritic_rating', sa.Integer(), nullable=True),
        sa.Column('awards_summary', sa.Text(), nullable=True),
        sa.Column('awards_count', sa.Integer(), server_default='0'),
        sa.Column('nominations_count', sa.Integer(), server_default='0'),
        sa.Column('awards_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('omdb_id', sa.String(50), nullable=False, unique=True),
        sa.Column('source', sa.String(20), server_default='omdb'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.CheckConstraint('year >= 1888 AND year <= 2100', name='check_year_range'),
        sa.CheckConstraint(
            "mpaa_rating IN ('G', 'PG', 'PG-13', 'R', 'NC-17', 'Not Rated') OR mpaa_rating IS NULL",
            name='check_mpaa_rating'
        ),
        sa.CheckConstraint(
            'imdb_rating >= 0 AND imdb_rating <= 10 OR imdb_rating IS NULL',
            name='check_imdb_rating'
        ),
        sa.CheckConstraint(
            'rt_rating >= 0 AND rt_rating <= 100 OR rt_rating IS NULL',
            name='check_rt_rating'
        ),
        sa.CheckConstraint(
            'metacritic_rating >= 0 AND metacritic_rating <= 100 OR metacritic_rating IS NULL',
            name='check_metacritic_rating'
        ),
    )
    
    # Create content_scores table
    op.create_table(
        'content_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('movie_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('sex_nudity', sa.Integer(), nullable=False),
        sa.Column('violence_gore', sa.Integer(), nullable=False),
        sa.Column('language_profanity', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(20), server_default='kids-in-mind'),
        sa.Column('source_available', sa.Boolean(), server_default='true'),
        sa.Column('scraped_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('match_confidence', sa.Numeric(5, 2), nullable=True),
        sa.Column('manually_reviewed', sa.Boolean(), server_default='false'),
        sa.ForeignKeyConstraint(['movie_id'], ['movies.id'], ondelete='CASCADE'),
        sa.CheckConstraint('sex_nudity >= 0 AND sex_nudity <= 10', name='check_sex_nudity_range'),
        sa.CheckConstraint('violence_gore >= 0 AND violence_gore <= 10', name='check_violence_gore_range'),
        sa.CheckConstraint('language_profanity >= 0 AND language_profanity <= 10', name='check_language_profanity_range'),
        sa.CheckConstraint(
            'match_confidence >= 0 AND match_confidence <= 100 OR match_confidence IS NULL',
            name='check_match_confidence_range'
        ),
    )
    
    # Create data_refresh_logs table
    op.create_table(
        'data_refresh_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('refresh_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('source', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('records_fetched', sa.Integer(), server_default='0'),
        sa.Column('records_updated', sa.Integer(), server_default='0'),
        sa.Column('records_created', sa.Integer(), server_default='0'),
        sa.Column('records_failed', sa.Integer(), server_default='0'),
        sa.Column('errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("source IN ('omdb', 'kids-in-mind')", name='check_source'),
        sa.CheckConstraint("status IN ('success', 'failed', 'partial')", name='check_status'),
    )
    
    # Create trigger function for auto-updating updated_at
    op.execute("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """)
    
    # Create triggers for movies and content_scores tables
    op.execute("""
    CREATE TRIGGER update_movies_updated_at
    BEFORE UPDATE ON movies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
    CREATE TRIGGER update_content_scores_updated_at
    BEFORE UPDATE ON content_scores
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_content_scores_updated_at ON content_scores')
    op.execute('DROP TRIGGER IF EXISTS update_movies_updated_at ON movies')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    
    # Drop tables
    op.drop_table('data_refresh_logs')
    op.drop_table('content_scores')
    op.drop_table('movies')
    
    # Drop UUID extension (optional, may be used by other schemas)
    # op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
