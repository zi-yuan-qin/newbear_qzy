import { useEffect, useMemo, useRef, useState } from "react";
import type { SyntheticEvent } from "react";
import { ActionPanel } from "./components/ActionPanel";
import { AuthPanel, type AuthMode } from "./components/AuthPanel";
import { IncidentOverlay } from "./components/IncidentOverlay";
import { MeetingPanel } from "./components/MeetingPanel";
import { OnboardingOverlay } from "./components/OnboardingOverlay";
import { PantryPanel } from "./components/PantryPanel";
import { ReportOverlay } from "./components/ReportOverlay";
import { WorldMap } from "./components/WorldMap";
import { useGameStore } from "./store/gameStore";
import "./styles/global.css";

const SPEECH_ROTATE_MS = 5000;
const AUTO_STEP_DELAY_MS = 900;
const ONBOARDING_STORAGE_KEY = "newbear_onboarding_seen_v1";

function onboardingStorageKey(username: string | undefined) {
  return `${ONBOARDING_STORAGE_KEY}:${username || "guest"}`;
}

function App() {
  const user = useGameStore((state) => state.user);
  const world = useGameStore((state) => state.world);
  const status = useGameStore((state) => state.status);
  const isSubmitting = useGameStore((state) => state.isSubmitting);
  const isBusy = useGameStore((state) => state.isBusy);
  const runStep = useGameStore((state) => state.runStep);
  const resetWorld = useGameStore((state) => state.resetWorld);
  const startMeeting = useGameStore((state) => state.startMeeting);
  const sendMeetingMessage = useGameStore((state) => state.sendMeetingMessage);
  const tickMeeting = useGameStore((state) => state.tickMeeting);
  const finishMeeting = useGameStore((state) => state.finishMeeting);
  const closeMeeting = useGameStore((state) => state.closeMeeting);
  const sendPantryMessage = useGameStore((state) => state.sendPantryMessage);
  const tickPantry = useGameStore((state) => state.tickPantry);
  const leavePantry = useGameStore((state) => state.leavePantry);
  const closeReport = useGameStore((state) => state.closeReport);
  const checkAuth = useGameStore((state) => state.checkAuth);
  const login = useGameStore((state) => state.login);
  const register = useGameStore((state) => state.register);
  const logout = useGameStore((state) => state.logout);

  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [username, setUsername] = useState("test01");
  const [password, setPassword] = useState("123456");
  const [affair, setAffair] = useState("");
  const [selectedActorId, setSelectedActorId] = useState<string | null>(null);
  const [dismissedIncidentId, setDismissedIncidentId] = useState<string | null>(null);
  const [isAutoStepEnabled, setIsAutoStepEnabled] = useState(false);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const [onboardingPrewarmed, setOnboardingPrewarmed] = useState(false);
  const [activeSpeechIndex, setActiveSpeechIndex] = useState(0);
  const bgmRef = useRef<HTMLAudioElement | null>(null);

  const actors = world?.actors ?? [];
  const selectedActor = actors.find((actor) => actor.actor_id === selectedActorId) ?? null;
  const speakingActors = actors.filter((actor) => actor.last_speech?.trim());
  const activeSpeechActor =
    activeSpeechIndex >= 0 && activeSpeechIndex < speakingActors.length
      ? speakingActors[activeSpeechIndex % speakingActors.length]
      : null;
  const speechQueueKey = speakingActors
    .map((actor) => `${actor.actor_id}:${actor.last_speech}`)
    .join("|");
  const incidentId =
    world?.pending_incident?.incident_id || world?.pending_incident?.id || null;
  const visibleIncident =
    incidentId && incidentId !== dismissedIncidentId ? world?.pending_incident : null;
  const isSpeechSequenceDone =
    speakingActors.length === 0 || activeSpeechIndex >= speakingActors.length - 1;
  const latestInputRecord =
    world?.user_inputs && world.user_inputs.length > 0
      ? world.user_inputs[world.user_inputs.length - 1]
      : undefined;
  const userOnboardingKey = onboardingStorageKey(user?.username);
  const isWorldStepAvailable = Boolean(
    world &&
      !world.active_meeting &&
      !world.active_pantry &&
      !world.active_report?.visible &&
      !visibleIncident &&
      !isOnboardingOpen,
  );
  const latestMovementByActorId = useMemo(() => {
    const movementMap = new Map<
      string,
      { fromLocation?: string; movementKey: string; toLocation?: string }
    >();

    for (const reaction of latestInputRecord?.actor_reactions ?? []) {
      const actorId = String(reaction.actor_id || "");
      if (!actorId) {
        continue;
      }

      const fromLocation = reaction.from_location || reaction.location;
      const toLocation = reaction.to_location || reaction.move_to;
      movementMap.set(actorId, {
        fromLocation,
        toLocation,
        movementKey: `${latestInputRecord?.input_id ?? latestInputRecord?.step ?? ""}:${actorId}:${fromLocation ?? ""}->${toLocation ?? ""}`,
      });
    }

    return movementMap;
  }, [latestInputRecord]);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (!world?.onboarding || !user || world.company?.day !== 1) {
      setIsOnboardingOpen(false);
      return;
    }

    setIsOnboardingOpen(window.localStorage.getItem(userOnboardingKey) !== "1");
  }, [user, userOnboardingKey, world?.company?.day, world?.onboarding]);

  useEffect(() => {
    if (!isOnboardingOpen || onboardingPrewarmed || isBusy) {
      return;
    }

    if (world?.company?.day !== 1 || world.company?.step !== 0) {
      return;
    }

    const timer = window.setTimeout(() => {
      setOnboardingPrewarmed(true);
      runStep("");
    }, 120);

    return () => window.clearTimeout(timer);
  }, [
    isBusy,
    isOnboardingOpen,
    onboardingPrewarmed,
    runStep,
    world?.company?.day,
    world?.company?.step,
  ]);

  useEffect(() => {
    if (!isAutoStepEnabled || isBusy || !isWorldStepAvailable || !isSpeechSequenceDone) {
      return;
    }

    const timer = window.setTimeout(() => {
      runStep(affair);
      setAffair("");
    }, AUTO_STEP_DELAY_MS);

    return () => window.clearTimeout(timer);
  }, [
    affair,
    isAutoStepEnabled,
    isBusy,
    isSpeechSequenceDone,
    isWorldStepAvailable,
    runStep,
    world?.company?.clock,
  ]);

  useEffect(() => {
    if (!user || !bgmRef.current) {
      return;
    }

    bgmRef.current.volume = 0.35;
    bgmRef.current.play().catch(() => {
      // Browsers require a user gesture before autoplay; the next click will retry.
    });
  }, [user]);

  useEffect(() => {
    function retryMusic() {
      if (!user || !bgmRef.current) {
        return;
      }
      bgmRef.current.volume = 0.35;
      bgmRef.current.play().catch(() => undefined);
    }

    window.addEventListener("pointerdown", retryMusic);
    return () => window.removeEventListener("pointerdown", retryMusic);
  }, [user]);

  useEffect(() => {
    if (incidentId && incidentId !== dismissedIncidentId) {
      return;
    }

    if (!incidentId) {
      setDismissedIncidentId(null);
    }
  }, [dismissedIncidentId, incidentId]);

  useEffect(() => {
    setActiveSpeechIndex(speakingActors.length > 0 ? 0 : -1);
  }, [speechQueueKey, speakingActors.length]);

  useEffect(() => {
    if (
      activeSpeechIndex < 0 ||
      speakingActors.length === 0 ||
      activeSpeechIndex >= speakingActors.length - 1
    ) {
      return;
    }

    const timer = window.setTimeout(() => {
      setActiveSpeechIndex((current) => Math.min(current + 1, speakingActors.length - 1));
    }, SPEECH_ROTATE_MS);

    return () => window.clearTimeout(timer);
  }, [activeSpeechIndex, speakingActors.length, speechQueueKey]);

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!username.trim() || !password.trim()) {
      return;
    }

    if (authMode === "login") {
      await login({ username, password });
    } else {
      await register({ username, password });
    }
  }

  async function handleLogout() {
    await logout();
  }

  async function handleRunStep() {
    await runStep(affair);
    setAffair("");
  }

  async function handleResetWorld() {
    setIsAutoStepEnabled(false);
    setOnboardingPrewarmed(false);
    window.localStorage.removeItem(userOnboardingKey);
    await resetWorld();
  }

  function handleCloseOnboarding() {
    window.localStorage.setItem(userOnboardingKey, "1");
    setIsOnboardingOpen(false);
  }

  if (!user) {
    return (
      <main className="app-shell">
        <audio ref={bgmRef} src="/assets/bgm.mp3" loop preload="auto" />
        <AuthPanel
          authMode={authMode}
          isSubmitting={isSubmitting}
          password={password}
          status={status}
          username={username}
          onAuthModeChange={setAuthMode}
          onPasswordChange={setPassword}
          onSubmit={handleSubmit}
          onUsernameChange={setUsername}
        />
      </main>
    );
  }

  if (world?.active_meeting) {
    return (
      <main className="app-shell">
        <audio ref={bgmRef} src="/assets/bgm.mp3" loop preload="auto" />
        <section className="mobile-frame">
          <header className="app-header">
            <div>
              <p className="app-kicker">{world.company?.name || "熊心壮职"}</p>
              <h1>会议室</h1>
            </div>
          </header>

          <MeetingPanel
            meeting={world.active_meeting}
            isBusy={isBusy}
            onClose={closeMeeting}
            onFinish={finishMeeting}
            onSend={sendMeetingMessage}
            onStart={startMeeting}
            onTick={tickMeeting}
          />

          <ReportOverlay report={world.active_report} onClose={closeReport} />
          <IncidentOverlay
            incident={visibleIncident}
            onClose={() => setDismissedIncidentId(incidentId)}
          />
        </section>
      </main>
    );
  }

  if (world?.active_pantry) {
    return (
      <main className="app-shell">
        <audio ref={bgmRef} src="/assets/bgm.mp3" loop preload="auto" />
        <section className="mobile-frame">
          <header className="app-header">
            <div>
              <p className="app-kicker">{world.company?.name || "熊心壮职"}</p>
              <h1>茶水间</h1>
            </div>
          </header>

          <PantryPanel
            pantry={world.active_pantry}
            isBusy={isBusy}
            onLeave={leavePantry}
            onSend={sendPantryMessage}
            onTick={tickPantry}
          />

          <ReportOverlay report={world.active_report} onClose={closeReport} />
          <IncidentOverlay
            incident={visibleIncident}
            onClose={() => setDismissedIncidentId(incidentId)}
          />
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <audio ref={bgmRef} src="/assets/bgm.mp3" loop preload="auto" />
      <section className="mobile-frame">
        <header className="app-header">
          <div>
            <p className="app-kicker">{world?.company?.name || "熊心壮职"}</p>
            <h1>入职第一天</h1>
          </div>
          <button className="icon-button" type="button" onClick={handleLogout}>
            退
          </button>
        </header>

        <WorldMap
          activeSpeechActor={activeSpeechActor}
          actors={actors}
          latestMovementByActorId={latestMovementByActorId}
          selectedActorId={selectedActorId}
          world={world}
          onSelectActor={setSelectedActorId}
        />

        <ActionPanel
          affair={affair}
          isAutoStepEnabled={isAutoStepEnabled}
          isBusy={isBusy}
          selectedActor={selectedActor}
          status={status}
          user={user}
          world={world}
          onAffairChange={setAffair}
          onAutoStepChange={setIsAutoStepEnabled}
          onCloseActor={() => setSelectedActorId(null)}
          onResetWorld={handleResetWorld}
          onRunStep={handleRunStep}
        />

        <ReportOverlay report={world?.active_report} onClose={closeReport} />
        <IncidentOverlay
          incident={visibleIncident}
          onClose={() => setDismissedIncidentId(incidentId)}
        />
        <OnboardingOverlay
          onboarding={world?.onboarding}
          open={isOnboardingOpen}
          onClose={handleCloseOnboarding}
        />
      </section>
    </main>
  );
}

export default App;
