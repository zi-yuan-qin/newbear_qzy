import { useLayoutEffect, useMemo, useRef } from "react";
import type { CSSProperties } from "react";
import type { ActorState, WorldState } from "../types/api";

const MAP_IMAGE_SRC = "/assets/map_slices/map_layer_001_-1.png";
const SPEECH_BUBBLE_WIDTH = 170;
const ACTOR_MOVE_DURATION_MS = 5000;
const ACTOR_FRAME_INTERVAL_MS = 130;

const ACTOR_COLORS: Record<string, string> = {
  xionglaoban: "#6f4a2f",
  xiongjishu: "#3f5568",
  xiongshichang: "#4f7d4f",
  xiongxingzheng: "#9a6a45",
};

const ACTOR_ASSETS: Record<
  string,
  { idleFront: string; idleBack: string; walkFront: string[]; walkBack: string[] }
> = {
  xionglaoban: buildActorAsset("xionglaoban"),
  xiongjishu: buildActorAsset("xiongjishu"),
  xiongshichang: buildActorAsset("xiongshichang"),
  xiongxingzheng: buildActorAsset("xiongxingzheng"),
};

type ActorMovement = {
  fromLocation?: string;
  movementKey?: string;
  toLocation?: string;
};

type WorldMapProps = {
  activeSpeechActor: ActorState | null;
  actors: ActorState[];
  latestMovementByActorId: Map<string, ActorMovement>;
  selectedActorId: string | null;
  world: WorldState | null;
  onSelectActor: (actorId: string) => void;
};

type ActorMarkerProps = {
  actor: ActorState;
  color: string;
  formation: { x: number; y: number };
  fromLeft?: number;
  fromTop?: number;
  index: number;
  isSelected: boolean;
  left: number;
  movementKey?: string;
  top: number;
  onSelect: () => void;
};

function buildWalkFrames(actorId: string, direction: "front" | "back") {
  return Array.from(
    { length: 6 },
    (_, index) => `/assets/actors/${actorId}/walk_${direction}_${index + 1}.webp`,
  );
}

function buildActorAsset(actorId: string) {
  return {
    idleFront: `/assets/actors/${actorId}/idle_front.webp`,
    idleBack: `/assets/actors/${actorId}/idle_back.webp`,
    walkFront: buildWalkFrames(actorId, "front"),
    walkBack: buildWalkFrames(actorId, "back"),
  };
}

function easeInOut(progress: number) {
  return progress < 0.5
    ? 2 * progress * progress
    : 1 - Math.pow(-2 * progress + 2, 2) / 2;
}

function getMoveDirection(deltaLeft: number, deltaTop: number) {
  if (Math.abs(deltaLeft) > Math.abs(deltaTop)) {
    return deltaLeft < 0 ? "left" : "right";
  }

  return deltaTop < 0 ? "back" : "front";
}

function getActorFrame(actorId: string, direction: string, isWalking: boolean, frame: number) {
  const asset = ACTOR_ASSETS[actorId] || ACTOR_ASSETS.xionglaoban;
  const isBack = direction === "back";
  const frames = isBack ? asset.walkBack : asset.walkFront;

  if (isWalking && frames.length) {
    return frames[frame % frames.length];
  }

  return isBack ? asset.idleBack || asset.idleFront : asset.idleFront;
}

function getActorFormationOffset(index: number, total: number) {
  if (total <= 1) {
    return { x: 0, y: 0 };
  }

  const spacingX = 38;
  const spacingY = 10;
  const center = (total - 1) / 2;

  return {
    x: (index - center) * spacingX,
    y: (index % 2 === 0 ? -1 : 1) * spacingY,
  };
}

function getSpeechFormationOffset(index: number, total: number, anchorLeft: number) {
  const center = (total - 1) / 2;
  const row = index % 2;
  let edgeShift = 0;

  if (anchorLeft < 24) {
    edgeShift = 78;
  } else if (anchorLeft > 76) {
    edgeShift = -78;
  }

  return {
    x: edgeShift + (index - center) * SPEECH_BUBBLE_WIDTH,
    y: -88 - row * 70,
  };
}

function getSpeechBubblePosition(left: number, top: number, index: number, total: number) {
  const offset = getSpeechFormationOffset(index, total, left);

  if (top < 28) {
    return {
      ...offset,
      y: 72 + (index % 2) * 54,
      placement: "below",
    };
  }

  return {
    ...offset,
    placement: "above",
  };
}

function ActorMarker({
  actor,
  color,
  formation,
  fromLeft,
  fromTop,
  index,
  isSelected,
  left,
  movementKey,
  top,
  onSelect,
}: ActorMarkerProps) {
  const previousTargetRef = useRef({ left, top });
  const lastMovementKeyRef = useRef<string | undefined>(undefined);
  const animationRef = useRef<number | null>(null);
  const nodeRef = useRef<HTMLButtonElement | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);

  useLayoutEffect(() => {
    const node = nodeRef.current;
    const image = imageRef.current;
    if (!node || !image) {
      return;
    }
    const actorNode = node;
    const actorImage = image;

    const hasExplicitFrom =
      movementKey !== lastMovementKeyRef.current &&
      Number.isFinite(fromLeft) &&
      Number.isFinite(fromTop);
    const from = hasExplicitFrom
      ? { left: Number(fromLeft), top: Number(fromTop) }
      : previousTargetRef.current;
    const to = { left, top };
    const deltaLeft = to.left - from.left;
    const deltaTop = to.top - from.top;
    lastMovementKeyRef.current = movementKey;

    if (Math.abs(deltaLeft) < 0.01 && Math.abs(deltaTop) < 0.01) {
      previousTargetRef.current = to;
      actorNode.style.left = `${to.left}%`;
      actorNode.style.top = `${to.top}%`;
      actorImage.src = getActorFrame(actor.actor_id, "front", false, 0);
      actorImage.style.transform = "scaleX(1)";
      actorNode.classList.remove("is-walking");
      return;
    }

    const nextDirection = getMoveDirection(deltaLeft, deltaTop);
    const startedAt = window.performance.now();
    actorNode.style.left = `${from.left}%`;
    actorNode.style.top = `${from.top}%`;
    actorNode.classList.add("is-walking");

    function tick(now: number) {
      const progress = Math.min(1, (now - startedAt) / ACTOR_MOVE_DURATION_MS);
      const eased = easeInOut(progress);
      const currentLeft = from.left + deltaLeft * eased;
      const currentTop = from.top + deltaTop * eased;
      const frameIndex = Math.floor((now - startedAt) / ACTOR_FRAME_INTERVAL_MS);

      actorNode.style.left = `${currentLeft}%`;
      actorNode.style.top = `${currentTop}%`;
      actorImage.src = getActorFrame(actor.actor_id, nextDirection, true, frameIndex);
      actorImage.style.transform = nextDirection === "left" ? "scaleX(-1)" : "scaleX(1)";

      if (progress < 1) {
        animationRef.current = window.requestAnimationFrame(tick);
        return;
      }

      previousTargetRef.current = to;
      actorNode.style.left = `${to.left}%`;
      actorNode.style.top = `${to.top}%`;
      actorImage.src = getActorFrame(actor.actor_id, nextDirection, false, 0);
      actorImage.style.transform = nextDirection === "left" ? "scaleX(-1)" : "scaleX(1)";
      actorNode.classList.remove("is-walking");
    }

    if (animationRef.current) {
      window.cancelAnimationFrame(animationRef.current);
    }
    animationRef.current = window.requestAnimationFrame(tick);

    return () => {
      if (animationRef.current) {
        window.cancelAnimationFrame(animationRef.current);
      }
    };
  }, [actor.actor_id, fromLeft, fromTop, left, movementKey, top]);

  return (
    <button
      className={`actor-marker ${isSelected ? "is-selected" : ""}`}
      ref={nodeRef}
      style={{
        left: `${left}%`,
        top: `${top}%`,
        zIndex: 10 + index,
        "--actor-offset-x": `${formation.x}px`,
        "--actor-offset-y": `${formation.y}px`,
      } as CSSProperties}
      type="button"
      onClick={onSelect}
      title={`${actor.display_name} · ${actor.location}`}
    >
      <div className="floor-actor-body">
        <div className="floor-actor-shadow" />
        <img
          className="floor-actor-image"
          ref={imageRef}
          src={getActorFrame(actor.actor_id, "front", false, 0)}
          alt={actor.display_name}
        />
        <div className="floor-actor-label" style={{ color, borderColor: color }}>
          {actor.display_name}
        </div>
      </div>
    </button>
  );
}

export function WorldMap({
  activeSpeechActor,
  actors,
  latestMovementByActorId,
  selectedActorId,
  world,
  onSelectActor,
}: WorldMapProps) {
  const mapLocations = world?.map?.semantics?.locations ?? [];
  const locationByName = useMemo(
    () => new Map(mapLocations.map((location) => [location.name, location])),
    [mapLocations],
  );
  const actorsByLocation = new Map<string, ActorState[]>();

  for (const actor of actors) {
    const group = actorsByLocation.get(actor.location) ?? [];
    group.push(actor);
    actorsByLocation.set(actor.location, group);
  }

  return (
    <section className="scene-panel">
      <div className="world-map">
        <img className="world-map-image" src={MAP_IMAGE_SRC} alt="公司地图" />

        <div className="speech-layer">
          {activeSpeechActor ? (() => {
            const actor = activeSpeechActor;
            const location = locationByName.get(actor.location);

            if (!location?.anchor_x || !location?.anchor_y) {
              return null;
            }

            const pixelWidth = world?.map?.world?.pixel_width || 1;
            const pixelHeight = world?.map?.world?.pixel_height || 1;
            const left = (location.anchor_x / pixelWidth) * 100;
            const top = (location.anchor_y / pixelHeight) * 100;
            const color = ACTOR_COLORS[actor.actor_id] || "#18212f";
            const group = actorsByLocation.get(actor.location) ?? [];
            const actorIndex = group.findIndex((item) => item.actor_id === actor.actor_id);
            const speechPosition = getSpeechBubblePosition(
              left,
              top,
              actorIndex,
              group.length,
            );

            return (
              <div
                className={`floor-speech ${
                  speechPosition.placement === "below" ? "is-below" : ""
                }`}
                key={`${actor.actor_id}-speech`}
                style={{
                  "--speech-anchor-x": `${left}%`,
                  "--speech-anchor-y": `${top}%`,
                  zIndex: 40,
                  borderColor: color,
                  "--speech-offset-x": `${speechPosition.x}px`,
                  "--speech-offset-y": `${speechPosition.y}px`,
                } as CSSProperties}
              >
                <strong style={{ color }}>{actor.display_name}</strong>
                <span>{actor.last_speech}</span>
              </div>
            );
          })() : null}
        </div>

        <div className="actor-layer">
          {actors.map((actor, index) => {
            const location = locationByName.get(actor.location);

            if (!location?.anchor_x || !location?.anchor_y) {
              return null;
            }

            const pixelWidth = world?.map?.world?.pixel_width || 1;
            const pixelHeight = world?.map?.world?.pixel_height || 1;
            const left = (location.anchor_x / pixelWidth) * 100;
            const top = (location.anchor_y / pixelHeight) * 100;
            const color = ACTOR_COLORS[actor.actor_id] || "#18212f";
            const group = actorsByLocation.get(actor.location) ?? [];
            const actorIndex = group.findIndex((item) => item.actor_id === actor.actor_id);
            const formation = getActorFormationOffset(actorIndex, group.length);
            const latestMovement = latestMovementByActorId.get(actor.actor_id);
            const fromLocation =
              latestMovement?.fromLocation && latestMovement.fromLocation !== latestMovement.toLocation
                ? locationByName.get(latestMovement.fromLocation)
                : undefined;
            const fromLeft =
              fromLocation?.anchor_x !== undefined
                ? (fromLocation.anchor_x / pixelWidth) * 100
                : undefined;
            const fromTop =
              fromLocation?.anchor_y !== undefined
                ? (fromLocation.anchor_y / pixelHeight) * 100
                : undefined;

            return (
              <ActorMarker
                actor={actor}
                color={color}
                formation={formation}
                fromLeft={fromLeft}
                fromTop={fromTop}
                index={index}
                isSelected={selectedActorId === actor.actor_id}
                key={actor.actor_id}
                left={left}
                movementKey={latestMovement?.movementKey}
                top={top}
                onSelect={() => onSelectActor(actor.actor_id)}
              />
            );
          })}
        </div>
      </div>
    </section>
  );
}
