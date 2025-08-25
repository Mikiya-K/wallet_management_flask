import asyncio
import bittensor
from flask import current_app
from app.errors.custom_errors import BlockchainError
from bittensor_cli.src.bittensor.subtensor_interface import SubtensorInterface
from bittensor_cli.src.commands.stake.remove import _get_hotkeys_to_unstake, _safe_unstake_extrinsic, _unstake_extrinsic

async def get_wallets_balances(coldkeys):
    subtensor = SubtensorInterface(network=current_app.config['BITTENSOR_NETWORK'])

    block_hash = await subtensor.substrate.get_chain_head()
    free_balances, staked_balances = await asyncio.gather(
        subtensor.get_balances(*coldkeys, block_hash=block_hash),
        subtensor.get_total_stake_for_coldkey(*coldkeys, block_hash=block_hash),
    )

    return free_balances, staked_balances

def transfer(wallet, alias, toAddress, amount, wallet_password):
    wallet.coldkey_file.save_password_to_env(wallet_password)
    wallet.unlock_coldkey()

    success = bittensor.core.extrinsics.transfer.transfer_extrinsic(
        subtensor=current_app.subtensor,
        wallet=bittensor.Wallet(name=alias),
        dest=toAddress,
        amount=amount,
        transfer_all=False
    )

    return success

def remove_stake_extrinsics(wallet, alias, amount, wallet_password):
    wallet.coldkey_file.save_password_to_env(wallet_password)
    wallet.unlock_coldkey()

    success = bittensor.core.extrinsics.unstaking.unstake_extrinsic(
        subtensor=current_app.subtensor,
        wallet=bittensor.Wallet(name=alias),
        amount=amount,
        unstake_all=False
    )

    return success

async def remove_stake(wallet, alias, amount, wallet_password):
    wallet.coldkey_file.save_password_to_env(wallet_password)
    wallet.unlock_coldkey()

    wallet_unstake=bittensor.Wallet(name=alias)
    subtensor = SubtensorInterface(network=current_app.config['BITTENSOR_NETWORK'])

    return await unstake(
        wallet=wallet_unstake,
        subtensor=subtensor,
        hotkey_ss58_address=None,
        all_hotkeys=True,
        include_hotkeys=[],
        exclude_hotkeys=[],
        amount=amount,
        netuid=0,
        safe_staking=False,
        rate_tolerance=0.005,
        allow_partial_stake=False,
        era=3  # Default era
    )

async def unstake(
    wallet,
    subtensor,
    hotkey_ss58_address,
    all_hotkeys,
    include_hotkeys,
    exclude_hotkeys,
    amount,
    netuid,
    safe_staking,
    rate_tolerance,
    allow_partial_stake,
    era
):
    """Unstake from hotkey(s)."""

    chain_head = await subtensor.substrate.get_chain_head()
    (
        all_sn_dynamic_info_,
        ck_hk_identities,
        old_identities,
        stake_infos,
    ) = await asyncio.gather(
        subtensor.all_subnets(block_hash=chain_head),
        subtensor.fetch_coldkey_hotkey_identities(block_hash=chain_head),
        subtensor.get_delegate_identities(block_hash=chain_head),
        subtensor.get_stake_for_coldkey(
            wallet.coldkeypub.ss58_address, block_hash=chain_head
        ),
    )
    all_sn_dynamic_info = {info.netuid: info for info in all_sn_dynamic_info_}

    netuids = (
        [int(netuid)]
        if netuid is not None
        else await subtensor.get_all_subnet_netuids()
    )
    hotkeys_to_unstake_from = _get_hotkeys_to_unstake(
        wallet=wallet,
        hotkey_ss58_address=hotkey_ss58_address,
        all_hotkeys=all_hotkeys,
        include_hotkeys=include_hotkeys,
        exclude_hotkeys=exclude_hotkeys,
        stake_infos=stake_infos,
        identities=ck_hk_identities,
        old_identities=old_identities,
    )

    stake_in_netuids = {}
    for stake_info in stake_infos:
        if stake_info.hotkey_ss58 not in stake_in_netuids:
            stake_in_netuids[stake_info.hotkey_ss58] = {}
        stake_in_netuids[stake_info.hotkey_ss58][stake_info.netuid] = (
            stake_info.stake
        )

    # Flag to check if user wants to quit
    skip_remaining_subnets = False

    # Iterate over hotkeys and netuids to collect unstake operations
    unstake_operations = []
    total_received_amount = bittensor.Balance.from_tao(0)
    for hotkey in hotkeys_to_unstake_from:
        if skip_remaining_subnets:
            break

        staking_address_name, staking_address_ss58, _ = hotkey
        netuids_to_process = netuids

        initial_amount = amount

        for netuid in netuids_to_process:
            if skip_remaining_subnets:
                break  # Exit the loop over netuids

            subnet_info = all_sn_dynamic_info.get(netuid)
            if staking_address_ss58 not in stake_in_netuids:
                print(
                    f"No stake found for hotkey: {staking_address_ss58} on netuid: {netuid}"
                )
                continue  # Skip to next hotkey

            current_stake_balance = stake_in_netuids[staking_address_ss58].get(netuid)
            if current_stake_balance is None or current_stake_balance.tao == 0:
                print(
                    f"No stake to unstake from {staking_address_ss58} on netuid: {netuid}"
                )
                continue  # No stake to unstake

            # Determine the amount we are unstaking.
            if initial_amount:
                amount_to_unstake_as_balance = bittensor.Balance.from_tao(initial_amount)

            # Check enough stake to remove.
            amount_to_unstake_as_balance.set_unit(netuid)
            if amount_to_unstake_as_balance > current_stake_balance:
                print(
                    f"[red]Not enough stake to remove[/red]:\n"
                    f" Stake balance: [dark_orange]{current_stake_balance}[/dark_orange]"
                    f" < Unstaking amount: [dark_orange]{amount_to_unstake_as_balance}[/dark_orange]"
                    f" on netuid: {netuid}"
                )
                continue  # Skip to the next subnet - useful when single amount is specified for all subnets

            try:
                current_price = subnet_info.price.tao
                rate = current_price
                received_amount = amount_to_unstake_as_balance * rate
            except ValueError:
                continue
            total_received_amount += received_amount

            base_unstake_op = {
                "netuid": netuid,
                "hotkey_name": staking_address_name
                if staking_address_name
                else staking_address_ss58,
                "hotkey_ss58": staking_address_ss58,
                "amount_to_unstake": amount_to_unstake_as_balance,
                "current_stake_balance": current_stake_balance,
                "received_amount": received_amount,
                "dynamic_info": subnet_info,
            }

            # Additional fields for safe unstaking
            if safe_staking:
                if subnet_info.is_dynamic:
                    price_with_tolerance = current_price * (1 - rate_tolerance)
                    rate_with_tolerance = price_with_tolerance
                    price_with_tolerance = bittensor.Balance.from_tao(
                        rate_with_tolerance
                    ).rao  # Actual price to pass to extrinsic
                else:
                    rate_with_tolerance = 1
                    price_with_tolerance = 1

                base_unstake_op["price_with_tolerance"] = price_with_tolerance

            unstake_operations.append(base_unstake_op)

    if not unstake_operations:
        raise BlockchainError("No unstake operations to perform")

    successes = []

    for op in unstake_operations:
        common_args = {
            "wallet": wallet,
            "subtensor": subtensor,
            "netuid": op["netuid"],
            "amount": op["amount_to_unstake"],
            "hotkey_ss58": op["hotkey_ss58"],
            "era": era
        }

        if safe_staking and op["netuid"] != 0:
            func = _safe_unstake_extrinsic
            specific_args = {
                "price_limit": op["price_with_tolerance"],
                "allow_partial_stake": allow_partial_stake,
            }
        else:
            func = _unstake_extrinsic
            specific_args = {"current_stake": op["current_stake_balance"]}

        suc = await func(**common_args, **specific_args)

        successes.append(
            {
                "netuid": op["netuid"],
                "hotkey_ss58": op["hotkey_ss58"],
                "unstake_amount": op["amount_to_unstake"].tao,
                "success": suc,
            }
        )
