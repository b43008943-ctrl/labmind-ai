/* ═══════════════════════════════════════════════════════════════
   LABMIND AI — Route Configuration
   ═══════════════════════════════════════════════════════════════
   Phase 1: Route definitions ONLY — not yet connected to the
   React Router <RouterProvider>. These map old view keys to
   future URL paths for the Phase 2 migration.
   ═══════════════════════════════════════════════════════════════ */

/**
 * Maps legacy `activeScreen` view keys → future URL paths.
 * Used by NavigationContext to translate between systems.
 */
const routeConfig = [
  // ─── Auth ───
  { path: '/',                    viewKey: 'splash' },
  { path: '/login',               viewKey: 'login' },
  { path: '/disclaimer',          viewKey: 'disclaimer' },

  // ─── Dashboard & Main Tabs ───
  { path: '/dashboard',           viewKey: 'dashboard' },
  { path: '/profile',             viewKey: 'profile' },
  { path: '/community',           viewKey: 'community' },
  { path: '/settings',            viewKey: 'settings' },
  { path: '/ai-assistant',        viewKey: 'ai-assistant' },

  // ─── Analysis ───
  { path: '/analysis',            viewKey: 'analysis' },
  { path: '/lab-results-analyzer',viewKey: 'lab-results-analyzer' },

  // ─── Virtual Lab + Sub-labs ───
  { path: '/lab',                 viewKey: 'virtual-lab' },
  { path: '/lab/hematology',      viewKey: 'hematology-lab' },
  { path: '/lab/urinalysis',      viewKey: 'urinalysis' },
  { path: '/lab/parasitology',    viewKey: 'parasitology-lab' },
  { path: '/lab/biochemistry',    viewKey: 'clinical' },
  { path: '/lab/microbiology',    viewKey: 'microbiology-lab' },
  { path: '/lab/blood-bank',      viewKey: 'bloodbank-lab' },

  // ─── Academic Hub + Sub-screens ───
  { path: '/academic',                viewKey: 'academic-hub' },
  { path: '/academic/library',        viewKey: 'knowledge-library' },
  { path: '/academic/ai-lab',         viewKey: 'ailab' },
  { path: '/academic/ai-archive',     viewKey: 'ai-archive' },
  { path: '/academic/testing-center', viewKey: 'ai-testing-center' },
  { path: '/academic/video-generator',viewKey: 'video-generator' },
  { path: '/academic/holo-lab',       viewKey: 'holo-lab' },
  { path: '/academic/curriculum-vault', viewKey: 'curriculum-vault' },

  // ─── Gamification ───
  { path: '/battle',              viewKey: 'battlefield' },
  { path: '/battle/results',      viewKey: 'aftermath' },
  { path: '/store',               viewKey: 'armory' },

  // ─── Data & Reports ───
  { path: '/patients',            viewKey: 'archive' },
  { path: '/reports',             viewKey: 'my-reports' },
];

/**
 * Lookup helpers for bi-directional mapping.
 */
export const viewKeyToPath = Object.fromEntries(
  // For viewKeys that map to multiple paths (e.g. dashboard → /dashboard, /profile, /community),
  // the FIRST entry wins — which is the primary path.
  routeConfig.reduce((acc, { path, viewKey }) => {
    if (!acc.has(viewKey)) acc.set(viewKey, path);
    return acc;
  }, new Map())
);

export const pathToViewKey = Object.fromEntries(
  routeConfig.map(({ path, viewKey }) => [path, viewKey])
);

export default routeConfig;
