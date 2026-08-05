import json


CONTRACT = "backend/escrow-judge.py"
MILESTONES_URL = "https://example.test/milestones.txt"


def _address(raw):
    from genlayer.py.types import Address

    return Address(raw) if isinstance(raw, bytes) else raw


def _capture_transfers(direct_vm):
    transfers = []

    def hook(_vm, request):
        if "EthSend" in request:
            transfers.append(request["EthSend"])
            return {"ok": None}
        return None

    direct_vm._gl_call_hook = hook
    return transfers


def _sent(transfers):
    return [(item["address"].as_bytes, int(item["value"])) for item in transfers]


def _open_deal(contract, vm, buyer, seller, total):
    vm.clear_mocks()
    vm.mock_web(
        r".*example\.test/milestones\.txt.*",
        {"status": 200, "body": "Milestone specification"},
    )
    vm.sender = buyer
    vm.value = total
    deal_id = contract.open_deal(_address(seller), MILESTONES_URL, total, False)
    vm.value = 0
    vm.clear_mocks()
    return deal_id


def _accept_and_declare(contract, vm, seller, deal_id, shares):
    vm.sender = seller
    contract.accept_deal(deal_id)
    for idx, share in enumerate(shares):
        contract.declare_milestone(deal_id, idx, f"Milestone {idx}", share)


def _open_dispute(contract, vm, opener, deal_id, idx, bond):
    vm.mock_llm(r".*Normalize a free-text dispute.*", json.dumps({"summary": "Delivery disputed"}))
    vm.sender = opener
    vm.value = bond
    dispute_id = contract.open_dispute(deal_id, idx, "The delivery does not match", "")
    vm.value = 0
    vm.clear_mocks()
    return dispute_id


def test_release_transfers_every_wei_and_closes_with_rounding_dust(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
):
    contract = direct_deploy(CONTRACT)
    transfers = _capture_transfers(direct_vm)
    deal_id = _open_deal(contract, direct_vm, direct_alice, direct_bob, 1001)
    _accept_and_declare(contract, direct_vm, direct_bob, deal_id, [5000, 5000])

    direct_vm.sender = direct_bob
    contract.request_release(deal_id, 0)
    direct_vm.sender = direct_alice
    assert contract.release_milestone(deal_id, 0) == 500

    direct_vm.sender = direct_bob
    contract.request_release(deal_id, 1)
    direct_vm.sender = direct_alice
    assert contract.release_milestone(deal_id, 1) == 501

    deal = contract.deal(deal_id)
    summary = contract.platform_summary()
    assert deal["phase"] == "CLOSED"
    assert deal["funded"] == deal["released"] + deal["refunded"] + deal["locked"]
    assert (deal["released"], deal["refunded"], deal["locked"]) == (1001, 0, 0)
    assert (summary["escrow_locked"], summary["seller_paid"]) == (0, 1001)
    assert _sent(transfers) == [(direct_bob, 500), (direct_bob, 501)]


def test_dispute_verdict_pays_both_sides_and_refunds_bond(
    direct_vm,
    direct_deploy,
    direct_owner,
    direct_alice,
    direct_bob,
    direct_charlie,
):
    contract = direct_deploy(CONTRACT)
    transfers = _capture_transfers(direct_vm)
    deal_id = _open_deal(contract, direct_vm, direct_alice, direct_bob, 1001)
    _accept_and_declare(contract, direct_vm, direct_bob, deal_id, [10000])
    dispute_id = _open_dispute(contract, direct_vm, direct_alice, deal_id, 0, 37)

    direct_vm.sender = direct_owner
    contract.assign_arbiter(deal_id, _address(direct_charlie))
    direct_vm.sender = direct_charlie
    contract.file_arbiter_finding(deal_id, dispute_id, "split", "Both sides have merit")

    direct_vm.mock_llm(
        r".*synthesize a final verdict.*",
        json.dumps({"verdict": "SPLIT", "split_bps": 6000, "reasoning": "Proportional settlement"}),
    )
    direct_vm.sender = direct_owner
    assert contract.finalize_dispute(deal_id, dispute_id) == "SPLIT"
    direct_vm.clear_mocks()

    deal = contract.deal(deal_id)
    dispute = contract.dispute(dispute_id)
    summary = contract.platform_summary()
    assert (deal["released"], deal["refunded"], deal["locked"]) == (600, 401, 0)
    assert deal["conserved"] is True
    assert deal["phase"] == "CLOSED"
    assert dispute["deal_id"] == deal_id
    assert dispute["bond"] == 37
    assert dispute["bond_refunded"] is True
    assert (dispute["settled_seller"], dispute["settled_buyer"]) == (600, 401)
    assert (summary["escrow_locked"], summary["bonds_locked"]) == (0, 0)
    assert summary["bonds_refunded"] == 37
    assert _sent(transfers) == [
        (direct_bob, 600),
        (direct_alice, 401),
        (direct_alice, 37),
    ]


def test_cross_deal_dispute_ids_are_rejected(
    direct_vm,
    direct_deploy,
    direct_owner,
    direct_alice,
    direct_bob,
    direct_charlie,
):
    contract = direct_deploy(CONTRACT)
    _capture_transfers(direct_vm)
    deal_a = _open_deal(contract, direct_vm, direct_alice, direct_bob, 100)
    _accept_and_declare(contract, direct_vm, direct_bob, deal_a, [10000])
    dispute_a = _open_dispute(contract, direct_vm, direct_alice, deal_a, 0, 3)

    deal_b = _open_deal(contract, direct_vm, direct_alice, direct_bob, 200)
    _accept_and_declare(contract, direct_vm, direct_bob, deal_b, [10000])
    _open_dispute(contract, direct_vm, direct_bob, deal_b, 0, 5)
    direct_vm.sender = direct_owner
    contract.assign_arbiter(deal_b, _address(direct_charlie))

    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("is not bound to deal"):
        contract.file_arbiter_finding(deal_b, dispute_a, "seller", "Wrong deal")


def test_void_refunds_remaining_escrow_and_live_dispute_bond(
    direct_vm,
    direct_deploy,
    direct_owner,
    direct_alice,
    direct_bob,
):
    contract = direct_deploy(CONTRACT)
    transfers = _capture_transfers(direct_vm)
    deal_id = _open_deal(contract, direct_vm, direct_alice, direct_bob, 1000)
    _accept_and_declare(contract, direct_vm, direct_bob, deal_id, [4000, 6000])

    direct_vm.sender = direct_bob
    contract.request_release(deal_id, 0)
    direct_vm.sender = direct_alice
    contract.release_milestone(deal_id, 0)
    dispute_id = _open_dispute(contract, direct_vm, direct_bob, deal_id, 1, 7)

    direct_vm.sender = direct_owner
    assert contract.void_deal(deal_id, "Stalled") == 600

    deal = contract.deal(deal_id)
    dispute = contract.dispute(dispute_id)
    summary = contract.platform_summary()
    assert deal["phase"] == "VOID"
    assert (deal["released"], deal["refunded"], deal["locked"]) == (400, 600, 0)
    assert deal["conserved"] is True
    assert dispute["bond_refunded"] is True
    assert (summary["escrow_locked"], summary["bonds_locked"]) == (0, 0)
    assert _sent(transfers) == [
        (direct_bob, 400),
        (direct_alice, 600),
        (direct_bob, 7),
    ]
