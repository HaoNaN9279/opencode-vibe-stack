# Global Rules

These rules apply to all AI agent sessions, regardless of project or domain.

## General Conduct
- Always read AGENTS.md files in the project hierarchy before starting work.
- Follow the project's existing code style and conventions.
- Do not suppress type errors with `as any`, `@ts-ignore`, or `@ts-expect-error`.
- Never commit unless explicitly requested by the user.
- When refactoring, ensure safe refactorings using appropriate tools.

## Communication
- Be concise. No flattery. No unnecessary status updates.
- Match the user's communication style.
- When the user's approach seems problematic, state concerns concisely and propose alternatives.

## Security
- Never hardcode secrets, API keys, or credentials.
- Never commit sensitive files (.env, credentials, private keys).
- Validate all user inputs before processing.

## Code Quality
- Prefer existing libraries over new dependencies.
- Prefer small, focused changes over large refactors.
- Fix root causes, not symptoms.
- Leave code in a working state after each change.
