# Reel-Filter Frontend

React TypeScript frontend for the Reel-Filter movie content-aware search application.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Defaults should work for local development
   ```

3. Run development server:
   ```bash
   npm run dev
   ```

App will be available at http://localhost:3000

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm test` - Run unit tests
- `npm run test:ui` - Run tests with UI
- `npm run test:e2e` - Run end-to-end tests
- `npm run lint` - Run ESLint

## Components

- **ContentBadge** - Color-coded content score badges
- **FilterPanel** - Content threshold sliders and filters
- **MovieCard** - Movie display card with poster and badges
- **SearchPage** - Main search interface with filters
