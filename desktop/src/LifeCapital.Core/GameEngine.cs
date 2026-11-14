namespace LifeCapital.Core;

public sealed class GameEngine
{
    private readonly GameRandom _random;
    private int _currentPlayerIndex;

    public GameEngine(IEnumerable<Player> players, int seed = 0)
    {
        Players = players.ToList();
        if (Players.Count is < 1 or > 5)
        {
            throw new ArgumentOutOfRangeException(nameof(players), "Choose between one and five players.");
        }

        var randomState = seed == 0
            ? unchecked((ulong)Random.Shared.NextInt64(1, long.MaxValue))
            : unchecked((ulong)(long)seed);
        _random = new GameRandom(randomState);
        foreach (var player in Players)
        {
            Record(player, "Opening cash", "Cash", "Opening equity", player.Cash);
            foreach (var liability in player.Liabilities)
            {
                Record(player, $"Opening {liability.Name}", "Opening equity", "Liabilities", liability.Principal);
            }
        }
    }

    private GameEngine(List<Player> players, GameSaveSnapshot snapshot)
    {
        Players = players;
        _random = new GameRandom(snapshot.RandomState);
        GameId = snapshot.GameId;
        _currentPlayerIndex = snapshot.CurrentPlayerIndex;
        TurnRolled = snapshot.TurnRolled;
        PendingDeal = snapshot.PendingDeal;
        CurrentTurnLedger = snapshot.CurrentTurnLedger.ToArray();
        WinReason = snapshot.WinReason;
        Winner = snapshot.WinnerPlayerId is Guid winnerId
            ? Players.SingleOrDefault(player => player.Id == winnerId)
                ?? throw new InvalidDataException("The saved winner is not in the player list.")
            : null;
    }

    public List<Player> Players { get; }
    public Guid GameId { get; private set; } = Guid.NewGuid();
    public int CurrentPlayerIndex => _currentPlayerIndex;
    public Player CurrentPlayer => Players[_currentPlayerIndex];
    public Player? Winner { get; private set; }
    public bool TurnRolled { get; private set; }
    public DealCard? PendingDeal { get; private set; }
    public IReadOnlyList<LedgerEntry> CurrentTurnLedger { get; private set; } = [];
    public string? WinReason { get; private set; }

    public GameSaveSnapshot CreateSnapshot() => new(
        GameId,
        CurrentPlayerIndex,
        TurnRolled,
        Winner?.Id,
        WinReason,
        PendingDeal,
        _random.State,
        CurrentTurnLedger.ToArray(),
        Players.Select(player => new PlayerSaveSnapshot(
            player.Id,
            player.Profile,
            player.Dream,
            player.Cash,
            player.MonthlyLivingExpenses,
            player.Position,
            player.Track,
            player.TurnsToSkip,
            player.CharityRollsRemaining,
            player.OwnsDream,
            player.Liabilities.Select(liability => new LiabilitySaveSnapshot(
                liability.Id,
                liability.Name,
                liability.Kind,
                liability.Principal,
                liability.MonthlyPayment,
                liability.MonthlyInterestRate)).ToArray(),
            player.Assets.Select(asset => new AssetSaveSnapshot(
                asset.Id,
                asset.Name,
                asset.MarketValue,
                asset.MonthlyCashflow,
                asset.Financing?.Id)).ToArray(),
            player.Ledger.ToArray())).ToArray());

    public static GameEngine Restore(GameSaveSnapshot snapshot)
    {
        ArgumentNullException.ThrowIfNull(snapshot);
        if (snapshot.Players is null
            || snapshot.CurrentTurnLedger is null
            || snapshot.RandomState == 0
            || snapshot.Players.Count is < 1 or > 5
            || snapshot.CurrentPlayerIndex < 0
            || snapshot.CurrentPlayerIndex >= snapshot.Players.Count)
        {
            throw new InvalidDataException("The saved game has an invalid player list or turn index.");
        }

        var players = snapshot.Players.Select(RestorePlayer).ToList();
        if (players.Select(player => player.Id).Distinct().Count() != players.Count)
        {
            throw new InvalidDataException("The saved game contains duplicate player IDs.");
        }

        return new GameEngine(players, snapshot);
    }

    public TurnResult Roll()
    {
        if (Winner is not null)
        {
            throw new InvalidOperationException("The game has already ended.");
        }
        if (TurnRolled)
        {
            throw new InvalidOperationException("End the current turn before rolling again.");
        }

        var player = CurrentPlayer;
        var turnEntries = new List<LedgerEntry>();
        if (player.TurnsToSkip > 0)
        {
            player.TurnsToSkip--;
            ApplyMonthlyCashflow(player, turnEntries, includeSalary: false);
            TurnRolled = true;
            CurrentTurnLedger = turnEntries;
            return new TurnResult(
                player,
                [],
                GetCurrentSpace(player),
                null,
                null,
                null,
                true,
                false,
                $"{player.Name} is downsized and skips this turn; monthly outgoings were paid.");
        }

        var diceCount = (player.Track == TrackKind.FastTrack ? 2 : 1)
            + (player.CharityRollsRemaining > 0 ? 1 : 0);
        var dice = Enumerable.Range(0, diceCount).Select(_ => _random.Next(1, 7)).ToArray();
        if (player.CharityRollsRemaining > 0)
        {
            player.CharityRollsRemaining--;
        }

        var spaces = SpacesFor(player.Track);
        var enteredFastTrack = false;
        BoardSpace landing = GetCurrentSpace(player);
        foreach (var _ in dice)
        {
            player.Position = (player.Position + 1) % spaces.Count;
            landing = spaces[player.Position];
            if (landing.Kind is SpaceKind.Payday or SpaceKind.CashflowDay)
            {
                ApplyMonthlyCashflow(player, turnEntries);
                if (player.Track == TrackKind.RatRace && player.CanEscapeRatRace)
                {
                    EnterFastTrack(player, turnEntries);
                    enteredFastTrack = true;
                    landing = GameContent.FastTrackSpaces[player.Position];
                    break;
                }
                if (player.Track == TrackKind.FastTrack
                    && player.PassiveIncome >= GameContent.FastTrackWinCashflow)
                {
                    Winner = player;
                    WinReason = $"Monthly passive income reached {Money(GameContent.FastTrackWinCashflow)}.";
                }
            }
        }

        DealCard? deal = null;
        EventCard? eventCard = null;
        DreamCard? dream = null;
        if (!enteredFastTrack && Winner is null)
        {
            ResolveLanding(player, landing, turnEntries, ref deal, ref eventCard, ref dream);
        }

        TurnRolled = true;
        CurrentTurnLedger = turnEntries;
        var summary = $"{player.Name} rolled {string.Join(" + ", dice)} and landed on {landing.Label}.";
        if (enteredFastTrack)
        {
            summary += " Passive income covers monthly outgoings. Fast Track unlocked!";
        }
        if (Winner == player && WinReason is not null)
        {
            summary += $" {WinReason}";
        }

        return new TurnResult(
            player, dice, landing, deal, eventCard, dream, false, enteredFastTrack, summary);
    }

    public void EndTurn()
    {
        if (Winner is not null)
        {
            throw new InvalidOperationException("The game has already ended.");
        }
        if (!TurnRolled)
        {
            throw new InvalidOperationException("Roll the dice before ending your turn.");
        }

        _currentPlayerIndex = (_currentPlayerIndex + 1) % Players.Count;
        TurnRolled = false;
        PendingDeal = null;
        CurrentTurnLedger = [];
    }

    public void ResolveCharity(bool donate)
    {
        var player = CurrentPlayer;
        if (!TurnRolled || GetCurrentSpace(player).Kind != SpaceKind.Charity)
        {
            throw new InvalidOperationException("Charity can only be resolved on a Charity space.");
        }
        if (!donate)
        {
            return;
        }

        var entries = CurrentTurnLedger.ToList();
        Spend(player, decimal.Round(player.Salary * 0.10m, 0), "Charity contribution", entries);
        player.CharityRollsRemaining = 3;
        CurrentTurnLedger = entries;
    }

    public void BuyPendingDeal(bool borrowForDownPayment = false)
    {
        var player = CurrentPlayer;
        var deal = PendingDeal ?? throw new InvalidOperationException("There is no pending deal.");
        var currentSpace = GetCurrentSpace(player);
        if (!IsDealSpaceAllowed(currentSpace, deal))
        {
            throw new InvalidOperationException("This deal does not match the space you landed on.");
        }

        var entries = CurrentTurnLedger.ToList();
        var shortfall = Math.Max(0m, deal.DownPayment - player.Cash);
        if (shortfall > 0)
        {
            if (!borrowForDownPayment)
            {
                throw new InvalidOperationException(
                    $"The down payment is short by {Money(shortfall)}. Borrow first or pass.");
            }
            BorrowBankLoan(player, RoundUpToLoanUnit(shortfall), "Deal down-payment loan", entries);
        }

        var financedAmount = deal.Price - deal.DownPayment;
        player.Cash -= deal.DownPayment;
        Record(player, $"Down payment: {deal.Title}", "Investment assets", "Cash", deal.DownPayment, entries);

        var asset = new InvestmentAsset
        {
            Name = deal.Title,
            MarketValue = deal.Price,
            MonthlyCashflow = deal.MonthlyCashflow
        };
        if (financedAmount > 0)
        {
            var liability = new Liability
            {
                Name = $"{deal.Title} financing",
                Kind = LiabilityKind.AssetLoan,
                Principal = financedAmount,
                MonthlyInterestRate = deal.AssetLoanRate ?? GameContent.BankLoanMonthlyInterestRate
            };
            asset.Financing = liability;
            player.Liabilities.Add(liability);
            Record(player, $"Financing: {deal.Title}", "Investment assets", "Asset financing", financedAmount, entries);
        }
        player.Assets.Add(asset);
        PendingDeal = null;
        CurrentTurnLedger = entries;
    }

    public void PassPendingDeal()
    {
        if (PendingDeal is null)
        {
            throw new InvalidOperationException("There is no pending deal to pass.");
        }
        PendingDeal = null;
    }

    public void BorrowBankLoan(decimal amount)
    {
        var entries = CurrentTurnLedger.ToList();
        BorrowBankLoan(CurrentPlayer, amount, "Bank loan", entries);
        CurrentTurnLedger = entries;
    }

    public void RepayBankLoan(decimal amount)
    {
        var player = CurrentPlayer;
        if (amount <= 0 || amount % 1_000m != 0)
        {
            throw new ArgumentOutOfRangeException(nameof(amount), "Repayments must be positive multiples of ₹1,000.");
        }
        if (amount > player.Cash)
        {
            throw new InvalidOperationException("Repayment cannot exceed available cash.");
        }
        if (amount > player.BankLoanBalance)
        {
            throw new InvalidOperationException("Repayment cannot exceed the outstanding bank-loan balance.");
        }

        var remaining = amount;
        var entries = CurrentTurnLedger.ToList();
        foreach (var loan in player.Liabilities.Where(x => x.Kind == LiabilityKind.BankLoan).ToArray())
        {
            var payment = Math.Min(remaining, loan.Principal);
            loan.Principal -= payment;
            player.Cash -= payment;
            remaining -= payment;
            Record(player, "Bank-loan principal repayment", "Bank loans", "Cash", payment, entries);
            if (loan.Principal == 0)
            {
                player.Liabilities.Remove(loan);
            }
            if (remaining == 0)
            {
                break;
            }
        }
        CurrentTurnLedger = entries;
    }

    public void BuyDream()
    {
        var player = CurrentPlayer;
        if (Winner is not null)
        {
            throw new InvalidOperationException("The game has already ended.");
        }
        if (player.Track != TrackKind.FastTrack || GetCurrentSpace(player).Kind != SpaceKind.Dream)
        {
            throw new InvalidOperationException("Land on a Dream space on the Fast Track first.");
        }
        if (player.Cash < player.Dream.Price)
        {
            throw new InvalidOperationException(
                $"You need {Money(player.Dream.Price - player.Cash)} more cash for this dream.");
        }

        var entries = CurrentTurnLedger.ToList();
        player.Cash -= player.Dream.Price;
        Record(player, $"Funded dream: {player.Dream.Title}", "Dreams funded", "Cash", player.Dream.Price, entries);
        player.OwnsDream = true;
        Winner = player;
        WinReason = $"Funded {player.Dream.Title}.";
        CurrentTurnLedger = entries;
    }

    public void SellAsset(InvestmentAsset asset, decimal offerPercent = 10m)
    {
        var player = CurrentPlayer;
        if (!player.Assets.Contains(asset))
        {
            throw new InvalidOperationException("That holding is not in this player's portfolio.");
        }
        if (offerPercent < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(offerPercent));
        }

        var entries = CurrentTurnLedger.ToList();
        var loan = asset.Financing;
        var proceeds = decimal.Round(asset.MarketValue * (1 + offerPercent / 100m), 0);
        player.Assets.Remove(asset);
        Record(player, $"Sold {asset.Name}", "Cash", "Investment assets", proceeds, entries);
        player.Cash += proceeds;

        if (loan is not null)
        {
            if (player.Cash < loan.Principal)
            {
                var shortfall = loan.Principal - player.Cash;
                BorrowBankLoan(player, RoundUpToLoanUnit(shortfall), "Emergency loan to clear asset financing", entries);
            }
            player.Cash -= loan.Principal;
            player.Liabilities.Remove(loan);
            Record(player, $"Cleared financing for {asset.Name}", "Asset financing", "Cash", loan.Principal, entries);
        }
        CurrentTurnLedger = entries;
    }

    public static IReadOnlyList<BoardSpace> SpacesFor(TrackKind track) =>
        track == TrackKind.RatRace ? GameContent.RatRaceSpaces : GameContent.FastTrackSpaces;

    public static string Money(decimal amount) => $"₹{amount:N0}";

    private void ResolveLanding(
        Player player,
        BoardSpace landing,
        List<LedgerEntry> entries,
        ref DealCard? deal,
        ref EventCard? eventCard,
        ref DreamCard? dream)
    {
        switch (landing.Kind)
        {
            case SpaceKind.SmallDeal:
            case SpaceKind.BigDeal:
            case SpaceKind.Opportunity:
                var size = landing.Kind == SpaceKind.SmallDeal ? DealSize.Small : DealSize.Big;
                var deck = GameContent.Deals.Where(card => card.Size == size).ToArray();
                if (deck.Length == 0)
                {
                    throw new InvalidOperationException($"No {size} deal cards are available.");
                }
                deal = deck[_random.Next(deck.Length)];
                PendingDeal = deal;
                break;

            case SpaceKind.Doodad:
                eventCard = Draw(GameContent.Doodads);
                Spend(player, eventCard.Amount, eventCard.Title, entries);
                break;

            case SpaceKind.Market:
                eventCard = Draw(GameContent.MarketEvents);
                ResolveMarket(player, eventCard, entries);
                break;

            case SpaceKind.Charity:
                eventCard = new EventCard(
                    "charity-choice",
                    "Charity",
                    "Optionally donate 10% of monthly salary. If you do, roll one extra die for your next three turns.");
                break;

            case SpaceKind.Downsized:
                player.TurnsToSkip = 2;
                eventCard = new EventCard(
                    "downsized",
                    "Downsized",
                    "Skip your next two turns. Monthly outgoings continue; shortfalls use an emergency bank loan.");
                break;

            case SpaceKind.Baby:
                eventCard = Draw(GameContent.BabyEvents);
                player.MonthlyLivingExpenses += eventCard.Amount;
                Record(player, eventCard.Title, "Household expenses", "Monthly budget", eventCard.Amount, entries);
                break;

            case SpaceKind.Dream:
                dream = player.Dream;
                break;
        }
    }

    private void ResolveMarket(Player player, EventCard card, List<LedgerEntry> entries)
    {
        if (card.Id == "market-growth" || card.Id == "market-correction")
        {
            foreach (var asset in player.Assets)
            {
                var change = decimal.Round(asset.MarketValue * card.Amount / 100m, 0);
                asset.MarketValue += change;
                var debit = change >= 0 ? "Investment assets" : "Market loss";
                var credit = change >= 0 ? "Market gain" : "Investment assets";
                Record(player, card.Title, debit, credit, Math.Abs(change), entries);
            }
        }
        else if (card.Id == "cash-distribution")
        {
            player.Cash += card.Amount;
            Record(player, card.Title, "Cash", "Investment income", card.Amount, entries);
        }
    }

    private void ApplyMonthlyCashflow(
        Player player,
        List<LedgerEntry> entries,
        bool includeSalary = true)
    {
        if (includeSalary && player.Track == TrackKind.RatRace && player.Salary > 0)
        {
            player.Cash += player.Salary;
            Record(player, "Monthly salary", "Cash", "Salary income", player.Salary, entries);
        }
        if (player.PassiveIncome > 0)
        {
            player.Cash += player.PassiveIncome;
            Record(player, "Monthly asset income", "Cash", "Passive income", player.PassiveIncome, entries);
        }

        Spend(player, player.MonthlyLivingExpenses, "Monthly living expenses", entries);
        foreach (var liability in player.Liabilities.ToArray())
        {
            if (liability.Kind == LiabilityKind.Consumer)
            {
                var payment = Math.Min(liability.Principal, liability.MonthlyPayment);
                if (player.Cash < payment)
                {
                    BorrowBankLoan(
                        player,
                        RoundUpToLoanUnit(payment - player.Cash),
                        $"Emergency loan for {liability.Name}",
                        entries);
                }
                player.Cash -= payment;
                liability.Principal -= payment;
                Record(player, $"{liability.Name} principal payment",
                    "Consumer debt", "Cash", payment, entries);
                if (liability.Principal == 0)
                {
                    player.Liabilities.Remove(liability);
                }
            }
            else
            {
                var interest = decimal.Round(liability.Principal * liability.MonthlyInterestRate, 0);
                Spend(player, interest, $"{liability.Name} interest", entries);
            }
        }
    }

    private void EnterFastTrack(Player player, List<LedgerEntry> entries)
    {
        player.Track = TrackKind.FastTrack;
        player.Position = 0;
        var bonus = player.Cash * 99m;
        player.Cash += bonus;
        Record(player, "Fast Track entry bonus (100x cash)", "Cash", "Fast Track bonus", bonus, entries);

        foreach (var liability in player.Liabilities
                     .Where(item => item.Kind == LiabilityKind.Consumer)
                     .ToArray())
        {
            Record(player, $"Cleared on Fast Track: {liability.Name}",
                "Consumer debt", "Fast Track debt relief", liability.Principal, entries);
            player.Liabilities.Remove(liability);
        }
    }

    private void Spend(Player player, decimal amount, string description, List<LedgerEntry> entries)
    {
        if (amount <= 0)
        {
            return;
        }
        if (player.Cash < amount)
        {
            var shortfall = amount - player.Cash;
            BorrowBankLoan(player, RoundUpToLoanUnit(shortfall), "Emergency loan", entries);
        }
        player.Cash -= amount;
        Record(player, description, "Expenses", "Cash", amount, entries);
    }

    private static void BorrowBankLoan(
        Player player,
        decimal amount,
        string purpose,
        List<LedgerEntry> entries)
    {
        if (amount <= 0 || amount % 1_000m != 0)
        {
            throw new ArgumentOutOfRangeException(nameof(amount), "Bank loans must be positive multiples of ₹1,000.");
        }

        player.Cash += amount;
        player.Liabilities.Add(new Liability
        {
            Name = purpose,
            Kind = LiabilityKind.BankLoan,
            Principal = amount,
            MonthlyInterestRate = GameContent.BankLoanMonthlyInterestRate
        });
        Record(player, purpose, "Cash", "Bank loans", amount, entries);
    }

    private static decimal RoundUpToLoanUnit(decimal amount) =>
        decimal.Ceiling(amount / 1_000m) * 1_000m;

    private static void Record(
        Player player,
        string description,
        string debitAccount,
        string creditAccount,
        decimal amount,
        List<LedgerEntry>? entries = null)
    {
        if (amount < 0 || (amount > 0
            && (string.IsNullOrWhiteSpace(debitAccount) || string.IsNullOrWhiteSpace(creditAccount))))
        {
            throw new InvalidOperationException("Ledger entries must have a non-negative amount and two accounts.");
        }
        if (amount == 0)
        {
            return;
        }

        var entry = new LedgerEntry(
            DateTimeOffset.UtcNow, description, debitAccount, creditAccount, amount);
        player.Ledger.Add(entry);
        entries?.Add(entry);
    }

    private static Player RestorePlayer(PlayerSaveSnapshot snapshot)
    {
        if (snapshot.Profile is null
            || snapshot.Dream is null
            || snapshot.Liabilities is null
            || snapshot.Assets is null
            || snapshot.Ledger is null
            || !Enum.IsDefined(typeof(TrackKind), snapshot.Track)
            || snapshot.Position < 0
            || snapshot.Position >= SpacesFor(snapshot.Track).Count
            || snapshot.TurnsToSkip < 0
            || snapshot.CharityRollsRemaining < 0)
        {
            throw new InvalidDataException("The saved player has an invalid board or turn state.");
        }
        if (snapshot.Liabilities.Any(item => !Enum.IsDefined(typeof(LiabilityKind), item.Kind))
            || snapshot.Liabilities.Select(item => item.Id).Distinct().Count() != snapshot.Liabilities.Count
            || snapshot.Assets.Select(item => item.Id).Distinct().Count() != snapshot.Assets.Count)
        {
            throw new InvalidDataException("The saved player has invalid or duplicate portfolio entries.");
        }

        var player = new Player(snapshot.Profile, snapshot.Dream, snapshot.Id)
        {
            Cash = snapshot.Cash,
            MonthlyLivingExpenses = snapshot.MonthlyLivingExpenses,
            Position = snapshot.Position,
            Track = snapshot.Track,
            TurnsToSkip = snapshot.TurnsToSkip,
            CharityRollsRemaining = snapshot.CharityRollsRemaining,
            OwnsDream = snapshot.OwnsDream
        };
        player.Liabilities.Clear();
        var liabilities = snapshot.Liabilities.Select(item => new Liability
        {
            Id = item.Id,
            Name = item.Name,
            Kind = item.Kind,
            Principal = item.Principal,
            MonthlyPayment = item.MonthlyPayment,
            MonthlyInterestRate = item.MonthlyInterestRate
        }).ToArray();
        player.Liabilities.AddRange(liabilities);
        var liabilitiesById = liabilities.ToDictionary(item => item.Id);
        foreach (var asset in snapshot.Assets)
        {
            Liability? financing = null;
            if (asset.FinancingId is Guid financingId
                && !liabilitiesById.TryGetValue(financingId, out financing))
            {
                throw new InvalidDataException("An asset's saved financing was not found.");
            }
            player.Assets.Add(new InvestmentAsset
            {
                Id = asset.Id,
                Name = asset.Name,
                MarketValue = asset.MarketValue,
                MonthlyCashflow = asset.MonthlyCashflow,
                Financing = financing
            });
        }
        player.Ledger.AddRange(snapshot.Ledger);
        return player;
    }

    private T Draw<T>(IReadOnlyList<T> deck) => deck[_random.Next(deck.Count)];

    private static bool IsDealSpaceAllowed(BoardSpace space, DealCard deal) =>
        space.Kind switch
        {
            SpaceKind.SmallDeal => deal.Size == DealSize.Small,
            SpaceKind.BigDeal => deal.Size == DealSize.Big,
            SpaceKind.Opportunity => deal.Size == DealSize.Big,
            _ => false
        };

    private static BoardSpace GetCurrentSpace(Player player) =>
        SpacesFor(player.Track)[player.Position];

    private sealed class GameRandom
    {
        private ulong _state;

        public GameRandom(ulong state)
        {
            _state = state == 0 ? 0x9E3779B97F4A7C15UL : state;
        }

        public ulong State => _state;

        public int Next(int maxExclusive) => Next(0, maxExclusive);

        public int Next(int minInclusive, int maxExclusive)
        {
            if (minInclusive >= maxExclusive)
            {
                throw new ArgumentOutOfRangeException(nameof(maxExclusive));
            }
            var bound = (uint)(maxExclusive - minInclusive);
            var threshold = unchecked(0UL - bound) % bound;
            ulong value;
            do
            {
                value = NextUInt64();
            } while (value < threshold);

            return minInclusive + (int)(value % bound);
        }

        private ulong NextUInt64()
        {
            var value = _state;
            value ^= value >> 12;
            value ^= value << 25;
            value ^= value >> 27;
            _state = value;
            return value * 0x2545F4914F6CDD1DUL;
        }
    }
}
