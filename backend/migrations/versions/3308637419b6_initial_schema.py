"""initial schema

Revision ID: 3308637419b6
Revises: 
Create Date: 2026-07-17 16:08:23.177293

"""
from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '3308637419b6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table('characters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('glyph', sa.String(length=8), nullable=False),
    sa.Column('pinyin', sa.String(length=160), nullable=False),
    sa.Column('translation', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('radical', sa.String(length=16), nullable=False),
    sa.Column('strokes', sa.Integer(), nullable=True),
    sa.Column('hsk_level', sa.String(length=40), nullable=False),
    sa.Column('image', sa.Text(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_characters_glyph'), 'characters', ['glyph'], unique=True)
    op.create_index(op.f('ix_characters_position'), 'characters', ['position'], unique=False)
    op.create_table('groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_groups_position'), 'groups', ['position'], unique=False)
    op.create_table('images',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('filename', sa.Text(), nullable=False),
    sa.Column('content_type', sa.Text(), nullable=False),
    sa.Column('image_bytes', postgresql.BYTEA(), nullable=False),
    sa.Column('image_width', sa.Integer(), nullable=False),
    sa.Column('image_height', sa.Integer(), nullable=False),
    sa.Column('embedding', Vector(dim=512), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('image_height > 0', name='ck_images_height_positive'),
    sa.CheckConstraint('image_width > 0', name='ck_images_width_positive'),
    sa.PrimaryKeyConstraint('id')
    )
    op.execute(
        "CREATE INDEX idx_images_embedding_cosine ON images "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    op.create_table('notes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(length=64), nullable=False),
    sa.Column('note_date', sa.Date(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'note_date', name='uq_notes_user_date')
    )
    op.create_index(op.f('ix_notes_note_date'), 'notes', ['note_date'], unique=False)
    op.create_index(op.f('ix_notes_user_id'), 'notes', ['user_id'], unique=False)
    op.create_table('photos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=80), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('content_type', sa.String(length=80), nullable=False),
    sa.Column('alt', sa.Text(), nullable=False),
    sa.Column('source', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_photos_slug'), 'photos', ['slug'], unique=True)
    op.create_table('sentences',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hanzi', sa.Text(), nullable=False),
    sa.Column('pinyin', sa.Text(), nullable=False),
    sa.Column('translation', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sentences_position'), 'sentences', ['position'], unique=False)
    op.create_table('ocr_boxes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('image_id', sa.UUID(), nullable=False),
    sa.Column('box_order', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('bbox', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('polygon', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.ForeignKeyConstraint(['image_id'], ['images.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ocr_boxes_image_id_order', 'ocr_boxes', ['image_id', 'box_order'], unique=False)
    op.create_table('user_character_progress',
    sa.Column('user_id', sa.String(length=64), nullable=False),
    sa.Column('character_id', sa.Integer(), nullable=False),
    sa.Column('knowledge_level', sa.Integer(), server_default='0', nullable=False),
    sa.Column('last_seen_at', sa.DateTime(), nullable=True),
    sa.Column('next_review_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'character_id')
    )
    op.create_table('words',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hanzi', sa.String(length=80), nullable=False),
    sa.Column('pinyin', sa.String(length=160), nullable=False),
    sa.Column('translation', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('part_of_speech', sa.String(length=80), nullable=False),
    sa.Column('level', sa.String(length=40), nullable=False),
    sa.Column('image', sa.Text(), nullable=False),
    sa.Column('photo_id', sa.Integer(), nullable=True),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['photo_id'], ['photos.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_words_hanzi'), 'words', ['hanzi'], unique=False)
    op.create_index(op.f('ix_words_photo_id'), 'words', ['photo_id'], unique=False)
    op.create_index(op.f('ix_words_position'), 'words', ['position'], unique=False)
    op.create_table('group_words',
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('word_id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['word_id'], ['words.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('group_id', 'word_id', 'position')
    )
    op.create_table('user_word_progress',
    sa.Column('user_id', sa.String(length=64), nullable=False),
    sa.Column('word_id', sa.Integer(), nullable=False),
    sa.Column('knowledge_level', sa.Integer(), server_default='0', nullable=False),
    sa.Column('last_seen_at', sa.DateTime(), nullable=True),
    sa.Column('next_review_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['word_id'], ['words.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'word_id')
    )
    op.create_table('word_characters',
    sa.Column('word_id', sa.Integer(), nullable=False),
    sa.Column('character_id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('pinyin', sa.String(length=160), nullable=False),
    sa.Column('role', sa.String(length=80), nullable=False),
    sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['word_id'], ['words.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('word_id', 'position')
    )
    op.create_index(op.f('ix_word_characters_character_id'), 'word_characters', ['character_id'], unique=False)
    op.create_table('word_sentences',
    sa.Column('word_id', sa.Integer(), nullable=False),
    sa.Column('sentence_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['sentence_id'], ['sentences.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['word_id'], ['words.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('word_id', 'sentence_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_table('word_sentences')
    op.drop_index(op.f('ix_word_characters_character_id'), table_name='word_characters')
    op.drop_table('word_characters')
    op.drop_table('user_word_progress')
    op.drop_table('group_words')
    op.drop_index(op.f('ix_words_position'), table_name='words')
    op.drop_index(op.f('ix_words_photo_id'), table_name='words')
    op.drop_index(op.f('ix_words_hanzi'), table_name='words')
    op.drop_table('words')
    op.drop_table('user_character_progress')
    op.drop_index('idx_ocr_boxes_image_id_order', table_name='ocr_boxes')
    op.drop_table('ocr_boxes')
    op.drop_index(op.f('ix_sentences_position'), table_name='sentences')
    op.drop_table('sentences')
    op.drop_index(op.f('ix_photos_slug'), table_name='photos')
    op.drop_table('photos')
    op.drop_index(op.f('ix_notes_user_id'), table_name='notes')
    op.drop_index(op.f('ix_notes_note_date'), table_name='notes')
    op.drop_table('notes')
    op.drop_table('images')
    op.drop_index(op.f('ix_groups_position'), table_name='groups')
    op.drop_table('groups')
    op.drop_index(op.f('ix_characters_position'), table_name='characters')
    op.drop_index(op.f('ix_characters_glyph'), table_name='characters')
    op.drop_table('characters')
    # ### end Alembic commands ###
