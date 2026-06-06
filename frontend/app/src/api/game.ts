import { apiRequest } from "./client";
import type {
  ResetResponse,
  StateResponse,
  StepPayload,
  StepResponse,
} from "../types/api";

export function fetchWorldState() {
  return apiRequest<StateResponse>("/api/state");
}

export function runStep(payload: StepPayload) {
  return apiRequest<StepResponse>("/api/step", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function resetWorld() {
  return apiRequest<ResetResponse>("/api/reset", {
    method: "POST",
  });
}
export function enterMeeting() {
  return apiRequest<StepResponse>("/api/meeting/enter", {
    method: "POST",
  });
}

export function startMeeting() {
  return apiRequest<StepResponse>("/api/meeting/start", {
    method: "POST",
  });
}

export function sendMeetingMessage(message: string) {
  return apiRequest<StepResponse>("/api/meeting/say", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function tickMeeting() {
  return apiRequest<StepResponse>("/api/meeting/tick", {
    method: "POST",
  });
}

export function finishMeeting() {
  return apiRequest<StepResponse>("/api/meeting/finish", {
    method: "POST",
  });
}

export function closeMeeting() {
  return apiRequest<StepResponse>("/api/meeting/close", {
    method: "POST",
  });
}

export function sendPantryMessage(message: string) {
  return apiRequest<StepResponse>("/api/pantry/say", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function tickPantry() {
  return apiRequest<StepResponse>("/api/pantry/tick", {
    method: "POST",
  });
}

export function leavePantry() {
  return apiRequest<StepResponse>("/api/pantry/leave", {
    method: "POST",
  });
}

export function closeReport() {
  return apiRequest<StepResponse>("/api/report/close", {
    method: "POST",
  });
}