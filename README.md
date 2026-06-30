# Stone & Scales

Multi-party milestone escrow with on-chain arbitration on [GenLayer](https://genlayer.com): a buyer funds a deal, milestone tranches release as the right roles sign off, and a contested tranche is settled by a validator jury rather than a server.

## How it works

1. Fund: a buyer opens a deal against a seller and escrows the full amount. The milestones document is fetched live and its sha256 is anchored on-chain.
2. Declare: the seller breaks the work into milestones, each carrying a basis-point share of the escrow — the tranches that release one at a time.
3. Witness and release: an optional witness attests a milestone is done, a validator-run model checks the notes actually describe the deliverable, and the buyer releases that tranche.
4. Dispute: if a milestone is contested, either side posts a bonded dispute and the grievance is normalized into a short summary for the arbiters.
5. Arbitrate: the platform seats arbiters who each file a finding; a GenLayer jury weighs the findings and fetched evidence into BUYER_WINS, SELLER_WINS, or SPLIT.
6. Settle: the verdict sets the exact share of the contested tranche that passes to the seller, and the deal returns to in-progress or closes.

## Architecture

```
backend/escrow-judge.py   GenLayer Intelligent Contract (Python, runs on the GenVM)
frontend/                 React + Vite + TypeScript console (genlayer-js)
```

A single basis-point split drives both the jury verdict and the on-chain release, so validators settle a contested tranche cleanly when they agree on a label and land within a tolerance band.

## Live deployment

- **Network**: GenLayer Studionet (chain id 61999)
- **Contract**: `0x52A5839F38e2D9a234ad95Ee11A306CA1A2cd841`
- **App**: https://paprrika.github.io/escrow-judge/
## Run locally

```bash
cd frontend
npm install
npm run dev
npm run build
```

The committed `.env` holds the public Studionet config; no secrets are required. Copy `.env.example` to `.env.local` only to override.

## Environment variables

| Name | Required | Description |
|------|----------|-------------|
| `VITE_CONTRACT_ADDRESS` | yes | Deployed EscrowArbiter contract on Studionet |
| `VITE_CHAIN_ID` | yes | GenLayer chain id (61999) |
| `VITE_RPC_URL` | yes | Studionet JSON-RPC endpoint |

## Deploy the contract

```bash
npx genlayer deploy --contract backend/escrow-judge.py
```

## Contract methods (`EscrowArbiter`)

| Method | Type | Description |
|--------|------|-------------|
| `open_deal` | payable | Buyer funds a deal against a seller; fetches the milestones doc and anchors its sha256. |
| `open_dispute` | payable | Either party posts a bond to contest a milestone; the grievance is summarized for arbiters. |
| `accept_deal` | write | Seller accepts a funded deal and moves it to in-progress. |
| `add_witness` | write | Buyer registers an optional witness address and binds the witness role. |
| `declare_milestone` | write | Seller declares a tranche with its basis-point share of the escrow. |
| `attest_milestone` | write | Witness attests a milestone; a validator model checks the notes match the deliverable. |
| `request_release` | write | Seller requests release of a completed tranche, moving the deal to review. |
| `release_milestone` | write | Buyer releases a requested tranche to the seller. |
| `assign_arbiter` | write | Platform seats an arbiter on a disputed deal. |
| `file_arbiter_finding` | write | Arbiter records which way they lean and why. |
| `finalize_dispute` | write | Jury synthesizes findings and fetched evidence into a verdict and split. |
| `void_deal` | write | Platform voids a stalled, non-terminal deal. |
| `deal` | view | Full deal record by id. |
| `milestones_of` | view | All milestones declared on a deal. |
| `role_of` | view | An address's role on a given deal. |
| `participants` | view | Buyer, seller, witness, and platform addresses for a deal. |
| `dispute` | view | Full dispute record by id. |
| `tranche_state` | view | Computed tranche value and release flags for a milestone. |
| `platform_summary` | view | Platform address, deal and dispute totals, and phase counts. |

## License

MIT
