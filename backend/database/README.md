# Database Assets

This directory keeps database artifacts out of the repository root.

## Layout

- `schema/`: current MariaDB table DDL used by the application and data-loading scripts.
- `archive/`: historical or backup DDL kept for reference only.

When adding a new table used by the app, place its DDL in `schema/` and link to it from the relevant documentation.
