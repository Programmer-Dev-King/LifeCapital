# LifeCapital

LifeCapital is a native Windows financial-literacy board game built with C# WinForms. The active `main` branch contains the desktop game and its tests.

[![CI](https://github.com/Programmer-Dev-King/LifeCapital/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Programmer-Dev-King/LifeCapital/actions/workflows/ci.yml)

## Play

Download and extract the [latest Windows preview](https://github.com/Programmer-Dev-King/LifeCapital/releases/latest), then run `LifeCapital.Desktop.exe`. The preview bundle is self-contained and does not require a separate .NET runtime installation.

Start a game for 1–5 players, choose each player's profession and dream, then take turns rolling and resolving board spaces. Build a portfolio, manage expenses and liabilities, make deals, and work toward the Fast Track goals. Games can be saved and resumed locally.

## Features

- Two 24-space tracks with a Rat Race-to-Fast Track progression
- Profession-based player profiles and selectable dreams
- Deals, liabilities, portfolio changes, and a transaction ledger
- Local save/load, including turn and random-number state
- Creator-fund tracker
- SQLite persistence on the player's device

## Build and test

Requires the .NET 10 SDK and Windows Desktop targeting pack.

Run these commands from the repository root:

```powershell
dotnet build .\desktop\LifeCapital.slnx -c Release
dotnet run --project .\desktop\tests\LifeCapital.RulesTests\LifeCapital.RulesTests.csproj -c Release
dotnet run --project .\desktop\tests\LifeCapital.DesktopSmoke\LifeCapital.DesktopSmoke.csproj -c Release
```

For packaging and additional setup notes, see [`desktop/README.md`](desktop/README.md).

## Local data and disclaimer

The desktop game stores its database at `%LOCALAPPDATA%\LifeCapital\life-capital.db`. Game scenarios and financial amounts are fictional and for educational entertainment only; they are not investment, tax, or legal advice. The game is independent and is not affiliated with or endorsed by the commercial CASHFLOW game or its rights holders. Real-world income tax is not calculated.

Earlier prototype snapshots remain available only through their historical Git tags; they are not part of the active desktop project.
