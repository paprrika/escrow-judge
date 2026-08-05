# Stone & Scales

Multi-party milestone escrow with on-chain arbitration on [GenLayer](https://genlayer.com): a buyer funds a deal, milestone tranches release as the right roles sign off, and a contested tranche is settled by a validator jury rather than a server.

## How it works

1. Fund: a buyer opens a deal against a seller and escrows the full amount. The milestones document is fetched live and its sha256 is anchored on-chain.
2. Declare: the seller breaks the work into milestones, each carrying a basis-point share of the escrow — the tranches that release one at a time.
3. Witness and release: an optional witness attests a milestone is done, a validator-run model checks the notes actually describe the deliverable, and the buyer releases that tranche as a native GEN transfer to the seller.
4. Dispute: if a milestone is contested, either side posts a tracked bond and the grievance is normalized into a short summary for the arbiters.
5. Arbitrate: the platform seats arbiters who each file a finding; a GenLayer jury weighs the findings and fetched evidence into BUYER_WINS, SELLER_WINS, or SPLIT.
6. Settle: the verdict transfers the seller share, refunds the buyer share, and returns the dispute bond to its opener. The deal then returns to in-progress or closes.

## Settlement guarantees

- Deal funding must equal the declared total exactly, so overfunding cannot become trapped.
- Every settled wei is classified as `released` to the seller, `refunded` to the buyer, or still `locked`.
- The last tranche receives integer-division dust, so a fully declared 10,000-bps deal closes with zero escrow left behind.
- Dispute records store their `deal_id`; findings and finalization reject a dispute id from any other deal.
- Finalization refunds the dispute bond, and voiding a deal refunds both remaining escrow and any live bond.
- `platform_summary` exposes escrow and bond liabilities alongside the contract balance.

## Architecture

```
backend/escrow-judge.py   GenLayer Intelligent Contract (Python, runs on the GenVM)
frontend/                 React + Vite + TypeScript console (genlayer-js)
```

A single basis-point split drives both the jury verdict and the on-chain release, so validators settle a contested tranche cleanly when they agree on a label and land within a tolerance band.

## Live deployment

- **Network**: GenLayer Studionet (chain id 61999)
- **Contract**: `0xc5B38B28d662A0d68bDEF7114f50719403fAceec`
- **Deployment transaction**: `0x4e25ff9e5ef5ea9cbdb4f8f35bb47d9d004bb36e293ff6d832c123e04ebc6232`
- **App**: https://paprrika.github.io/escrow-judge/
## Run locally

```bash
cd frontend
npm install
npm run dev
npm run build
```

Contract checks:

```bash
pip install -r requirements-dev.txt
genvm-lint check backend/escrow-judge.py
pytest tests/direct -v
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
| `release_milestone` | write | Buyer releases a requested tranche via a native GEN transfer to the seller. |
| `assign_arbiter` | write | Platform seats an arbiter on a disputed deal. |
| `file_arbiter_finding` | write | Arbiter records which way they lean and why. |
| `finalize_dispute` | write | Jury synthesizes a verdict, pays/refunds the tranche split, and refunds the bond. |
| `void_deal` | write | Platform voids a stalled deal and refunds its remaining escrow and live bond. |
| `deal` | view | Full deal record by id. |
| `milestones_of` | view | All milestones declared on a deal. |
| `role_of` | view | An address's role on a given deal. |
| `participants` | view | Buyer, seller, witness, and platform addresses for a deal. |
| `dispute` | view | Full dispute record by id. |
| `tranche_state` | view | Computed tranche value and release flags for a milestone. |
| `platform_summary` | view | Platform address, deal and dispute totals, and phase counts. |

## License

MIT
