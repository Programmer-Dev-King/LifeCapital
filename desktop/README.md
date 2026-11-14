# Life Capital

Life Capital is a native Windows desktop financial-literacy board game, built in C# with WinForms. SQLite stores the creator-fund tracker and the latest game save.

## Play

- Download and extract the Windows preview bundle from [GitHub Releases](https://github.com/Programmer-Dev-King/LifeCapital/releases/latest), then run `LifeCapital.Desktop.exe`. You can also run the desktop project from Visual Studio.
- Choose 1–5 players, a profession, and a dream.
- Take turns rolling, resolving the landing space, and passing the device to the next player.
- Save and load from the top bar. A saved game includes player portfolios, liabilities, ledger history, pending deals, turn state, and the random-number state.
- The database is stored at `%LOCALAPPDATA%\LifeCapital\life-capital.db`.

## Rules and content

The two 24-space tracks, player profiles, and project-specific goals are based on the supplied project summary. The small-deal limit, loan increments and interest, charity bonus, Fast Track entry bonus, and win goals are implemented as game rules described by that summary.

Deal and event cards, living budgets, and investment returns are original fictional scenarios for gameplay. They are not copied from the commercial CASHFLOW game and are not real investment projections or financial advice. The game does not currently calculate real-world income tax.

The creator-fund tracker starts at ₹18,150 with a ₹55,00,000 target. Its percentage is calculated from those amounts (about 0.33%); the 33% figure in the project summary does not match that target and starting balance.

## Build and test

Requires the .NET 10 SDK and Windows Desktop targeting pack.

```powershell
dotnet build .\LifeCapital.slnx
dotnet run --project .\tests\LifeCapital.RulesTests\LifeCapital.RulesTests.csproj
dotnet run --project .\tests\LifeCapital.DesktopSmoke\LifeCapital.DesktopSmoke.csproj
dotnet publish .\src\LifeCapital.Desktop\LifeCapital.Desktop.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -o .\publish\win-x64-fixed
```
