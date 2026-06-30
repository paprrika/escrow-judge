// Types mirroring the EscrowArbiter contract surface.

export type Hex = `0x${string}`;

// The 9 lifecycle phases, in canonical order (matches PHASES_ALL on-chain).
export const PHASES = [
  "AWAITING_FUND",
  "FUNDED",
  "IN_PROGRESS",
  "MILESTONE_REVIEW",
  "DISPUTED",
  "ARBITRATING",
  "SETTLING",
  "CLOSED",
  "VOID",
] as const;
export type Phase = (typeof PHASES)[number] | "UNKNOWN";

export const ROLE_NAMES = [
  "NONE",
  "BUYER",
  "SELLER",
  "WITNESS",
  "ARBITER",
  "PLATFORM",
] as const;
export type RoleName = (typeof ROLE_NAMES)[number];

export const VERDICTS = ["BUYER_WINS", "SELLER_WINS", "SPLIT", ""] as const;
export type Verdict = (typeof VERDICTS)[number];

export interface DealView {
  deal_id: string;
  exists: boolean;
  buyer: string;
  seller: string;
  witness: string;
  witness_required: boolean;
  milestones_uri: string;
  milestones_doc_sha256: string;
  total: number;
  funded: number;
  released: number;
  phase: Phase;
  opened_at_seq: number;
}

export interface MilestoneView {
  idx: number;
  description: string;
  share_bps: number;
  declared: boolean;
  witnessed_ok: boolean;
  requested_release: boolean;
  released: boolean;
  coherence_rationale: string;
}

export interface ParticipantsView {
  buyer?: string;
  seller?: string;
  witness?: string;
  platform?: string;
}

export interface DisputeView {
  dispute_id: string;
  exists: boolean;
  deal_id: string;
  milestone_idx: number;
  opener: string;
  ground: string;
  ground_summary: string;
  evidence_uri: string;
  opened_at_seq: number;
  finalized_at_seq: number;
  final_verdict: Verdict;
  final_split_bps: number;
}

export interface PlatformSummary {
  platform: string;
  deals_total: number;
  disputes_total: number;
  phase_counts: Record<string, number>;
}

// A locally-tracked deal (the contract has no enumeration view, deal_ids are
// sha256 hashes returned at creation; we persist the ones the user touches).
export interface TrackedDeal {
  id: string;
  label: string;
  addedAt: number;
  disputeIds: string[];
}
