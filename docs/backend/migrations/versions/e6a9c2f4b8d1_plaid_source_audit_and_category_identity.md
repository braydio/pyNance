# Plaid source audit and category identity migration

Owner: Backend
Last Updated: 2026-09-30
Status: Implemented

Revision `e6a9c2f4b8d1` follows `a3c8e1f4b2d7`.

The migration removes the unique constraint on legacy category primary/detailed paths. Canonical `category_slug` remains unique: several PFC categories can share the same old Plaid path without mutating each other's identity.

It creates `plaid_source_events`, with an index on transaction ID and a unique run/page/event/transaction key. Events retain their own account and transaction identifiers without cascade relationships to active rows. PostgreSQL triggers prevent update, deletion, or truncation of audit evidence. The migration does not itself rewrite financial records.

Use [the reconciliation command](../../app/services/plaid_audit.md) after backing up and testing an isolated restore. The command records a baseline before repairing retained evidence. Downgrade refuses destructive history deletion; a verified database backup is the complete rollback mechanism.
