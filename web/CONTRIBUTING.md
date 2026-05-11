# Contributing

## Overview

This project is a Next.js 16 application using the App Router, React 19, TypeScript, Tailwind CSS 4, and ESLint.

Before changing framework-specific code, read the relevant guide in `node_modules/next/dist/docs/`. This repo uses a newer Next.js version, so older conventions may be incorrect.

## Local Setup

1. Install dependencies:

```bash
npm install
```

2. Start the development server:

```bash
npm run dev
```

3. Open `http://localhost:3000`.

## Project Structure

- `app/`: App Router routes, layout, and global styles
- `components/`: reusable UI and home page sections
- `constants/`: shared static data
- `types/`: shared TypeScript types
- `public/`: static assets

## Development Guidelines

- Keep changes focused and minimal.
- Prefer TypeScript-safe changes over loose typing.
- Reuse existing patterns before introducing new abstractions.
- Use Heroicons via `@heroicons/react` when adding interface icons.
- Avoid invalid interactive nesting such as links wrapping buttons.

## Validation

Run these before submitting changes:

```bash
npm run lint
npm run build
```

## Pull Request Notes

When opening a pull request, include:

- What changed
- Why it changed
- Any UI impact
- How you validated the change

## Style Notes

- Use clear, user-facing copy.
- Keep components readable and small.
- Prefer semantic HTML.
- Preserve responsive behavior across mobile and desktop layouts.
