/* ═══════════════════════════════════════════════════════════════
   LABMIND AI — App.jsx (Phase 2 + Error Boundaries)
   ═══════════════════════════════════════════════════════════════
   Every screen route is wrapped with ScreenErrorBoundary so that
   a crash in one screen doesn't kill the entire app. The
   GlobalErrorBoundary in main.jsx catches anything that escapes.
   ═══════════════════════════════════════════════════════════════ */

import { useEffect, lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Lazy-loaded screens (heavy 3D dependencies)
const HolographicLabScreenLazy = lazy(() => import('./screens/HolographicLabScreen'));
import { useAppSettings } from './context/AppSettingsContext';
import { useAuth } from './context/AuthContext';
import { useNavigation } from './context/NavigationContext';
import { useAppState } from './context/AppStateContext';
import { fetchCurrentUser } from './services/apiClient';
import ProtectedRoute from './components/ProtectedRoute';
import ScreenErrorBoundary from './components/ScreenErrorBoundary';
import ActionModal from './components/ActionModal';
import ToastContainer from './components/ToastContainer';
import HolographicLineArtBackground from './components/HolographicLineArtBackground';
import AlertsPanel from './components/AlertsPanel';
import PWAInstallButton from './components/PWAInstallButton';

import SplashScreen from './screens/SplashScreen';
import LoginScreen from './screens/LoginScreen';
import DashboardScreen from './screens/DashboardScreen';
import UserProfile from './screens/UserProfile';
import StudentCommunityScreen from './screens/StudentCommunityScreen';
import LabResultsAnalyzerScreen from './screens/LabResultsAnalyzerScreen';
import SettingsScreen from './screens/SettingsScreen';
import RashaAIScreen from './screens/RashaAIScreen';
import BottomTabBar from './components/BottomTabBar';
import AnalysisHubScreen from './screens/AnalysisHubScreen';
import VirtualLabScreen from './screens/VirtualLabScreen';
import HematologyLabScreen from './screens/HematologyLabScreen';
import UrinalysisLabScreen from './screens/UrinalysisLabScreen';
import ParasitologyLabScreen from './screens/ParasitologyLabScreen';
import BiochemistryLabScreen from './screens/BiochemistryLabScreen';
import MicrobiologyLabScreen from './screens/MicrobiologyLabScreen';
import BloodBankLabScreen from './screens/BloodBankLabScreen';
import PatientArchive from './screens/PatientArchive';
import AcademicHubScreen from './screens/AcademicHubScreen';
import DigitalLibraryScreen from './screens/DigitalLibraryScreen';
import AIGenerativeLabScreen from './screens/AIGenerativeLabScreen';
import ArchiveScreen from './screens/ArchiveScreen';
import AITestingCenterScreen from './screens/AITestingCenterScreen';
import BattlefieldScreen from './screens/BattlefieldScreen';
import BattleAftermathScreen from './screens/BattleAftermathScreen';
import ArmoryStoreScreen from './screens/ArmoryStoreScreen';
import MyReportsScreen from './screens/MyReportsScreen';
import VideoGeneratorScreen from './screens/VideoGeneratorScreen';
import CurriculumVaultScreen from './screens/CurriculumVaultScreen';
import DisclaimerScreen from './screens/DisclaimerScreen';
export default function App() {
  const { isLight } = useAppSettings();
  const { currentUser, isBootstrapping, setCurrentUser } = useAuth();

  // ─── Navigation (from NavigationContext) ───
  const { currentView, navigate, setView, alertsOpen, setAlertsOpen } = useNavigation();

  // ─── App State (from AppStateContext) ───
  const {
    user, setUser,
    analystName, setAnalystName,
    alerts, clearAlert,
    handleAddRecord,
    isModalOpen, setIsModalOpen,
    toastEvent,
    handleImportData,
  } = useAppState();

  // ─── Navigation handler for screens ───
  const handleNavigate = navigate;

  // ─── JWT Session Restore ───
  useEffect(() => {
    if (!isBootstrapping && currentUser && (currentView === 'splash' || currentView === 'login')) {
      const serverName = currentUser.full_name || 'DR. COMMANDER ALPHA';
      setAnalystName(serverName);
      setUser(prev => ({
        ...prev,
        name: serverName,
        email: currentUser.email,
        rank: currentUser.rank_title || prev.rank,
        avatar: currentUser.avatar_url || prev.avatar,
      }));
      setView('dashboard');

    }
  }, [isBootstrapping, currentUser]);

  // ─── Login handler ───
  const handleLogin = async (name) => {
    try {
      const serverUser = await fetchCurrentUser();
      setCurrentUser(serverUser);
      const serverName = serverUser.full_name || name || 'DR. COMMANDER ALPHA';
      setAnalystName(serverName);
      setUser(prev => ({
        ...prev,
        name: serverName,
        email: serverUser.email,
        rank: serverUser.rank_title || prev.rank,
        avatar: serverUser.avatar_url || prev.avatar,
      }));
    } catch {
      const finalName = name || 'DR. COMMANDER ALPHA';
      setAnalystName(finalName);
      setUser(prev => ({ ...prev, name: finalName }));
    }
    navigate('dashboard');
  };

  // ─── Shared props ───
  const navProps = { onNavigate: handleNavigate };

  return (
    <>
      <ToastContainer toastEvent={toastEvent} />

      <div className="min-h-dvh w-full overflow-x-hidden relative">
        {!isLight && <HolographicLineArtBackground />}

        <Routes>
          {/* ─── Public Routes ─── */}
          <Route
            path="/"
            element={
              !isBootstrapping && currentUser
                ? <Navigate to="/dashboard" replace />
                : <ScreenErrorBoundary screenName="Splash">
                    <SplashScreen onStart={() => {
                      const disclaimerAccepted = localStorage.getItem('labmind_disclaimer_accepted');
                      if (!disclaimerAccepted) {
                        navigate('disclaimer');
                      } else {
                        navigate('login');
                      }
                    }} />
                  </ScreenErrorBoundary>
            }
          />
          <Route
            path="/disclaimer"
            element={
              <ScreenErrorBoundary screenName="Disclaimer">
                <DisclaimerScreen onAccept={() => navigate('login')} />
              </ScreenErrorBoundary>
            }
          />
          <Route
            path="/login"
            element={
              !isBootstrapping && currentUser
                ? <Navigate to="/dashboard" replace />
                : <ScreenErrorBoundary screenName="Login">
                    <LoginScreen onLogin={handleLogin} />
                  </ScreenErrorBoundary>
            }
          />

          {/* ─── Dashboard & Main Tabs ─── */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="Dashboard">
                <DashboardScreen
                  onNavigate={handleNavigate}
                  alerts={alerts}
                  onOpenModal={() => setIsModalOpen(true)}
                  analystName={analystName}
                  user={user}
                />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="UserProfile">
                <UserProfile
                  onNavigate={handleNavigate}
                  user={user}
                  setUser={setUser}
                />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/community" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="StudentCommunity">
                <StudentCommunityScreen />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/settings" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="Settings">
                <SettingsScreen />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/ai-assistant" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="RashaAI">
                <RashaAIScreen />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />

          {/* ─── Analysis Hub ─── */}
          <Route path="/analysis" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="AnalysisHub">
                <AnalysisHubScreen {...navProps} />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/lab-results-analyzer" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="LabResultsAnalyzer">
                <LabResultsAnalyzerScreen />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />

          {/* ─── Virtual Lab + Sub-labs ─── */}
          <Route path="/lab" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="VirtualLab">
                <VirtualLabScreen {...navProps} alerts={alerts} clearAlert={clearAlert} />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/lab/hematology" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="HematologyLab">
                <HematologyLabScreen {...navProps} onAddRecord={handleAddRecord} />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/lab/urinalysis" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="UrinalysisLab">
                <UrinalysisLabScreen {...navProps} onAddRecord={handleAddRecord} />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/lab/parasitology" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="ParasitologyLab">
                <ParasitologyLabScreen {...navProps} onAddRecord={handleAddRecord} />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/lab/biochemistry" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="BiochemistryLab">
                <BiochemistryLabScreen {...navProps} />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/lab/microbiology" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="MicrobiologyLab">
                <MicrobiologyLabScreen {...navProps} />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/lab/blood-bank" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="BloodBankLab">
                <BloodBankLabScreen {...navProps} />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />

          {/* ─── Patient Archive ─── */}
          <Route path="/patients" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="PatientArchive">
                <PatientArchive {...navProps} />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />

          {/* ─── Academic Hub + Sub-screens ─── */}
          <Route path="/academic" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="AcademicHub">
                <AcademicHubScreen {...navProps} />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/academic/library" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="DigitalLibrary">
                <DigitalLibraryScreen {...navProps} />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/academic/ai-lab" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="AIGenerativeLab">
                <AIGenerativeLabScreen {...navProps} />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/academic/ai-archive" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="AIArchive">
                <ArchiveScreen {...navProps} />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/academic/testing-center" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="AITestingCenter">
                <AITestingCenterScreen />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/academic/video-generator" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="VideoGenerator">
                <VideoGeneratorScreen />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/academic/holo-lab" element={
            <ProtectedRoute>
              <Suspense fallback={null}>
                <HolographicLabScreenLazy />
              </Suspense>
            </ProtectedRoute>
          } />
          <Route path="/academic/curriculum-vault" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="CurriculumVault">
                <CurriculumVaultScreen />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />

          {/* ─── Gamification ─── */}
          <Route path="/battle" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="Battlefield">
                <BattlefieldScreen />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/battle/results" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="BattleAftermath">
                <BattleAftermathScreen />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />
          <Route path="/store" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="ArmoryStore">
                <ArmoryStoreScreen />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />

          {/* ─── Reports ─── */}
          <Route path="/reports" element={
            <ProtectedRoute>
              <ScreenErrorBoundary screenName="MyReports">
                <MyReportsScreen {...navProps} />
              </ScreenErrorBoundary>
            </ProtectedRoute>
          } />

          {/* ─── Catch-all ─── */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        {/* ─── Overlays (state-driven, not routes) ─── */}
        <AlertsPanel isOpen={alertsOpen} onClose={() => setAlertsOpen(false)} />

        <ActionModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onImportData={handleImportData}
        />


        {/* ─── Bottom Tab Bar Visibility Logic ─── */}
        {(() => {
          const visibleViews = [
            'dashboard', 'community', 'profile', 'settings', 
            'ai-assistant', 'armory', 'academic-hub', 'my-reports', 'archive'
          ];
          return visibleViews.includes(currentView) ? <BottomTabBar /> : null;
        })()}

        <PWAInstallButton />
      </div>
    </>
  );
}
