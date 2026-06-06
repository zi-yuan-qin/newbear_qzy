export type AuthUser = {
  user_id: number;
  username: string;
  session_id: string;
};

export type AuthMeResponse =
  | {
      authenticated: true;
      user: AuthUser;
    }
  | {
      authenticated: false;
    };

export type AuthPayload = {
  username: string;
  password: string;
};

export type CompanyState = {
  name?: string;
  cash?: number;
  day?: number;
  step?: number;
  clock?: string;
  phase?: string;
  logs?: CompanyLog[];
};

export type ActorState = {
  actor_id: string;
  display_name: string;
  location: string;
  stress?: number;
  energy?: number;
  mood?: string;
  current_task?: string;
  intent?: string;
  move_to?: string;
  last_speech?: string;
  memory?: string[];
  memory_stream?: MemoryRecord[];
  reflection_importance_buffer?: number;
};

export type MemoryRecord = {
  memory_id?: number;
  kind?: string;
  text?: string;
  clock?: string;
  importance?: number;
  tags?: string[];
  related_actor_ids?: string[];
};
export type ActorReaction = {
  actor_id?: string;
  display_name?: string;
  from_location?: string;
  location?: string;
  to_location?: string;
  move_to?: string;
  task?: string;
  intent?: string;
  speech?: string;
  stress?: number;
  energy?: number;
};

export type CompanyLog = {
  step: number;
  from_clock?: string;
  to_clock?: string;
  affair?: string;
  actor_reactions?: ActorReaction[];
  encounters?: EncounterRecord[];
};

export type EncounterRecord = {
  location?: string;
  summary?: string;
  actor_ids?: string[];
  actor_names?: string[];
  display_names?: string[];
  dialogue?: DialogueLine[];
};

export type DialogueLine = {
  actor_id?: string;
  to_actor_id?: string;
  speech?: string;
};

export type InputRecord = {
  input_id?: string;
  step?: number;
  clock?: string;
  raw_text?: string;
  is_empty?: boolean;
  actor_reactions?: ActorReaction[];
};

export type IncidentRecord = {
  incident_id?: string;
  id?: string;
  time?: string;
  clock?: string;
  title?: string;
  content?: string;
  visible?: boolean;
};

export type MeetingLine = {
  actor_id?: string;
  display_name?: string;
  speaker?: string;
  speech?: string;
  text?: string;
  content?: string;
  role?: "user" | "assistant" | string;
  kind?: string;
};

export type MeetingState = {
  meeting_id: string;
  time?: string;
  title?: string;
  content?: string;
  participants?: string[];
  day?: number;
  step?: number;
  clock?: string;
  phase?: string;
  duration_seconds?: number;
  remaining_seconds?: number;
  transcript?: MeetingLine[];
  result?: string | Record<string, unknown>;
};

export type MeetingEvent = {
  meeting_id?: string;
  time?: string;
  title?: string;
  content?: string;
  participants?: string[];
  day?: number;
  step?: number;
  clock?: string;
};

export type PantryLine = {
  actor_id?: string;
  display_name?: string;
  speaker?: string;
  speech?: string;
  text?: string;
  content?: string;
  role?: "user" | "assistant" | string;
  kind?: string;
};

export type PantryState = {
  pantry_id?: string;
  title?: string;
  content?: string;
  participants?: string[];
  transcript?: PantryLine[];
  user_message?: string;
  phase?: string;
};

export type ReportRadarItem = {
  code?: string;
  label?: string;
  value?: number;
};

export type ReportState = {
  visible?: boolean;
  report_id?: string;
  clock?: string;
  time?: string;
  letter_title?: string;
  letter_body?: string;
  trait_summary?: string;
  evidence?: string[];
  radar_items?: ReportRadarItem[];
  scores?: Record<string, number>;
};

export type OnboardingCharacter = {
  actor_id: string;
  display_name?: string;
  role?: string;
  job_title?: string;
  work_title?: string;
  role_name?: string;
  company_lens?: string;
  kpi?: string;
  speaking_style?: string;
  core_drives?: string[];
  personality?: Record<string, unknown>;
  work?: Record<string, unknown>;
  relationships?: Record<string, unknown>;
};

export type OnboardingState = {
  company?: {
    name?: string;
    business?: string;
    stage?: string;
    team_state?: string;
    external_pressure?: string;
    working_style?: string;
    short_term_goals?: string[];
  };
  characters?: OnboardingCharacter[];
};

export type MapLocation = {
  location_id: string;
  name: string;
  function?: string;
  can_move_to?: boolean;
  aliases?: string[];
  contains?: string[];
  anchor_x?: number;
  anchor_y?: number;
};

export type MapState = {
  world?: {
    pixel_width?: number;
    pixel_height?: number;
  };
  semantics?: {
    locations?: MapLocation[];
  };
};

export type WorldState = {
  seed?: {
    seed_id?: string;
    summary?: Record<string, unknown>;
    incident_pool_ids?: string[];
    meeting_topic_ids?: string[];
    pantry_topic_ids?: string[];
    report_template_ids?: string[];
    session_record_id?: string;
  };
  company?: CompanyState;
  actors?: ActorState[];
  map?: MapState;
  user_inputs?: InputRecord[];
  pending_incident?: IncidentRecord | null;
  incidents?: IncidentRecord[];
  active_meeting?: MeetingState | null;
  meetings?: MeetingEvent[];
  active_pantry?: PantryState | null;
  active_report?: ReportState | null;
  onboarding?: OnboardingState;
};

export type AuthSuccessResponse = {
  ok: true;
  user: AuthUser;
  state: WorldState;
};

export type ApiErrorResponse = {
  error: string;
};
export type StateResponse = {
  state: WorldState;
};

export type StepPayload = {
  affair: string;
};

export type StepResponse = {
  ok: true;
  state: WorldState;
};

export type ResetResponse = {
  ok: true;
  state: WorldState;
};
