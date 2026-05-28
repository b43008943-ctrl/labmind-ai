# LabMind AI — Navigation System Audit

> **Purpose**: Complete documentation of the current `useState`-based navigation state machine,
> to serve as the migration blueprint for `react-router-dom`.
>
> Generated: 2026-04-09

---

## PART 1 — CURRENT VIEW STATES

The entire navigation system is controlled by a single `useState` in `App.jsx`:

```js
const [activeScreen, setActiveScreen] = useState('splash');
```

Each value of `activeScreen` maps to exactly one screen component. The `handleNavigate` function intercepts the `'alerts'` target to open an overlay panel instead of changing screens.

| # | View Key | Screen Component | File | Props Passed from App.jsx |
|---|----------|-----------------|------|---------------------------|
| 1 | `splash` | `SplashScreen` | `SplashScreen.jsx` | `onStart` (→ sets screen to `login`) |
| 2 | `login` | `LoginScreen` | `LoginScreen.jsx` | `onLogin(name)` (→ fetches user, sets screen to `dashboard`) |
| 3 | `dashboard` | `DashboardPager` ¹ | `DashboardPager.jsx` | `onNavigate`, `alerts`, `onOpenModal`, `analystName`, `user`, `setUser` |
| 4 | `analysis` | `AnalysisHubScreen` | `AnalysisHubScreen.jsx` | `onNavigate` (note: uses `setActiveScreen` directly) |
| 5 | `virtual-lab` | `VirtualLabScreen` | `VirtualLabScreen.jsx` | `onNavigate`, `alerts`, `clearAlert` |
| 6 | `hematology-lab` | `HematologyLabScreen` | `HematologyLabScreen.jsx` | `onNavigate`, `onAddRecord` |
| 7 | `urinalysis` | `UrinalysisLabScreen` | `UrinalysisLabScreen.jsx` | `onNavigate`, `onAddRecord` |
| 8 | `parasitology-lab` | `ParasitologyLabScreen` | `ParasitologyLabScreen.jsx` | `onNavigate`, `onAddRecord` |
| 9 | `clinical` | `BiochemistryLabScreen` | `BiochemistryLabScreen.jsx` | `onNavigate` |
| 10 | `microbiology-lab` | `MicrobiologyLabScreen` | `MicrobiologyLabScreen.jsx` | `onNavigate` |
| 11 | `bloodbank-lab` | `BloodBankLabScreen` | `BloodBankLabScreen.jsx` | `onNavigate` |
| 12 | `archive` | `PatientArchive` | `PatientArchive.jsx` | `onNavigate` |
| 13 | `academic-hub` | `AcademicHubScreen` | `AcademicHubScreen.jsx` | `onNavigate` |
| 14 | `knowledge-library` | `DigitalLibraryScreen` | `DigitalLibraryScreen.jsx` | `onNavigate`, `onReadingContextChange` |
| 15 | `ailab` | `AIGenerativeLabScreen` | `AIGenerativeLabScreen.jsx` | `onNavigate` |
| 16 | `ai-archive` | `ArchiveScreen` | `ArchiveScreen.jsx` | `onNavigate` |
| 17 | `ai-testing-center` | `AITestingCenterScreen` | `AITestingCenterScreen.jsx` | `onNavigate` |
| 18 | `battlefield` | `BattlefieldScreen` | `BattlefieldScreen.jsx` | `onNavigate` |
| 19 | `aftermath` | `BattleAftermathScreen` | `BattleAftermathScreen.jsx` | `onNavigate` |
| 20 | `armory` | `ArmoryStoreScreen` | `ArmoryStoreScreen.jsx` | `onNavigate` |
| 21 | `my-reports` | `MyReportsScreen` | `MyReportsScreen.jsx` | `onNavigate` |

**¹ DashboardPager is special** — it is a horizontal carousel component that embeds 3 sub-screens:

| Pager Panel | Position | Sub-screen Component | Props from Pager |
|---|---|---|---|
| Left (0) | Profile | `UserProfile` | `onNavigate`, `isInPager=true`, `user`, `setUser`, `onModalChange` |
| Center (1) | Dashboard | `DashboardScreen` | `onNavigate`, `alerts`, `onOpenModal`, `analystName`, `user`, `onSlideToCommunity`, `activeView` |
| Right (2) | Community | `StudentCommunityScreen` | `onNavigate`, `onSlideBack` |

The pager renders a persistent `Navigation` bottom bar with 4 icons:
- **User** → swipe to Profile panel
- **Home** → swipe to Dashboard panel
- **Biometric Upload** → opens `ActionModal` (upload portal)
- **Network** → swipe to Community panel

---

## PART 2 — NAVIGATION MAP

### Screen-by-Screen Navigation Targets

Each entry shows: where the user can GO from that screen, and how they get back.

---

#### 1. SplashScreen
- **Outbound**: `login` (via `onStart` callback)
- **Back**: None (entry point)

#### 2. LoginScreen
- **Outbound**: `dashboard` (via `onLogin` callback after authentication)
- **Back**: None (would need logout)

#### 3. DashboardPager (containing Dashboard, Profile, Community)

##### 3a. DashboardScreen (center panel)
- **Outbound**:
  - → `alerts` (header bell icon — intercepted by `handleNavigate` to open `AlertsPanel` overlay)
  - → `my-reports` (header "REPORTS" button)
  - → `archive` (header "ARCHIVE" button)
  - → `analysis` (via "Change Intelligence" card click)
  - → `virtual-lab` (via "Virtual Lab" card click)
  - → `academic-hub` (via "Academic Hub" card click)
  - → `modal` (via "Performance" card click — opens `ActionModal`)
- **Navigation pattern**: Uses `handleNavigation()` with 600ms exit animation delay, then calls `onNavigate(target)`
- **Back**: None (home screen) — Pager swipe to Profile or Community

##### 3b. UserProfile (left panel)
- **Outbound**: No screen navigation (stays within pager)
- **Back**: Swipe right to Dashboard panel

##### 3c. StudentCommunityScreen (right panel)
- **Outbound**:
  - → `dashboard` (back chevron button, line 236)
  - → `armory` (store/shop button, line 1106)
  - → `battlefield` (battle button, line 1759)
- **Back**: `onSlideBack` → swipe to Dashboard panel

---

#### 4. AnalysisHubScreen
- **Outbound**: → `dashboard` (back arrow button)
- **Back**: → `dashboard`
- **Navigation pattern**: Uses `handleNavigation()` with 600ms exit animation delay

#### 5. VirtualLabScreen
- **Outbound**:
  - → `dashboard` (back arrow)
  - → `hematology-lab` (Hematology card)
  - → `urinalysis` (Urinalysis card)
  - → `microbiology-lab` (Microbiology card)
  - → `clinical` (Clinical Biochemistry card)
  - → `parasitology-lab` (Parasitology card)
  - → `bloodbank-lab` (Blood Bank card)
- **Back**: → `dashboard`
- **Navigation pattern**: Uses `handleNavigation()` with 600ms exit animation delay
- **Extra**: Has "Learning Mode" toggle; clears alert badges on card click

#### 6. HematologyLabScreen
- **Outbound**: → `virtual-lab` (back arrow)
- **Back**: → `virtual-lab`
- **Extra**: Has `SidebarNavigation` component with → `dashboard` shortcut
- **Extra**: Receives `onAddRecord` prop — adds records to App.jsx's `pastRecords` state

#### 7. UrinalysisLabScreen
- **Outbound**: → `virtual-lab` (back arrow)
- **Back**: → `virtual-lab`
- **Extra**: Has `SidebarNavigation` component with → `dashboard` shortcut

#### 8. ParasitologyLabScreen
- **Outbound**: → `virtual-lab` (back arrow)
- **Back**: → `virtual-lab`
- **Extra**: Has `SidebarNavigation` component with → `dashboard` shortcut

#### 9. BiochemistryLabScreen (key: `clinical`)
- **Outbound**: → `virtual-lab` (back arrow)
- **Back**: → `virtual-lab`
- **Extra**: Has `SidebarNavigation` component with → `dashboard` shortcut

#### 10. MicrobiologyLabScreen
- **Outbound**: → `virtual-lab` (back arrow)
- **Back**: → `virtual-lab`
- **Extra**: Has `SidebarNavigation` component with → `dashboard` shortcut

#### 11. BloodBankLabScreen
- **Outbound**: → `virtual-lab` (back arrow)
- **Back**: → `virtual-lab`
- **Extra**: Has `SidebarNavigation` component with → `dashboard` shortcut

#### 12. PatientArchive (key: `archive`)
- **Outbound**: → `dashboard` (back arrow)
- **Back**: → `dashboard`

#### 13. AcademicHubScreen
- **Outbound**:
  - → `dashboard` (back arrow, line 570)
  - → `knowledge-library` (Knowledge Library tile — via `handleTileClick('knowledge-library')`)
  - → `ailab` (AI Generative Lab tile — via `handleTileClick('ailab')`)
  - → (internal) `curriculum` tile opens Curriculum Vault modal (does NOT navigate)
  - → (internal) `bio-lab` tile opens Bio Holo Lab modal (does NOT navigate)
- **Back**: → `dashboard`
- **Navigation pattern**: `handleTileClick(tileId)` calls `onNavigate(tileId)` for external tiles, opens modals for `curriculum` and `bio-lab`

#### 14. DigitalLibraryScreen (key: `knowledge-library`)
- **Outbound**: → `academic-hub` (back button, lines 212 & 304)
- **Back**: → `academic-hub`
- **Extra**: Passes `onReadingContextChange` up to App.jsx (used by `FloatingAIAssistant`)

#### 15. AIGenerativeLabScreen (key: `ailab`)
- **Outbound**:
  - → `ai-archive` (after video synthesis completes, line 448 — navigates after 1.5s delay)
  - → `academic-hub` (back button, line 967)
- **Back**: → `academic-hub`

#### 16. ArchiveScreen (key: `ai-archive`)
- **Outbound**: → `academic-hub` (back arrow, line 63)
- **Back**: → `academic-hub`

#### 17. AITestingCenterScreen (key: `ai-testing-center`)
- **Outbound**: → `academic-hub` (back button, line 195)
- **Back**: → `academic-hub`
- **Extra**: Receives optional `directText` and `onExitPortal` props (currently unused from App.jsx)
- **Note**: No screen currently navigates TO this screen — it's only defined in App.jsx's state machine. Likely accessed via a mechanism not captured (or temporarily orphaned).

#### 18. BattlefieldScreen
- **Outbound**:
  - → `aftermath` (on battle end, line 37)
  - → `dashboard` (exit/forfeit button, line 51)
- **Back**: → `dashboard`

#### 19. BattleAftermathScreen (key: `aftermath`)
- **Outbound**: → `dashboard` (return button, line 200)
- **Back**: → `dashboard`

#### 20. ArmoryStoreScreen (key: `armory`)
- **Outbound**: → `dashboard` (back arrow, line 121)
- **Back**: → `dashboard`

#### 21. MyReportsScreen (key: `my-reports`)
- **Outbound**: → `dashboard` (back button, line 105)
- **Back**: → `dashboard`

---

### Overlay Components (NOT screens — no URL)

| Component | Trigger | Close |
|---|---|---|
| `AlertsPanel` | `onNavigate('alerts')` intercepted in `handleNavigate` | `onClose` button |
| `ActionModal` | `onOpenModal()` from Dashboard cards or bottom nav | `onClose` button |
| `FloatingAIAssistant` | Auto-rendered when not on `splash` or `login` | Toggle button |

---

## PART 3 — NAVIGATION GRAPH

```
                                ┌─────────┐
                                │  SPLASH  │
                                └────┬─────┘
                                     │ onStart
                                ┌────▼─────┐
                                │  LOGIN   │
                                └────┬─────┘
                                     │ onLogin
                       ┌─────────────▼──────────────┐
                       │     DASHBOARD PAGER         │
                       │  ┌────────┬────────┬──────┐ │
                       │  │Profile │ Dash   │Commu-│ │
                       │  │(swipe) │(center)│ nity │ │
                       │  └────────┴───┬────┴──┬───┘ │
                       └───────────────┼───────┼─────┘
                          ┌────────────┼───────┼────────────┐
                          │            │       │            │
                    ┌─────▼──┐   ┌─────▼──┐ ┌──▼─────┐ ┌───▼────┐
                    │analysis│   │virtual │ │archive │ │my-     │
                    │  hub   │   │  lab   │ │(patient│ │reports │
                    └────────┘   └───┬────┘ └────────┘ └────────┘
                                     │
              ┌──────────┬───────────┼───────────┬──────────┬──────────┐
              │          │           │           │          │          │
          ┌───▼───┐  ┌───▼───┐  ┌───▼────┐  ┌──▼────┐ ┌──▼─────┐ ┌─▼───────┐
          │hemato-│  │urinal-│  │micro-  │  │biochem│ │parasit-│ │bloodbank│
          │ logy  │  │ ysis  │  │biology │  │istry  │ │ology   │ │         │
          └───────┘  └───────┘  └────────┘  └───────┘ └────────┘ └─────────┘


   Community ──► armory
   Community ──► battlefield ──► aftermath ──► dashboard

   Dashboard ──► academic-hub ──┬──► knowledge-library
                                ├──► ailab ──► ai-archive
                                └──► (curriculum vault - modal)
                                     (bio holo lab - modal)

   App.jsx defines ──► ai-testing-center (currently orphaned — no inbound navigation)
```

---

## PART 4 — STATE & DATA PASSING ANALYSIS

### State Managed in App.jsx (lifted state)

| State Variable | Type | Used By | Migration Risk |
|---|---|---|---|
| `activeScreen` | `string` | Core navigator | **Will be replaced** by `react-router-dom` |
| `user` | `object` | `DashboardPager` → `DashboardScreen`, `UserProfile` | Move to context or keep in layout |
| `analystName` | `string` | `DashboardPager` → `DashboardScreen`, `FloatingAIAssistant` | Move to context |
| `alerts` | `object` | `DashboardPager` → `DashboardScreen`, `VirtualLabScreen` | Move to context |
| `pastRecords` | `array` | `HematologyLabScreen`, `UrinalysisLabScreen`, `ParasitologyLabScreen` | Move to context |
| `isModalOpen` | `boolean` | `ActionModal` | Keep local to layout |
| `toastEvent` | `object` | `ToastContainer` | Keep local to layout |
| `nymphState` | `string` | `FloatingAIAssistant` | Keep local to layout |
| `readingContext` | `any` | `DigitalLibraryScreen` → `FloatingAIAssistant` | Move to context |
| `alertsOpen` | `boolean` | `AlertsPanel` | Keep local to layout |

### Critical Props Passed Down

| Prop | From | To | Purpose |
|---|---|---|---|
| `onNavigate` | App.jsx | All screens | Navigation callback — **will become `useNavigate()`** |
| `onAddRecord` | App.jsx | HematologyLab, Urinalysis, Parasitology | Adds to `pastRecords` — needs context |
| `alerts` / `clearAlert` | App.jsx | VirtualLabScreen | Alert badge system — needs context |
| `onReadingContextChange` | App.jsx | DigitalLibraryScreen | Feeds reading context to FloatingAIAssistant |
| `user` / `setUser` | App.jsx | DashboardPager → UserProfile | User state — already partially in AuthContext |
| `onOpenModal` | App.jsx | DashboardPager → DashboardScreen, Navigation | Opens ActionModal — keep in layout |

---

## PART 5 — TRANSITION ANIMATION PATTERN

Most screens use a consistent 3-phase transition pattern:

```js
// Phase 1: Mount with hidden state
const [screenState, setScreenState] = useState('screen-transition-hidden');

// Phase 2: Enter animation (50ms after mount)
useEffect(() => {
    const t = setTimeout(() => setScreenState('screen-visible'), 50);
    return () => clearTimeout(t);
}, []);

// Phase 3: Exit animation (600ms) before navigation
const handleNavigation = (target) => {
    setScreenState('screen-exit');
    setTimeout(() => onNavigate(target), 600);
};
```

> **Migration note**: With `react-router-dom`, this pattern would need to be replaced with `framer-motion`'s `AnimatePresence` + route-level transitions, or a similar exit animation strategy. The 600ms `setTimeout` pattern will NOT work with router-based navigation.

---

## PART 6 — PROPOSED URL STRUCTURE

| View Key | Proposed Route | Notes |
|---|---|---|
| `splash` | `/` | Redirect to `/dashboard` if authenticated |
| `login` | `/login` | Redirect to `/dashboard` if authenticated |
| `dashboard` | `/dashboard` | DashboardPager (center panel) |
| `dashboard` (profile) | `/profile` | DashboardPager (left panel, activeView=0) |
| `dashboard` (community) | `/community` | DashboardPager (right panel, activeView=2) |
| `analysis` | `/analysis` | |
| `virtual-lab` | `/lab` | |
| `hematology-lab` | `/lab/hematology` | Nested under lab |
| `urinalysis` | `/lab/urinalysis` | Nested under lab |
| `parasitology-lab` | `/lab/parasitology` | Nested under lab |
| `clinical` | `/lab/biochemistry` | Renamed for clarity |
| `microbiology-lab` | `/lab/microbiology` | Nested under lab |
| `bloodbank-lab` | `/lab/bloodbank` | Nested under lab |
| `archive` | `/patients` | PatientArchive |
| `academic-hub` | `/academic` | |
| `knowledge-library` | `/academic/library` | Nested under academic |
| `ailab` | `/academic/ai-lab` | Nested under academic |
| `ai-archive` | `/academic/ai-archive` | Nested under academic |
| `ai-testing-center` | `/academic/testing` | Nested under academic |
| `battlefield` | `/battle` | |
| `aftermath` | `/battle/results` | Nested under battle |
| `armory` | `/store` | |
| `my-reports` | `/reports` | |

---

## PART 7 — RISK ASSESSMENT

### HIGH RISK
1. **DashboardPager swipe physics** — The horizontal carousel with touch gestures needs careful integration with router. The pager manages its own `activeView` state (0/1/2) independent of routes. URL must sync with swipe position.
2. **Exit animation pattern** — 17+ screens use `setTimeout(() => onNavigate(target), 600)`. Router transitions don't support delayed navigation. Need `framer-motion` `AnimatePresence` with route keys.
3. **`nymphState` synchronization** — The `FloatingAIAssistant` changes behavior based on `activeScreen`. With router, this needs to read from `useLocation()` instead.

### MEDIUM RISK
4. **Lifted state in App.jsx** — `alerts`, `pastRecords`, `user`, `readingContext` are passed as props. These need to move to React Context before the router migration.
5. **`handleNavigate` intercept** — The `'alerts'` target is intercepted to open an overlay, not navigate. This pattern must be preserved in the router migration.
6. **`onAddRecord` prop** — 3 lab screens add records to App state. This tight coupling needs a context provider.

### LOW RISK
7. **Overlay components** — `AlertsPanel`, `ActionModal`, `FloatingAIAssistant` are independent of routing.
8. **`SidebarNavigation`** — Only one nav target (`dashboard`) — simple to convert.
9. **Orphaned route** — `ai-testing-center` has no inbound navigation from any screen. Verify if this is intentional or a bug.

---

## PART 8 — MIGRATION PREREQUISITES

Before starting the `react-router-dom` migration:

1. **Create `AppStateContext`** — Move `alerts`, `pastRecords`, `user`, `analystName`, `readingContext` out of `App.jsx` into a context provider
2. **Install `react-router-dom`** — `npm install react-router-dom`
3. **Create Layout component** — Extract `ToastContainer`, `HolographicLineArtBackground`, `AlertsPanel`, `ActionModal`, `FloatingAIAssistant` into a shared `AppLayout` component
4. **Resolve orphaned route** — Decide what to do with `ai-testing-center` (connect it or remove it)
5. **Design transition strategy** — Replace `setTimeout` exit animations with `framer-motion` `AnimatePresence` + route transition wrapper
