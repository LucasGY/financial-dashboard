CREATE TABLE IF NOT EXISTS intelligence_event (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    event_key VARCHAR(255) NOT NULL,
    domain VARCHAR(32) NOT NULL,
    title TEXT NOT NULL,
    title_zh TEXT NULL,
    summary TEXT NOT NULL,
    tldr_zh TEXT NULL,
    first_seen_at DATETIME NOT NULL,
    last_seen_at DATETIME NOT NULL,
    entity_ids JSON NOT NULL,
    event_tags JSON NOT NULL,
    topic_tags JSON NOT NULL,
    importance_score INT NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'new',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_intelligence_event_key (event_key),
    KEY idx_intelligence_event_domain_date (domain, last_seen_at),
    KEY idx_intelligence_event_importance (importance_score)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS intelligence_event_source (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    event_id BIGINT UNSIGNED NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    source_name VARCHAR(128) NOT NULL,
    source_platform VARCHAR(64) NOT NULL,
    source_type VARCHAR(64) NOT NULL,
    source_url TEXT NULL,
    source_role VARCHAR(32) NOT NULL DEFAULT 'primary',
    original_url TEXT NULL,
    quoted_url TEXT NULL,
    reposted_url TEXT NULL,
    reply_to_url TEXT NULL,
    assets JSON NOT NULL,
    extracted_at DATETIME NULL,
    extraction_status VARCHAR(32) NULL,
    author_avatar_url TEXT NULL,
    author_name TEXT NULL,
    source_date DATETIME NOT NULL,
    title TEXT NOT NULL,
    title_en TEXT NULL,
    title_zh TEXT NULL,
    summary TEXT NULL,
    summary_en TEXT NULL,
    summary_zh TEXT NULL,
    raw_content MEDIUMTEXT NULL,
    raw_content_en MEDIUMTEXT NULL,
    raw_content_zh MEDIUMTEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_intelligence_source_external_id (external_id),
    KEY idx_intelligence_source_event_id (event_id),
    KEY idx_intelligence_source_date (source_date),
    CONSTRAINT fk_intelligence_source_event
        FOREIGN KEY (event_id)
        REFERENCES intelligence_event(id)
        ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

ALTER TABLE intelligence_event_source
    ADD COLUMN IF NOT EXISTS title_en TEXT NULL AFTER title,
    ADD COLUMN IF NOT EXISTS title_zh TEXT NULL AFTER title,
    ADD COLUMN IF NOT EXISTS summary_en TEXT NULL AFTER summary,
    ADD COLUMN IF NOT EXISTS summary_zh TEXT NULL AFTER summary,
    ADD COLUMN IF NOT EXISTS raw_content_en MEDIUMTEXT NULL AFTER raw_content,
    ADD COLUMN IF NOT EXISTS raw_content_zh MEDIUMTEXT NULL AFTER raw_content;
