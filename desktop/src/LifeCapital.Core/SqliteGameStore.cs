using System.Globalization;
using System.Text.Json;
using Microsoft.Data.Sqlite;

namespace LifeCapital.Core;

public sealed class SqliteGameStore
{
    private readonly string _databasePath;
    private readonly string _connectionString;

    public SqliteGameStore(string databasePath)
    {
        var fullPath = Path.GetFullPath(databasePath);
        _databasePath = fullPath;
        _connectionString = new SqliteConnectionStringBuilder
        {
            DataSource = fullPath,
            ForeignKeys = true
        }.ToString();
    }

    public async Task InitializeAsync(CancellationToken cancellationToken = default)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(_databasePath)!);
        await using var connection = new SqliteConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);
        await using var command = connection.CreateCommand();
        command.CommandText = """
            CREATE TABLE IF NOT EXISTS GameSaves (
                Id TEXT PRIMARY KEY,
                SavedAtUtc TEXT NOT NULL,
                CurrentPlayerIndex INTEGER NOT NULL,
                TurnRolled INTEGER NOT NULL,
                WinnerPlayerId TEXT NULL,
                WinReason TEXT NULL,
                StateJson TEXT NULL
            );
            CREATE TABLE IF NOT EXISTS GamePlayers (
                Id TEXT PRIMARY KEY,
                GameId TEXT NOT NULL REFERENCES GameSaves(Id) ON DELETE CASCADE,
                Name TEXT NOT NULL,
                Profession TEXT NOT NULL,
                City TEXT NOT NULL,
                MonthlySalary TEXT NOT NULL,
                MonthlyLivingExpenses TEXT NOT NULL,
                Cash TEXT NOT NULL,
                Track INTEGER NOT NULL,
                Position INTEGER NOT NULL,
                TurnsToSkip INTEGER NOT NULL,
                CharityRollsRemaining INTEGER NOT NULL,
                DreamId TEXT NOT NULL,
                DreamPrice TEXT NOT NULL,
                OwnsDream INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS Liabilities (
                Id TEXT PRIMARY KEY,
                PlayerId TEXT NOT NULL REFERENCES GamePlayers(Id) ON DELETE CASCADE,
                Name TEXT NOT NULL,
                Kind INTEGER NOT NULL,
                Principal TEXT NOT NULL,
                MonthlyPayment TEXT NOT NULL,
                MonthlyInterestRate TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS Assets (
                Id TEXT PRIMARY KEY,
                PlayerId TEXT NOT NULL REFERENCES GamePlayers(Id) ON DELETE CASCADE,
                Name TEXT NOT NULL,
                MarketValue TEXT NOT NULL,
                MonthlyCashflow TEXT NOT NULL,
                FinancingId TEXT NULL
            );
            CREATE TABLE IF NOT EXISTS LedgerEntries (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                PlayerId TEXT NOT NULL REFERENCES GamePlayers(Id) ON DELETE CASCADE,
                PostedAtUtc TEXT NOT NULL,
                Description TEXT NOT NULL,
                DebitAccount TEXT NOT NULL,
                CreditAccount TEXT NOT NULL,
                Amount TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS CreatorFundGoals (
                Id INTEGER PRIMARY KEY CHECK (Id = 1),
                SavedAmount TEXT NOT NULL,
                TargetAmount TEXT NOT NULL
            );
            INSERT OR IGNORE INTO CreatorFundGoals (Id, SavedAmount, TargetAmount)
            VALUES (1, '18150', '5500000');
            CREATE INDEX IF NOT EXISTS IX_GamePlayers_GameId ON GamePlayers(GameId);
            CREATE INDEX IF NOT EXISTS IX_LedgerEntries_PlayerId ON LedgerEntries(PlayerId);
            """;
        await command.ExecuteNonQueryAsync(cancellationToken);

        var hasStateColumn = false;
        await using (var columns = connection.CreateCommand())
        {
            columns.CommandText = "PRAGMA table_info(GameSaves);";
            await using var reader = await columns.ExecuteReaderAsync(cancellationToken);
            while (await reader.ReadAsync(cancellationToken))
            {
                if (reader.GetString(1) == "StateJson")
                {
                    hasStateColumn = true;
                    break;
                }
            }
        }
        if (!hasStateColumn)
        {
            await using var migration = connection.CreateCommand();
            migration.CommandText = "ALTER TABLE GameSaves ADD COLUMN StateJson TEXT NULL;";
            await migration.ExecuteNonQueryAsync(cancellationToken);
        }
    }

    public async Task<CreatorFundStatus> GetCreatorFundAsync(
        CancellationToken cancellationToken = default)
    {
        await using var connection = new SqliteConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);
        await using var command = connection.CreateCommand();
        command.CommandText = "SELECT SavedAmount, TargetAmount FROM CreatorFundGoals WHERE Id = 1;";
        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        if (!await reader.ReadAsync(cancellationToken))
        {
            throw new InvalidOperationException("The creator fund has not been initialized.");
        }

        return new CreatorFundStatus(
            decimal.Parse(reader.GetString(0), CultureInfo.InvariantCulture),
            decimal.Parse(reader.GetString(1), CultureInfo.InvariantCulture));
    }

    public async Task<CreatorFundStatus> AddCreatorFundContributionAsync(
        decimal amount,
        CancellationToken cancellationToken = default)
    {
        if (amount <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(amount), "Contribution must be greater than zero.");
        }

        await using var connection = new SqliteConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);
        await using var transaction = connection.BeginTransaction();
        decimal current;
        decimal target;
        await using (var read = connection.CreateCommand())
        {
            read.Transaction = transaction;
            read.CommandText = "SELECT SavedAmount, TargetAmount FROM CreatorFundGoals WHERE Id = 1;";
            await using var reader = await read.ExecuteReaderAsync(cancellationToken);
            if (!await reader.ReadAsync(cancellationToken))
            {
                throw new InvalidOperationException("The creator fund has not been initialized.");
            }
            current = decimal.Parse(reader.GetString(0), CultureInfo.InvariantCulture);
            target = decimal.Parse(reader.GetString(1), CultureInfo.InvariantCulture);
        }

        current += amount;
        await ExecuteAsync(connection, transaction,
            "UPDATE CreatorFundGoals SET SavedAmount = $saved WHERE Id = 1;",
            cancellationToken,
            ("$saved", ToDatabase(current)));
        await transaction.CommitAsync(cancellationToken);
        return new CreatorFundStatus(current, target);
    }

    public async Task SaveAsync(GameEngine game, CancellationToken cancellationToken = default)
    {
        await using var connection = new SqliteConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);
        await using var transaction = connection.BeginTransaction();

        await ExecuteAsync(connection, transaction, """
            DELETE FROM GameSaves WHERE Id = $id;
            INSERT INTO GameSaves
                (Id, SavedAtUtc, CurrentPlayerIndex, TurnRolled, WinnerPlayerId, WinReason, StateJson)
            VALUES
                ($id, $savedAt, $currentPlayer, $turnRolled, $winnerId, $winReason, $stateJson);
            """,
            cancellationToken,
            ("$id", game.GameId.ToString()),
            ("$savedAt", DateTimeOffset.UtcNow.ToString("O", CultureInfo.InvariantCulture)),
            ("$currentPlayer", game.CurrentPlayerIndex),
            ("$turnRolled", game.TurnRolled ? 1 : 0),
            ("$winnerId", game.Winner?.Id.ToString()),
            ("$winReason", game.WinReason),
            ("$stateJson", JsonSerializer.Serialize(game.CreateSnapshot())));

        foreach (var player in game.Players)
        {
            var profile = player.Profile;
            await ExecuteAsync(connection, transaction, """
                INSERT INTO GamePlayers
                    (Id, GameId, Name, Profession, City, MonthlySalary, MonthlyLivingExpenses,
                     Cash, Track, Position, TurnsToSkip, CharityRollsRemaining, DreamId,
                     DreamPrice, OwnsDream)
                VALUES
                    ($id, $gameId, $name, $profession, $city, $salary, $expenses,
                     $cash, $track, $position, $skip, $charity, $dreamId, $dreamPrice, $ownsDream);
                """,
                cancellationToken,
                ("$id", player.Id.ToString()),
                ("$gameId", game.GameId.ToString()),
                ("$name", player.Name),
                ("$profession", profile.Profession),
                ("$city", profile.City),
                ("$salary", ToDatabase(player.Salary)),
                ("$expenses", ToDatabase(player.MonthlyLivingExpenses)),
                ("$cash", ToDatabase(player.Cash)),
                ("$track", (int)player.Track),
                ("$position", player.Position),
                ("$skip", player.TurnsToSkip),
                ("$charity", player.CharityRollsRemaining),
                ("$dreamId", player.Dream.Id),
                ("$dreamPrice", ToDatabase(player.Dream.Price)),
                ("$ownsDream", player.OwnsDream ? 1 : 0));

            foreach (var liability in player.Liabilities)
            {
                await ExecuteAsync(connection, transaction, """
                    INSERT INTO Liabilities
                        (Id, PlayerId, Name, Kind, Principal, MonthlyPayment, MonthlyInterestRate)
                    VALUES
                        ($id, $playerId, $name, $kind, $principal, $payment, $rate);
                    """,
                    cancellationToken,
                    ("$id", liability.Id.ToString()),
                    ("$playerId", player.Id.ToString()),
                    ("$name", liability.Name),
                    ("$kind", (int)liability.Kind),
                    ("$principal", ToDatabase(liability.Principal)),
                    ("$payment", ToDatabase(liability.MonthlyPayment)),
                    ("$rate", ToDatabase(liability.MonthlyInterestRate)));
            }

            foreach (var asset in player.Assets)
            {
                await ExecuteAsync(connection, transaction, """
                    INSERT INTO Assets (Id, PlayerId, Name, MarketValue, MonthlyCashflow, FinancingId)
                    VALUES ($id, $playerId, $name, $value, $cashflow, $financingId);
                    """,
                    cancellationToken,
                    ("$id", asset.Id.ToString()),
                    ("$playerId", player.Id.ToString()),
                    ("$name", asset.Name),
                    ("$value", ToDatabase(asset.MarketValue)),
                    ("$cashflow", ToDatabase(asset.MonthlyCashflow)),
                    ("$financingId", asset.Financing?.Id.ToString()));
            }

            foreach (var entry in player.Ledger)
            {
                await ExecuteAsync(connection, transaction, """
                    INSERT INTO LedgerEntries
                        (PlayerId, PostedAtUtc, Description, DebitAccount, CreditAccount, Amount)
                    VALUES
                        ($playerId, $postedAt, $description, $debit, $credit, $amount);
                    """,
                    cancellationToken,
                    ("$playerId", player.Id.ToString()),
                    ("$postedAt", entry.PostedAt.ToString("O", CultureInfo.InvariantCulture)),
                    ("$description", entry.Description),
                    ("$debit", entry.DebitAccount),
                    ("$credit", entry.CreditAccount),
                    ("$amount", ToDatabase(entry.Amount)));
            }
        }

        await transaction.CommitAsync(cancellationToken);
    }

    public async Task<GameEngine?> LoadAsync(CancellationToken cancellationToken = default)
    {
        await using var connection = new SqliteConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);
        await using var command = connection.CreateCommand();
        command.CommandText = "SELECT StateJson FROM GameSaves ORDER BY SavedAtUtc DESC LIMIT 1;";
        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        if (!await reader.ReadAsync(cancellationToken))
        {
            return null;
        }
        if (reader.IsDBNull(0))
        {
            throw new InvalidDataException(
                "The saved game uses an older format. Start a new game and save it to continue.");
        }

        var snapshot = JsonSerializer.Deserialize<GameSaveSnapshot>(reader.GetString(0))
            ?? throw new InvalidDataException("The saved game could not be read.");
        return GameEngine.Restore(snapshot);
    }

    private static async Task ExecuteAsync(
        SqliteConnection connection,
        SqliteTransaction transaction,
        string sql,
        CancellationToken cancellationToken,
        params (string Name, object? Value)[] parameters)
    {
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = sql;
        foreach (var (name, value) in parameters)
        {
            command.Parameters.AddWithValue(name, value ?? DBNull.Value);
        }
        await command.ExecuteNonQueryAsync(cancellationToken);
    }

    private static string ToDatabase(decimal value) =>
        value.ToString(CultureInfo.InvariantCulture);
}
