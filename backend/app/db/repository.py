# Vault-backed repository — stores all data as markdown files in the Obsidian vault.
# Replaces the SQLite implementation. Same public API, zero import changes elsewhere.
# ponytail: single file per entity, YAML frontmatter. Upgrade to SQLite if filesystem
#   I/O becomes a bottleneck (unlikely for single-user desktop use).

from app.db.vault import *  # noqa: F401, F403
