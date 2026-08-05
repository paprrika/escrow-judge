// EscrowArbiter — deployed on GenLayer Studionet.
// Public config; values come from the committed .env (see .env.example) with
// the deployed fallbacks below so a build without an env file stays correct.
export const CONTRACT_ADDRESS = (import.meta.env.VITE_CONTRACT_ADDRESS ??
  "0xc5B38B28d662A0d68bDEF7114f50719403fAceec") as `0x${string}`;

export const NETWORK = "studionet" as const;
export const CHAIN_ID = Number(import.meta.env.VITE_CHAIN_ID ?? 61999);
export const RPC_URL =
  import.meta.env.VITE_RPC_URL ?? "https://studio.genlayer.com/api";
export const EXPLORER_TX = "https://studio.genlayer.com/";
