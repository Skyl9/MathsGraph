"""init_database

Revision ID: 7323d2c13e11
Revises:
Create Date: 2026-05-14 15:50:58.704966

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7323d2c13e11"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
    create table categories
(
    id          serial primary key,
    nom         text not null
        unique,
    description text,
    parent_id   integer
                     references categories
                         on delete set null
);

create table mathematiciens
(
    id             serial
        primary key,
    nom            text not null
        unique,
    date_naissance date,
    date_deces     date,
    biographie     text,
    nationalite    text,
    domaine        text,
    url            text,
    recompenses    text,
    epoque         text
);

create index idx_mathematiciens_domaine
    on mathematiciens (domaine);

create table sources
(
    id               integer     default nextval('relations_id_seq'::regclass) not null
        constraint id
            primary key,
    titre            text,
    auteur           text,
    annee            integer,
    url              text,
    type             text                                                      not null
        constraint sources_type_check
            check (type = ANY (ARRAY ['livre'::text, 'article'::text, 'site_web'::text, 'autre'::text])),
    doi              varchar(255),
    isbn             varchar(13),
    date_publication date,
    editeur          varchar(255),
    langue           varchar(10) default 'fr'::character varying,
    abstract         text
);

create table tags
(
    id   serial
        primary key,
    name varchar(50) not null
        unique
);

create table type
(
    id   serial
        constraint type_pk
            primary key,
    type text not null
);


create table concepts
(
    id                serial
        primary key,
    nom               text                not null
        unique,
    enonce            text                not null,
    demonstration     text,
    verification      boolean   default false,
    date_modification timestamp default CURRENT_TIMESTAMP,
    mathematicien_id  integer
        constraint fk_mathematicien
            references mathematiciens,
    categorie_id      integer
        constraint fk_categorie
            references categories,
    type_id           integer   default 1 not null
        constraint concepts_type_id_fk
            references type
);

create table aliases
(
    id         serial
        primary key,
    concept_id integer not null
        constraint aliases_concepts_id_fk
            references concepts
            on delete cascade
        constraint fk_concept_principal
            references concepts
            on delete cascade,
    alias      text    not null
        unique
);


create table concept_tags
(
    concept_id integer not null
        references concepts,
    tag_id     integer not null
        references tags,
    created_at timestamp with time zone default CURRENT_TIMESTAMP,
    primary key (concept_id, tag_id)
);
create index idx_concept_tags_tag_id
    on concept_tags (tag_id);

create index idx_concepts_date_modification
    on concepts (date_modification);

create index idx_concepts_nom
    on concepts (nom);

create index idx_concepts_verification
    on concepts (verification);

create table concepts_sources
(
    concept_id integer not null
        references concepts
            on delete cascade,
    source_id  integer not null
        references sources
            on delete cascade,
    primary key (concept_id, source_id)
);


create table foreign_name
(
    id          serial primary key,
    "Nom_étranger" text                                                 not null,
    langue         text                                                 not null,
    concept_id     integer                                              not null
        constraint foreign_name_concepts_id_fk
            references concepts
);

create index idx_foreign_name_langue
    on foreign_name (langue);

create table positions
(
    id         serial
        primary key,
    concept_id integer          not null
        references concepts
            on delete cascade,
    vue        varchar(100)     not null,
    x          double precision not null,
    y          double precision not null,
    z          double precision not null,
    unique (concept_id, vue)
);



create table relations
(
    id             serial
        primary key,
    concept_source integer
        references concepts
            on delete cascade,
    concept_cible  integer
        references concepts
            on delete cascade,
    type_relation  text not null
        constraint relations_type_relation_check
            check (type_relation = ANY
                   (ARRAY ['utilise'::text, 'implication'::text, 'equivalence'::text, 'reciproque'::text])),
    date_relation  timestamp,
    description    text
);



create index idx_relations_cible
    on relations (concept_cible);

create index idx_relations_source
    on relations (concept_source);

create table users
(
    id                 serial
        primary key,
    username           varchar(50)                                                not null
        unique,
    email              varchar(100)                                               not null
        unique,
    password_hash      varchar(255)                                               not null,
    is_active          boolean                  default true,
    created_at         timestamp with time zone default CURRENT_TIMESTAMP,
    role               varchar(20)              default 'user'::character varying not null
        constraint users_role_check
            check ((role)::text = ANY
                   (ARRAY [('admin'::character varying)::text, ('user'::character varying)::text, ('moderator'::character varying)::text])),
    last_login         timestamp with time zone,
    preferred_language varchar(10)              default 'fr'::character varying,
    avatar_url         varchar(255),
    bio                text
);


create table comments
(
    id         serial
        primary key,
    concept_id integer
        references concepts
            on update cascade on delete cascade,
    user_id    integer not null
        references users,
    content    text    not null,
    created_at timestamp with time zone default CURRENT_TIMESTAMP,
    updated_at timestamp with time zone default CURRENT_TIMESTAMP,
    parent_id  integer
        references comments
            on update cascade on delete cascade,
    is_deleted boolean                  default false,
    field      text    not null,
    constraint chk_parent_not_self
        check ((parent_id IS NULL) OR (parent_id <> id))
);


create index idx_comments_concept_id
    on comments (concept_id);

create index idx_comments_parent_id
    on comments (parent_id);

create index idx_comments_user_id
    on comments (user_id);

create index idx_comments_created_at
    on comments (created_at);

create table concept_views
(
    id         serial
        primary key,
    concept_id integer
        references concepts,
    user_id    integer
        references users,
    viewed_at  timestamp with time zone default CURRENT_TIMESTAMP,
    ip_address inet
);


create table password_reset_tokens
(
    id         serial
        primary key,
    user_id    integer
        references users,
    token      varchar(255)             not null
        constraint unique_reset_token
            unique,
    expires_at timestamp with time zone not null,
    created_at timestamp with time zone default CURRENT_TIMESTAMP,
    used       boolean                  default false
);


create table user_contributions
(
    id          serial
        primary key,
    user_id     integer
        references users,
    concept_id  integer
        references concepts,
    action_type varchar(50),
    created_at  timestamp with time zone default CURRENT_TIMESTAMP,
    details     jsonb
);

create index idx_user_contributions_created_at
    on user_contributions (created_at);

create table user_favorites
(
    user_id          integer not null
        references users,
    concept_id       integer
        references concepts,
    created_at       timestamp with time zone default CURRENT_TIMESTAMP,
    id               serial
        constraint user_favorites_pk
            primary key,
    category_id      integer
        constraint user_favorites_categories_id_fk
            references categories,
    mathematicien_id integer
        constraint user_favorites_mathematiciens_id_fk
            references mathematiciens,
    type_id          integer
        constraint user_favorites_type_id_fk
            references type
);


create table user_sessions
(
    id         serial
        primary key,
    user_id    integer
        references users,
    token      varchar(255)             not null
        constraint unique_token
            unique,
    expires_at timestamp with time zone not null,
    created_at timestamp with time zone default CURRENT_TIMESTAMP
);

create table concept_versions
(
    id             serial
        primary key,
    concept_id     integer     not null
        references concepts
            on delete cascade,
    modified_by    integer
        references users,
    modified_at    timestamp with time zone default CURRENT_TIMESTAMP,
    field_modified varchar(50) not null,
    old_value      text,
    new_value      text,
    version_number integer,
    global_version integer,
    is_rollback    boolean                  default false,
    note           text
);

create index idx_concept_versions_concept_id
    on concept_versions (concept_id);

create index idx_concept_versions_modified_at
    on concept_versions (modified_at);

create function update_timestamp_modification() returns trigger
    language plpgsql
as
$$
BEGIN
  NEW.date_modification := CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$;


create function trigger_set_updated_at() returns trigger
    language plpgsql
as
$$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;



    """
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
