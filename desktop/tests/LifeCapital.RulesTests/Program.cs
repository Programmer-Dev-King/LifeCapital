using LifeCapital.Core;
using Microsoft.Data.Sqlite;
using System.Globalization;

var tests = new (string Name, Action Run)[]
{
    ("Both board tracks have 24 spaces", BoardTracksHaveTwentyFourSpaces),
    ("Bank loans use ₹1,000 increments", BankLoansUseThousandRupeeIncrements),
    ("A payday applies salary, living costs and debt service", PaydayPostsMonthlyCashflow),
    ("Emergency borrowing prevents negative cash", EmergencyBorrowingPreventsNegativeCash),
    ("Fast Track exit clears consumer debt and grants the entry bonus", FastTrackExitAppliesItsRules),
    ("Small-deal purchase finances a cash shortfall", DealPurchaseFinancesDownPayment),
    ("Every ledger posting has equal debit and credit", LedgerEntriesAreBalanced),
    ("SQLite stores game, ledger and creator-fund records", SqlitePersistsGameData)
};

var failures = new List<string>();
foreach (var (name, run) in tests)
{
    try
    {
        run();
        Console.WriteLine($"PASS  {name}");
    }
    catch (Exception error)
    {
        failures.Add($"{name}: {error.Message}");
        Console.WriteLine($"FAIL  {name}: {error.Message}");
    }
}

Console.WriteLine($"{tests.Length - failures.Count}/{tests.Length} rule checks passed.");
return failures.Count == 0 ? 0 : 1;

static void BoardTracksHaveTwentyFourSpaces()
{
    Equal(24, GameContent.RatRaceSpaces.Count);
    Equal(24, GameContent.FastTrackSpaces.Count);
    Equal(5, GameContent.Professions.Count);
}

static void BankLoansUseThousandRupeeIncrements()
{
    var player = CreatePlayer();
    var game = new GameEngine([player], seed: 17);
    var originalCash = player.Cash;

    Throws<ArgumentOutOfRangeException>(() => game.BorrowBankLoan(1_500m));
    Equal(originalCash, player.Cash);

    game.BorrowBankLoan(2_000m);
    Equal(originalCash + 2_000m, player.Cash);
    Equal(2_000m, player.BankLoanBalance);
}

static void PaydayPostsMonthlyCashflow()
{
    var player = CreatePlayer();
    player.Position = 2;
    var game = new GameEngine([player], seed: SeedForDie(1));
    var initialCash = player.Cash;
    var initialDebt = player.ConsumerDebt;

    var result = game.Roll();

    Equal(1, result.Dice.Count);
    Equal(SpaceKind.Payday, result.LandingSpace.Kind);
    Equal(initialCash + player.Salary - player.MonthlyLivingExpenses
        - 6_000m, player.Cash);
    Equal(initialDebt - 6_000m, player.ConsumerDebt);
}

static void EmergencyBorrowingPreventsNegativeCash()
{
    var profile = GameContent.Professions[0] with { StartingCash = 0m };
    var player = new Player(profile, GameContent.Dreams[0]) { TurnsToSkip = 1 };
    var game = new GameEngine([player], seed: 9);

    var result = game.Roll();

    True(result.TurnSkipped);
    True(player.Cash >= 0);
    True(player.BankLoanBalance >= 40_000m);
}

static void FastTrackExitAppliesItsRules()
{
    var player = CreatePlayer();
    player.Position = 2;
    player.Assets.Add(new InvestmentAsset
    {
        Name = "Scenario income asset",
        MarketValue = 50_000m,
        MonthlyCashflow = 50_000m
    });
    player.Liabilities.Add(new Liability
    {
        Name = "Scenario asset loan",
        Kind = LiabilityKind.AssetLoan,
        Principal = 20_000m,
        MonthlyInterestRate = GameContent.BankLoanMonthlyInterestRate
    });
    var initialCash = player.Cash;
    var game = new GameEngine([player], seed: SeedForDie(1));

    var result = game.Roll();

    True(result.EnteredFastTrack);
    Equal(TrackKind.FastTrack, player.Track);
    Equal(0, player.Position);
    Equal(0m, player.ConsumerDebt);
    Equal(20_000m, player.AssetDebt);
    True(player.Cash > initialCash * 99m);
}

static void DealPurchaseFinancesDownPayment()
{
    var profile = GameContent.Professions[0] with { StartingCash = 0m };
    var player = new Player(profile, GameContent.Dreams[0]);
    var game = new GameEngine([player], seed: SeedForDie(1));

    var result = game.Roll();

    Equal(SpaceKind.SmallDeal, result.LandingSpace.Kind);
    True(result.Deal is not null);
    game.BuyPendingDeal(borrowForDownPayment: true);

    Equal(1, player.Assets.Count);
    True(player.Cash >= 0);
    True(player.BankLoanBalance > 0);
    True(player.PassiveIncome > 0);
}

static void LedgerEntriesAreBalanced()
{
    var player = CreatePlayer();
    var game = new GameEngine([player], seed: SeedForDie(1));
    player.Position = 2;
    game.Roll();

    True(player.Ledger.Count > 0);
    True(player.Ledger.All(entry =>
        entry.Amount > 0
        && !string.IsNullOrWhiteSpace(entry.DebitAccount)
        && !string.IsNullOrWhiteSpace(entry.CreditAccount)));
}

static void SqlitePersistsGameData()
{
    var path = Path.Combine(Path.GetTempPath(), $"life-capital-{Guid.NewGuid():N}.db");
    try
    {
        using (var oldConnection = new SqliteConnection(
            new SqliteConnectionStringBuilder { DataSource = path }.ToString()))
        {
            oldConnection.Open();
            using var command = oldConnection.CreateCommand();
            command.CommandText = """
                CREATE TABLE GameSaves (
                    Id TEXT PRIMARY KEY,
                    SavedAtUtc TEXT NOT NULL,
                    CurrentPlayerIndex INTEGER NOT NULL,
                    TurnRolled INTEGER NOT NULL,
                    WinnerPlayerId TEXT NULL,
                    WinReason TEXT NULL
                );
                """;
            command.ExecuteNonQuery();
        }

        var store = new SqliteGameStore(path);
        store.InitializeAsync().GetAwaiter().GetResult();
        Equal<GameEngine?>(null, store.LoadAsync().GetAwaiter().GetResult());
        var fund = store.GetCreatorFundAsync().GetAwaiter().GetResult();
        Equal(18_150m, fund.Saved);
        Equal(5_500_000m, fund.Target);
        fund = store.AddCreatorFundContributionAsync(1_000m).GetAwaiter().GetResult();
        Equal(19_150m, fund.Saved);

        var player = CreatePlayer();
        player.Position = 5;
        var game = new GameEngine([player], seed: SeedForDie(1));
        var turn = game.Roll();
        Equal(SpaceKind.BigDeal, turn.LandingSpace.Kind);
        store.SaveAsync(game).GetAwaiter().GetResult();
        store.SaveAsync(game).GetAwaiter().GetResult();
        var restored = store.LoadAsync().GetAwaiter().GetResult()
            ?? throw new InvalidOperationException("The saved game was not returned.");
        Equal(game.GameId, restored.GameId);
        Equal(game.CurrentPlayer.Id, restored.CurrentPlayer.Id);
        Equal(game.CurrentPlayer.Position, restored.CurrentPlayer.Position);
        Equal(game.PendingDeal?.Id, restored.PendingDeal?.Id);
        Equal(game.CurrentPlayer.Ledger.Count, restored.CurrentPlayer.Ledger.Count);

        game.BuyPendingDeal();
        restored.BuyPendingDeal();
        Equal(game.CurrentPlayer.Cash, restored.CurrentPlayer.Cash);
        True(game.CurrentPlayer.Assets[0].Financing is not null);
        True(restored.CurrentPlayer.Assets[0].Financing is not null);
        Equal(game.CurrentPlayer.Assets[0].Financing?.Principal,
            restored.CurrentPlayer.Assets[0].Financing?.Principal);
        game.EndTurn();
        restored.EndTurn();
        var expectedNextTurn = game.Roll();
        var restoredNextTurn = restored.Roll();
        True(expectedNextTurn.Dice.SequenceEqual(restoredNextTurn.Dice));
        var savedAssetId = restored.CurrentPlayer.Assets[0].Id;
        var savedFinancingId = restored.CurrentPlayer.Assets[0].Financing?.Id;
        store.SaveAsync(restored).GetAwaiter().GetResult();
        restored = store.LoadAsync().GetAwaiter().GetResult()
            ?? throw new InvalidOperationException("The updated saved game was not returned.");
        Equal(savedAssetId, restored.CurrentPlayer.Assets[0].Id);
        Equal(savedFinancingId, restored.CurrentPlayer.Assets[0].Financing?.Id);

        {
            using var connection = new SqliteConnection(
                new SqliteConnectionStringBuilder { DataSource = path }.ToString());
            connection.Open();
            Equal(1L, Scalar(connection, "SELECT COUNT(*) FROM GameSaves;"));
            Equal(1L, Scalar(connection, "SELECT COUNT(*) FROM GamePlayers;"));
            True(Scalar(connection, "SELECT COUNT(*) FROM Liabilities;") >= 2L);
            True(Scalar(connection, "SELECT COUNT(*) FROM LedgerEntries;") > 0);
            True(HasColumn(connection, "GameSaves", "StateJson"));
        }
    }
    finally
    {
        SqliteConnection.ClearAllPools();
        foreach (var suffix in new[] { "", "-wal", "-shm" })
        {
            var file = path + suffix;
            if (File.Exists(file))
            {
                File.Delete(file);
            }
        }
    }
}

static long Scalar(SqliteConnection connection, string sql)
{
    using var command = connection.CreateCommand();
    command.CommandText = sql;
    return Convert.ToInt64(command.ExecuteScalar(), CultureInfo.InvariantCulture);
}

static bool HasColumn(SqliteConnection connection, string table, string name)
{
    using var command = connection.CreateCommand();
    command.CommandText = $"PRAGMA table_info({table});";
    using var reader = command.ExecuteReader();
    while (reader.Read())
    {
        if (reader.GetString(1) == name)
        {
            return true;
        }
    }
    return false;
}

static Player CreatePlayer() =>
    new(GameContent.Professions[0], GameContent.Dreams[0]);

static int SeedForDie(int target)
{
    for (var seed = 1; seed < 10_000; seed++)
    {
        if (new GameEngine([CreatePlayer()], seed).Roll().Dice[0] == target)
        {
            return seed;
        }
    }
    throw new InvalidOperationException("Could not find a deterministic die seed.");
}

static void True(bool condition)
{
    if (!condition)
    {
        throw new InvalidOperationException("Expected condition to be true.");
    }
}

static void Equal<T>(T expected, T actual)
{
    if (!EqualityComparer<T>.Default.Equals(expected, actual))
    {
        throw new InvalidOperationException($"Expected {expected}; received {actual}.");
    }
}

static void Throws<TException>(Action action) where TException : Exception
{
    try
    {
        action();
    }
    catch (TException)
    {
        return;
    }
    throw new InvalidOperationException($"Expected {typeof(TException).Name}.");
}
