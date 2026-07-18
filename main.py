from engine.game_manager import GameManager
from engine.save_system import save_game, load_game
from engine.market import MarketManager
import os
import argparse


def choose_profile() -> dict:
    print("Choose a starting profile:")
    print(" 1) Student (low cash, low income potential)")
    print(" 2) Graduate (entry-level salary)")
    print(" 3) Employee (mid salary)")
    print(" 4) Small Business Owner (higher variance)")
    choice = input("Enter 1-4 (default 2): ")
    try:
        c = int(choice)
    except Exception:
        c = 2
    if c == 1:
        return {"cash": 10_000.0, "monthly_income": 8_000.0, "expenses": 6_000.0}
    if c == 3:
        return {"cash": 60_000.0, "monthly_income": 45_000.0, "expenses": 25_000.0}
    if c == 4:
        return {"cash": 150_000.0, "monthly_income": 60_000.0, "expenses": 40_000.0}
    # default Graduate
    return {"cash": 30_000.0, "monthly_income": 30_000.0, "expenses": 18_000.0}


def main() -> None:
    print("Welcome to LifeCapital: Indian Financial Freedom Prototype")
    print("This prototype demonstrates a dynamic economy and financial decision loop.")
    print()

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--profile", choices=["student", "graduate", "employee", "business"], default=None)
    parser.add_argument("--months", type=int, default=36)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--save", type=str, default=None)
    args = parser.parse_args()

    data_path = os.path.join(os.getcwd(), "savegame.json")
    if args.save:
        data_path = args.save
    if os.path.exists(data_path) and not args.headless:
        ans = input("Found a savegame. Load it? (y/N): ")
        if ans.lower().startswith("y"):
            loaded = load_game(data_path)
            if loaded:
                player, econ = loaded
                game = GameManager()
                game.player = player
                game.economy.state = econ
                print("Loaded savegame.")
                game.start()
                return

    if args.profile:
        mapping = {
            "student": {"cash": 10_000.0, "monthly_income": 8_000.0, "expenses": 6_000.0},
            "graduate": {"cash": 30_000.0, "monthly_income": 30_000.0, "expenses": 18_000.0},
            "employee": {"cash": 60_000.0, "monthly_income": 45_000.0, "expenses": 25_000.0},
            "business": {"cash": 150_000.0, "monthly_income": 60_000.0, "expenses": 40_000.0},
        }
        profile = mapping.get(args.profile, mapping["graduate"])
    else:
        profile = choose_profile()
    game = GameManager()
    # apply profile
    game.player.cash = profile["cash"]
    game.player.monthly_income = profile["monthly_income"]
    game.player.expenses = profile["expenses"]

    # optional seed
    seed = args.seed
    if seed is not None:
        game.economy = game.economy.__class__(seed=seed)

    # Market demo list
    market = MarketManager(seed=seed)
    game.market = market
    print("Market instruments available:")
    for s in market.list_marketable():
        print(f" - {s['symbol']}: {s['name']}")

    interactive = not args.headless
    game.start(months=args.months, interactive=interactive)
    # offer save
    if args.save:
        save_game(data_path, game.player, game.economy.state)
        print(f"Saved to {data_path}")
    elif not args.headless:
        ans = input("Save this game? (y/N): ")
        if ans.lower().startswith("y"):
            save_game(data_path, game.player, game.economy.state)
            print(f"Saved to {data_path}")


if __name__ == "__main__":
    main()
