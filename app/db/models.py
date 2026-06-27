from datetime import datetime, date
from typing import List, Optional
import uuid
from uuid import UUID as PyUUID

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Text,
    Float,
    CheckConstraint,
    UniqueConstraint,
    Index,
    Table,
    Column,
    func,
    Enum,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.schemas.enums import VueLayout


class Base(DeclarativeBase):
    pass


# --- Tables d'association (Many-to-Many) ---

concept_tags = Table(
    "concept_tags",
    Base.metadata,
    Column("concept_id", Integer, ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

concepts_sources = Table(
    "concepts_sources",
    Base.metadata,
    Column("concept_id", Integer, ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True),
    Column("source_id", Integer, ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True),
)


# --- Modèles ---


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))

    # Relations
    parent: Mapped[Optional["Category"]] = relationship("Category", remote_side=[id], back_populates="children")
    children: Mapped[List["Category"]] = relationship("Category", back_populates="parent")
    concepts: Mapped[List["Concept"]] = relationship("Concept", back_populates="category")
    user_favorites: Mapped[List["UserFavorite"]] = relationship("UserFavorite", back_populates="category")


class Mathematicien(Base):
    __tablename__ = "mathematiciens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    date_naissance: Mapped[Optional[date]] = mapped_column(Date)
    date_deces: Mapped[Optional[date]] = mapped_column(Date)
    biographie: Mapped[Optional[str]] = mapped_column(Text)
    nationalite: Mapped[Optional[str]] = mapped_column(Text)
    domaine: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[Optional[str]] = mapped_column(Text)
    recompenses: Mapped[Optional[str]] = mapped_column(Text)
    epoque: Mapped[Optional[str]] = mapped_column(Text)

    # Relations
    concepts: Mapped[List["Concept"]] = relationship("Concept", back_populates="mathematicien")
    user_favorites: Mapped[List["UserFavorite"]] = relationship("UserFavorite", back_populates="mathematicien")

    __table_args__ = (Index("idx_mathematiciens_domaine", "domaine"),)


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titre: Mapped[Optional[str]] = mapped_column(Text)
    auteur: Mapped[Optional[str]] = mapped_column(Text)
    annee: Mapped[Optional[int]] = mapped_column(Integer)
    url: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    doi: Mapped[Optional[str]] = mapped_column(String(255))
    isbn: Mapped[Optional[str]] = mapped_column(String(13))
    date_publication: Mapped[Optional[date]] = mapped_column(Date)
    editeur: Mapped[Optional[str]] = mapped_column(String(255))
    langue: Mapped[Optional[str]] = mapped_column(String(10), server_default="fr")
    abstract: Mapped[Optional[str]] = mapped_column(Text)

    # Relations
    concepts: Mapped[List["Concept"]] = relationship("Concept", secondary=concepts_sources, back_populates="sources")

    __table_args__ = (
        CheckConstraint("type = ANY (ARRAY['livre', 'article', 'site_web', 'autre'])", name="sources_type_check"),
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Relations
    concepts: Mapped[List["Concept"]] = relationship("Concept", secondary=concept_tags, back_populates="tags")


class Type(Base):
    __tablename__ = "type"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(Text, nullable=False)

    # Relations
    concepts: Mapped[List["Concept"]] = relationship("Concept", back_populates="type")
    user_favorites: Mapped[List["UserFavorite"]] = relationship("UserFavorite", back_populates="type")


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    enonce: Mapped[str] = mapped_column(Text, nullable=False)
    demonstration: Mapped[Optional[str]] = mapped_column(Text)
    verification: Mapped[bool] = mapped_column(Boolean, server_default="false")
    date_modification: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )
    mathematicien_id: Mapped[Optional[int]] = mapped_column(ForeignKey("mathematiciens.id"))
    categorie_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    type_id: Mapped[int] = mapped_column(ForeignKey("type.id"), server_default="1")

    # Relations
    mathematicien: Mapped[Optional["Mathematicien"]] = relationship("Mathematicien", back_populates="concepts")
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="concepts")
    type: Mapped["Type"] = relationship("Type", back_populates="concepts")
    aliases: Mapped[List["Alias"]] = relationship("Alias", back_populates="concept", cascade="all, delete-orphan")
    tags: Mapped[List["Tag"]] = relationship("Tag", secondary=concept_tags, back_populates="concepts")
    sources: Mapped[List["Source"]] = relationship("Source", secondary=concepts_sources, back_populates="concepts")
    foreign_names: Mapped[List["ForeignName"]] = relationship("ForeignName", back_populates="concept")
    positions: Mapped[List["Position"]] = relationship(
        "Position", back_populates="concept", cascade="all, delete-orphan"
    )
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="concept", cascade="all, delete-orphan")
    views: Mapped[List["ConceptView"]] = relationship("ConceptView", back_populates="concept")
    versions: Mapped[List["ConceptVersion"]] = relationship(
        "ConceptVersion", back_populates="concept", cascade="all, delete-orphan"
    )
    contributions: Mapped[List["UserContribution"]] = relationship("UserContribution", back_populates="concept")
    user_favorites: Mapped[List["UserFavorite"]] = relationship("UserFavorite", back_populates="concept")

    # Relations (Self-referencing through Relation table)
    outgoing_relations: Mapped[List["Relation"]] = relationship(
        "Relation", foreign_keys="[Relation.concept_source]", back_populates="source_concept"
    )
    incoming_relations: Mapped[List["Relation"]] = relationship(
        "Relation", foreign_keys="[Relation.concept_cible]", back_populates="target_concept"
    )

    __table_args__ = (
        Index("idx_concepts_date_modification", "date_modification"),
        Index("idx_concepts_nom", "nom"),
        Index("idx_concepts_verification", "verification"),
        Index("idx_concepts_mathematicien_id", "mathematicien_id"),
        Index("idx_concepts_categorie_id", "categorie_id"),
        Index("idx_concepts_type_id", "type_id"),
        Index(
            "idx_concepts_fts",
            func.to_tsvector(text("'french'"), nom + " " + enonce),
            postgresql_using="gin",
        ),
    )


class Alias(Base):
    __tablename__ = "aliases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    alias: Mapped[str] = mapped_column(Text, unique=True, nullable=False)

    # Relations
    concept: Mapped["Concept"] = relationship("Concept", back_populates="aliases")


class ForeignName(Base):
    __tablename__ = "foreign_name"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nom_etranger: Mapped[str] = mapped_column("Nom_étranger", Text, nullable=False)
    langue: Mapped[str] = mapped_column(Text, nullable=False)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), nullable=False)

    # Relations
    concept: Mapped["Concept"] = relationship("Concept", back_populates="foreign_names")

    __table_args__ = (Index("idx_foreign_name_langue", "langue"),)


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    vue: Mapped[VueLayout] = mapped_column(Enum(VueLayout, native_enum=False, length=100), nullable=False)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    z: Mapped[float] = mapped_column(Float, nullable=False)

    # Relations
    concept: Mapped["Concept"] = relationship("Concept", back_populates="positions")

    __table_args__ = (UniqueConstraint("concept_id", "vue"),)


class Relation(Base):
    __tablename__ = "relations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    concept_source: Mapped[Optional[int]] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"))
    concept_cible: Mapped[Optional[int]] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"))
    type_relation: Mapped[str] = mapped_column(Text, nullable=False)
    date_relation: Mapped[Optional[datetime]] = mapped_column(DateTime)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Relations
    source_concept: Mapped[Optional["Concept"]] = relationship(
        "Concept", foreign_keys=[concept_source], back_populates="outgoing_relations"
    )
    target_concept: Mapped[Optional["Concept"]] = relationship(
        "Concept", foreign_keys=[concept_cible], back_populates="incoming_relations"
    )

    __table_args__ = (
        CheckConstraint(
            "type_relation = ANY (ARRAY['utilise', 'implication', 'equivalence', 'reciproque'])",
            name="relations_type_relation_check",
        ),
        Index("idx_relations_cible", "concept_cible"),
        Index("idx_relations_source", "concept_source"),
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[PyUUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    role: Mapped[str] = mapped_column(String(20), server_default="user", nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    preferred_language: Mapped[Optional[str]] = mapped_column(String(10), server_default="fr")
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255))
    bio: Mapped[Optional[str]] = mapped_column(Text)

    # Relations
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="user")
    views: Mapped[List["ConceptView"]] = relationship("ConceptView", back_populates="user")
    favorites: Mapped[List["UserFavorite"]] = relationship("UserFavorite", back_populates="user")
    contributions: Mapped[List["UserContribution"]] = relationship("UserContribution", back_populates="user")
    sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user")
    reset_tokens: Mapped[List["PasswordResetToken"]] = relationship("PasswordResetToken", back_populates="user")
    modified_versions: Mapped[List["ConceptVersion"]] = relationship("ConceptVersion", back_populates="modifier")

    __table_args__ = (CheckConstraint("role = ANY (ARRAY['admin', 'user', 'moderator'])", name="users_role_check"),)


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    concept_id: Mapped[Optional[int]] = mapped_column(ForeignKey("concepts.id", onupdate="CASCADE", ondelete="CASCADE"))
    user_id: Mapped[Optional[PyUUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id", onupdate="CASCADE", ondelete="CASCADE"))
    is_deleted: Mapped[bool] = mapped_column(Boolean, server_default="false")
    field: Mapped[str] = mapped_column(Text, nullable=False)

    # Relations
    concept: Mapped[Optional["Concept"]] = relationship("Concept", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="comments")
    parent: Mapped[Optional["Comment"]] = relationship("Comment", remote_side=[id], back_populates="children")
    children: Mapped[List["Comment"]] = relationship("Comment", back_populates="parent")

    __table_args__ = (
        CheckConstraint("(parent_id IS NULL) OR (parent_id <> id)", name="chk_parent_not_self"),
        Index("idx_comments_concept_id", "concept_id"),
        Index("idx_comments_parent_id", "parent_id"),
        Index("idx_comments_user_id", "user_id"),
        Index("idx_comments_created_at", "created_at"),
    )


class ConceptView(Base):
    __tablename__ = "concept_views"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    concept_id: Mapped[Optional[int]] = mapped_column(ForeignKey("concepts.id"))
    user_id: Mapped[Optional[PyUUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ip_address: Mapped[Optional[str]] = mapped_column(INET)

    # Relations
    concept: Mapped[Optional["Concept"]] = relationship("Concept", back_populates="views")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="views")

    __table_args__ = (
        Index("idx_concept_views_user_id", "user_id"),
        Index("idx_concept_views_concept_id", "concept_id"),
    )


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[PyUUID]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    used: Mapped[bool] = mapped_column(Boolean, server_default="false")

    # Relations
    user: Mapped[Optional["User"]] = relationship("User", back_populates="reset_tokens")

    __table_args__ = (Index("idx_password_reset_tokens_user_id", "user_id"),)


class UserContribution(Base):
    __tablename__ = "user_contributions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[PyUUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    concept_id: Mapped[Optional[int]] = mapped_column(ForeignKey("concepts.id"))
    action_type: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    details: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relations
    user: Mapped[Optional["User"]] = relationship("User", back_populates="contributions")
    concept: Mapped[Optional["Concept"]] = relationship("Concept", back_populates="contributions")

    __table_args__ = (
        Index("idx_user_contributions_created_at", "created_at"),
        Index("idx_user_contributions_user_id", "user_id"),
    )


class UserFavorite(Base):
    __tablename__ = "user_favorites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[PyUUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    concept_id: Mapped[Optional[int]] = mapped_column(ForeignKey("concepts.id"))
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    mathematicien_id: Mapped[Optional[int]] = mapped_column(ForeignKey("mathematiciens.id"))
    type_id: Mapped[Optional[int]] = mapped_column(ForeignKey("type.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    concept: Mapped[Optional["Concept"]] = relationship("Concept", back_populates="user_favorites")
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="user_favorites")
    mathematicien: Mapped[Optional["Mathematicien"]] = relationship("Mathematicien", back_populates="user_favorites")
    type: Mapped[Optional["Type"]] = relationship("Type", back_populates="user_favorites")

    __table_args__ = (
        CheckConstraint(
            "(CASE WHEN concept_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN category_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN mathematicien_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN type_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="chk_single_favorite_target",
        ),
        Index("idx_user_favorites_user_id", "user_id"),
    )


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[PyUUID]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    user: Mapped[Optional["User"]] = relationship("User", back_populates="sessions")

    __table_args__ = (Index("idx_user_sessions_user_id", "user_id"),)


class ConceptVersion(Base):
    __tablename__ = "concept_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    modified_by: Mapped[Optional[PyUUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    modified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    field_modified: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text)
    new_value: Mapped[Optional[str]] = mapped_column(Text)
    version_number: Mapped[Optional[int]] = mapped_column(Integer)
    global_version: Mapped[Optional[int]] = mapped_column(Integer)
    is_rollback: Mapped[bool] = mapped_column(Boolean, server_default="false")
    note: Mapped[Optional[str]] = mapped_column(Text)

    # Relations
    concept: Mapped["Concept"] = relationship("Concept", back_populates="versions")
    modifier: Mapped[Optional["User"]] = relationship("User", back_populates="modified_versions")

    __table_args__ = (
        Index("idx_concept_versions_concept_id", "concept_id"),
        Index("idx_concept_versions_modified_at", "modified_at"),
        Index("idx_concept_versions_modified_by", "modified_by"),
    )


class ApiLog(Base):
    __tablename__ = "api_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_api_logs_created_at", "created_at"),
        Index("idx_api_logs_endpoint", "endpoint"),
    )
