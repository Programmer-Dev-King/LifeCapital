from __future__ import annotations

import argparse
import sys
from typing import Optional

from .cashflow import CashflowGameEngine, DealCard, MarketCard, DoodadCard


def ask_yes_no(prompt: str) -> bool:
    answer = input(prompt + " [y/N]: ").strip().lower()
    return answer in ("y", "yes")


def print_player_state(engine: CashflowGameEngine) -> None:
    player = engine.player
    print("\n=== Player Snapshot ===")
    print(f"Name          : {player.name}")
    print(f"Profession    : {player.profession}")
    print(f"Region        : {player.region}")
    print(f"Cash          : ₹{player.cash:,.0f}")
    print(f"Salary        : ₹{player.salary:,.0f}")
    print(f"Passive Income: ₹{player.passive_income():,.0f}")
    print(f"Total Income  : ₹{player.total_income():,.0f}")
    print(f"Total Expense : ₹{player.total_expenses():,.0f}")
    print(f"Cashflow      : ₹{player.monthly_cashflow():,.0f}")
    print(f"Net Worth     : ₹{player.net_worth():,.0f}")
    print(f"Assets        : {len(player.assets)}")
    print(f"Liabilities   : {len(player.liabilities)}")
    print(f"Children      : {player.children}")
    print(f"On Fast Track : {player.on_fast_track}")
    if player.on_fast_track:
        print(f"FT Income     : ₹{player.ft_monthly_income:,.0f}")
    print("=======================\n")


def describe_card(card: object) -> None:
    if isinstance(card, DealCard):
        print(f"Deal: {card.name}")
        print(f"  Cost: ₹{card.cost:,.0f}")
        print(f"  Down Payment: ₹{card.down_payment:,.0f}")
        print(f"  Monthly Cashflow: ₹{card.monthly_cashflow:,.0f}")
        print(f"  Description: {card.description}")
    elif isinstance(card, DoodadCard):
        print(f"Doodad: {card.description}")
        print(f"  Cost: ₹{card.cost:,.0f}")
        print(f"  Payment Type: {card.payment_type}")
        if card.payment_type == "monthly_increase":
            print(f"  Monthly Increase: ₹{card.monthly_increase:,.0f}")
    elif isinstance(card, MarketCard):
        print(f"Market: {card.description}")
        print(f"  Affects: {card.affects}")
        print(f"  Multiplier: {card.multiplier}")
        print(f"  Sell Opportunity: {card.sell_opportunity}")
    else:
        print("Unknown card type.")


def sell_matching_assets(engine: CashflowGameEngine, affects: str) -> None:
    matches = [a for a in engine.player.assets if a.asset_type.value == affects or a.asset_type.value == affects.replace("_", " ")]
    if not matches:
        print("No matching assets to sell.")
        return
    for asset in matches:
        if ask_yes_no(f"Sell {asset.name} worth ₹{asset.value:,.0f}? "):
            print(engine.sell_asset(asset.name))


def run() -> None:
    parser = argparse.ArgumentParser(description="Cashflow Rat Race CLI Prototype")
    parser.add_argument("--profession", choices=["ias", "ca", "clerk", "startup", "kisan"], default="startup")
    parser.add_argument("--region", choices=["metro", "tier2", "rural"], default="tier2")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    engine = CashflowGameEngine(profession=args.profession, region=args.region, seed=args.seed)
    print("Welcome to LifeCapital Cashflow Prototype")
    print("Play through the Indian Rat Race and escape to Fast Track.")
    print_player_state(engine)

    while True:
        if engine.player.bankrupt:
            print("Game over: You are bankrupt.")
            break
        if engine.player.on_fast_track and engine.check_win():
            print("Congratulations! You won Fast Track.")
            break

        if engine.player.on_fast_track:
            result = engine.fast_track_turn()
        else:
            result = engine.take_turn()

        print(f"Rolled: {result.rolled}")
        print(f"Space: {result.space.name} ({result.space.space_type})")
        print(result.event)

        if result.card:
            describe_card(result.card)
            if isinstance(result.card, DealCard):
                accept = ask_yes_no("Do you want to purchase this deal?")
                print(engine.apply_deal_card(result.card, accept))
            elif isinstance(result.card, MarketCard) and result.card.sell_opportunity:
                if ask_yes_no("Do you want to sell matching assets at this opportunity?"):
                    sell_matching_assets(engine, result.card.affects)

        if result.entered_fast_track:
            print("You can now enter Fast Track! Use the next turn automatically.")

        print_player_state(engine)
        if engine.player.on_fast_track and engine.check_win():
            print("Congratulations! You won Fast Track.")
            break
        if not ask_yes_no("Continue to next turn?"):
            print("Exiting game. Save the prototype state and play again later.")
            break

    print("Final state:")
    print_player_state(engine)


if __name__ == "__main__":
    run()
