# Rocket Flight Simulator - Vercel Rewrite

This folder contains a Vercel-compatible Next.js rewrite of the rocket flight simulator.

## What it includes
- Rocket Library data and custom rocket fallback
- Lightweight simulation engine in TypeScript
- Launch vehicle comparison table
- Educational disclaimer and vehicle metadata support
- API route for simulation payloads

## Run locally
1. Open a terminal in this folder.
2. Install dependencies with `npm install`.
3. Start the app with `npm run dev`.
4. Open `http://localhost:3000` in your browser.

## Deploy to Vercel
1. Push this folder to a GitHub repository.
2. Sign in to Vercel.
3. Choose **Add New Project**.
4. Import the `vercel-app` folder as the project root.
5. Keep the framework preset as **Next.js**.
6. Leave the default build settings unless you add new tooling.
7. Click **Deploy**.

## Notes
- The app already includes API routes for simulation, vehicle data, and comparison data.
- The educational disclaimer is included in the UI and simulation payloads.
