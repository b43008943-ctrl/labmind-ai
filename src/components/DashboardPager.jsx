import { useState, useRef } from 'react';
import DashboardScreen from '../screens/DashboardScreen';
import StudentCommunityScreen from '../screens/StudentCommunityScreen';
import UserProfile from '../screens/UserProfile';
import Navigation from './Navigation';

/* ═══════════════════════════════════════════════════════════════
   DASHBOARD PAGER — Horizontal View Pager
   Holds Dashboard (left) and Community (right) in a sliding
   carousel with native-feeling swipe + icon navigation.
   Navigation bar is rendered as a persistent fixed overlay.
   ═══════════════════════════════════════════════════════════════ */

export default function DashboardPager({ onNavigate, alerts, onOpenModal, analystName, user, setUser }) {
    const [activeView, setActiveView] = useState(1); // 0 = Profile, 1 = Dashboard, 2 = Community
    const touchStartX = useRef(0);
    const touchStartY = useRef(0);
    const swipeLocked = useRef(false); // TRUE when a child modal is open

    // ─── Swipe gesture handlers ───
    const handleTouchStart = (e) => {
        // Guard: Ignore ALL touches when a child modal is open
        if (swipeLocked.current) return;
        if (e.target.closest('[data-modal-overlay]')) return;
        touchStartX.current = e.changedTouches[0].screenX;
        touchStartY.current = e.changedTouches[0].screenY;
    };

    const handleTouchEnd = (e) => {
        // Guard: Ignore ALL touches when a child modal is open
        if (swipeLocked.current) return;
        if (e.target.closest('[data-modal-overlay]')) return;
        const dx = e.changedTouches[0].screenX - touchStartX.current;
        const dy = e.changedTouches[0].screenY - touchStartY.current;

        // Only trigger slide if horizontal movement > vertical (prevents scroll hijacking)
        if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 60) {
            if (dx < 0) {
                // Swipe left → go to next panel
                if (activeView < 2) setActiveView(prev => prev + 1);
            } else if (dx > 0) {
                // Swipe right → go to previous panel
                if (activeView > 0) setActiveView(prev => prev - 1);
            }
        }
    };

    // Callback for child screens to lock/unlock swiping (e.g. when modal opens)
    const handleModalChange = (isOpen) => {
        swipeLocked.current = isOpen;
    };

    const slideToProfile = () => setActiveView(0);
    const slideToDashboard = () => setActiveView(1);
    const slideToCommunity = () => setActiveView(2);

    return (
        <div
            className="fixed inset-0 overflow-hidden"
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
        >
            {/* ─── Sliding Content Container ─── */}
            <div
                className="flex flex-row h-full"
                style={{
                    width: '300vw',
                    transform: `translateX(-${activeView * 100}vw)`,
                    transition: 'transform 0.5s cubic-bezier(0.32, 0.72, 0, 1)',
                    willChange: 'transform',
                }}
            >
                {/* LEFT PANEL: Profile */}
                <div className="shrink-0 w-screen h-full overflow-y-auto">
                    <UserProfile
                        onNavigate={onNavigate}
                        isInPager={true}
                        user={user}
                        setUser={setUser}
                        onModalChange={handleModalChange}
                    />
                </div>

                {/* CENTER PANEL: Dashboard */}
                <div className="shrink-0 w-screen h-full overflow-y-auto">
                    <DashboardScreen
                        onNavigate={onNavigate}
                        alerts={alerts}
                        onOpenModal={onOpenModal}
                        analystName={analystName}
                        user={user}
                        onSlideToCommunity={slideToCommunity}
                        activeView={activeView === 1 ? 0 : activeView === 2 ? 1 : -1}
                    />
                </div>

                {/* RIGHT PANEL: Community */}
                <div className="shrink-0 w-screen h-full overflow-y-auto">
                    <StudentCommunityScreen
                        onNavigate={onNavigate}
                        onSlideBack={slideToDashboard}
                    />
                </div>
            </div>

            {/* ─── PERSISTENT BOTTOM NAVIGATION (fixed overlay, always visible) ─── */}
            <div className="fixed bottom-0 left-0 right-0 z-40">
                <Navigation
                    onOpenModal={onOpenModal}
                    onNavigateCommunity={slideToCommunity}
                    onNavigateHome={slideToDashboard}
                    onNavigateProfile={slideToProfile}
                    isCommunityActive={activeView === 2}
                    activeTab={activeView} // 0=Profile, 1=Home, 2=Community
                />
            </div>
        </div>
    );
}
