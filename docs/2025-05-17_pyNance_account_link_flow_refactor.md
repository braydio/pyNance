# 2025-05-17 Repo Log - pyNance
`by: assistant
`goal: Refactor link account flow and separate product scoping from unlink execution.

# Tasklist
- X Explicit product scope selection with vmodel to Plaid
[ ] Refactor `linkPlaid` and `linkTeller` flows to be triggered ondumand
- [ ] Move link token generation closer to button clicks instead of mount
- [ ] No stale plaid products - choosen must exist for client instance

- [ ] Humanized disabled controls when products are unselected
- [ ] Patched linkConnection to controlled launching.

# Timestamps
- 2025-05-17 13:00 AM: Added new file `linkProviderLauncher.vue`
- 2025-05-17 13:30 AM: Replaced all direct token generation in `linkAccount.vue`
- 2025-05-17 13:35 AM: Refreshed reactive cycle with v-model based product scope
