namespace LifeCapital.Core;

public enum TrackKind
{
    RatRace,
    FastTrack
}

public enum SpaceKind
{
    Payday,
    SmallDeal,
    BigDeal,
    Market,
    Doodad,
    Charity,
    Downsized,
    Baby,
    CashflowDay,
    Dream,
    Opportunity
}

public enum LiabilityKind
{
    Consumer,
    BankLoan,
    AssetLoan
}

public enum DealSize
{
    Small,
    Big
}

public sealed record BoardSpace(int Index, TrackKind Track, SpaceKind Kind, string Label);

public sealed record LiabilityTerms(
    string Name,
    decimal Principal,
    decimal MonthlyPayment,
    LiabilityKind Kind);

public sealed record ProfessionProfile(
    string Name,
    string Profession,
    string City,
    decimal MonthlySalary,
    decimal MonthlyLivingExpenses,
    decimal StartingCash,
    LiabilityTerms? StartingLiability,
    string ScenarioNote);

public sealed record DealCard(
    string Id,
    DealSize Size,
    string Title,
    string Description,
    decimal Price,
    decimal DownPayment,
    decimal MonthlyCashflow,
    decimal? AssetLoanRate = null);

public sealed record EventCard(
    string Id,
    string Title,
    string Description,
    decimal Amount = 0);

public sealed record DreamCard(string Id, string Title, decimal Price);

public sealed record CreatorFundStatus(decimal Saved, decimal Target);

public sealed record GameSaveSnapshot(
    Guid GameId,
    int CurrentPlayerIndex,
    bool TurnRolled,
    Guid? WinnerPlayerId,
    string? WinReason,
    DealCard? PendingDeal,
    ulong RandomState,
    IReadOnlyList<LedgerEntry> CurrentTurnLedger,
    IReadOnlyList<PlayerSaveSnapshot> Players);

public sealed record PlayerSaveSnapshot(
    Guid Id,
    ProfessionProfile Profile,
    DreamCard Dream,
    decimal Cash,
    decimal MonthlyLivingExpenses,
    int Position,
    TrackKind Track,
    int TurnsToSkip,
    int CharityRollsRemaining,
    bool OwnsDream,
    IReadOnlyList<LiabilitySaveSnapshot> Liabilities,
    IReadOnlyList<AssetSaveSnapshot> Assets,
    IReadOnlyList<LedgerEntry> Ledger);

public sealed record LiabilitySaveSnapshot(
    Guid Id,
    string Name,
    LiabilityKind Kind,
    decimal Principal,
    decimal MonthlyPayment,
    decimal MonthlyInterestRate);

public sealed record AssetSaveSnapshot(
    Guid Id,
    string Name,
    decimal MarketValue,
    decimal MonthlyCashflow,
    Guid? FinancingId);

public sealed record LedgerEntry(
    DateTimeOffset PostedAt,
    string Description,
    string DebitAccount,
    string CreditAccount,
    decimal Amount);

public sealed class Liability
{
    public Guid Id { get; init; } = Guid.NewGuid();
    public required string Name { get; init; }
    public required LiabilityKind Kind { get; init; }
    public required decimal Principal { get; set; }
    public decimal MonthlyPayment { get; init; }
    public decimal MonthlyInterestRate { get; init; }
}

public sealed class InvestmentAsset
{
    public Guid Id { get; init; } = Guid.NewGuid();
    public required string Name { get; init; }
    public required decimal MarketValue { get; set; }
    public required decimal MonthlyCashflow { get; init; }
    public Liability? Financing { get; set; }
}

public sealed class Player
{
    public Player(ProfessionProfile profile, DreamCard dream, Guid? id = null)
    {
        Id = id ?? Guid.NewGuid();
        Profile = profile;
        Dream = dream;
        Cash = profile.StartingCash;
        MonthlyLivingExpenses = profile.MonthlyLivingExpenses;
        if (profile.StartingLiability is { } liability)
        {
            Liabilities.Add(new Liability
            {
                Name = liability.Name,
                Kind = liability.Kind,
                Principal = liability.Principal,
                MonthlyPayment = liability.MonthlyPayment
            });
        }
    }

    public Guid Id { get; }
    public ProfessionProfile Profile { get; }
    public string Name => Profile.Name;
    public DreamCard Dream { get; }
    public decimal Cash { get; set; }
    public decimal MonthlyLivingExpenses { get; set; }
    public int Position { get; set; }
    public TrackKind Track { get; set; } = TrackKind.RatRace;
    public int TurnsToSkip { get; set; }
    public int CharityRollsRemaining { get; set; }
    public bool OwnsDream { get; set; }
    public List<Liability> Liabilities { get; } = [];
    public List<InvestmentAsset> Assets { get; } = [];
    public List<LedgerEntry> Ledger { get; } = [];

    public decimal Salary => Profile.MonthlySalary;
    public decimal PassiveIncome => Assets.Sum(asset => asset.MonthlyCashflow);
    public decimal ConsumerDebt => Liabilities
        .Where(liability => liability.Kind == LiabilityKind.Consumer)
        .Sum(liability => liability.Principal);
    public decimal BankLoanBalance => Liabilities
        .Where(liability => liability.Kind == LiabilityKind.BankLoan)
        .Sum(liability => liability.Principal);
    public decimal AssetDebt => Liabilities
        .Where(liability => liability.Kind == LiabilityKind.AssetLoan)
        .Sum(liability => liability.Principal);
    public decimal TotalDebt => Liabilities.Sum(liability => liability.Principal);
    public decimal MonthlyDebtPayments => Liabilities.Sum(liability =>
        liability.Kind == LiabilityKind.Consumer
            ? Math.Min(liability.Principal, liability.MonthlyPayment)
            : liability.Principal * liability.MonthlyInterestRate);
    public decimal MonthlyOutgoings => MonthlyLivingExpenses + MonthlyDebtPayments;
    public decimal MonthlyNetCashflow =>
        (Track == TrackKind.RatRace ? Salary : 0) + PassiveIncome - MonthlyOutgoings;
    public decimal NetWorth => Cash + Assets.Sum(asset => asset.MarketValue) - TotalDebt;

    public bool CanEscapeRatRace => PassiveIncome > MonthlyOutgoings;
}

public sealed record TurnResult(
    Player Player,
    IReadOnlyList<int> Dice,
    BoardSpace LandingSpace,
    DealCard? Deal,
    EventCard? Event,
    DreamCard? Dream,
    bool TurnSkipped,
    bool EnteredFastTrack,
    string Summary);

public static class GameContent
{
    public const decimal BankLoanMonthlyInterestRate = 0.10m;
    public const decimal SmallDealMaximum = 5_000m;
    public const decimal BigDealMinimum = 6_000m;
    public const decimal FastTrackWinCashflow = 50_000m;

    public static IReadOnlyList<ProfessionProfile> Professions { get; } =
    [
        new("Rohan Sharma", "Junior Software Engineer", "Bengaluru, Karnataka",
            65_000m, 34_000m, 60_000m,
            new("Education loan", 350_000m, 6_000m, LiabilityKind.Consumer),
            "Salary and loan are from the supplied project summary; monthly budget is a game-balancing assumption."),
        new("Suresh Verma", "Senior Admin Assistant", "Bhopal, Madhya Pradesh",
            42_000m, 27_000m, 35_000m,
            new("Personal loan", 120_000m, 4_000m, LiabilityKind.Consumer),
            "Salary and loan are from the supplied project summary; monthly budget is a game-balancing assumption."),
        new("Dhaval Patel", "Textile & Garment Merchant", "Surat, Gujarat",
            55_000m, 37_000m, 90_000m,
            new("MSME working-capital loan", 250_000m, 9_000m, LiabilityKind.Consumer),
            "Salary and loan are from the supplied project summary; monthly budget is a game-balancing assumption."),
        new("Ananya Roy", "Freelance UI/UX Designer", "Noida, Delhi NCR",
            58_000m, 33_000m, 50_000m,
            new("Credit-card EMI", 45_000m, 4_000m, LiabilityKind.Consumer),
            "Salary and loan are from the supplied project summary; monthly budget is a game-balancing assumption."),
        new("Dr. Meera Nair", "General Physician", "Kochi, Kerala",
            110_000m, 65_000m, 180_000m,
            new("Medical-equipment lease", 600_000m, 18_000m, LiabilityKind.Consumer),
            "Salary and loan are from the supplied project summary; monthly budget is a game-balancing assumption.")
    ];

    public static IReadOnlyList<DreamCard> Dreams { get; } =
    [
        new("community-clinic", "Open a community clinic", 350_000m),
        new("surat-studio", "Build a Surat design studio", 500_000m),
        new("coastal-retreat", "Create a coastal retreat", 750_000m),
        new("independent-school", "Fund a neighborhood learning center", 1_000_000m)
    ];

    public static IReadOnlyList<BoardSpace> RatRaceSpaces { get; } = BuildTrack(
        TrackKind.RatRace,
        [
            (SpaceKind.Payday, "Payday"),
            (SpaceKind.SmallDeal, "Small deal"),
            (SpaceKind.Doodad, "Doodad"),
            (SpaceKind.Payday, "Payday"),
            (SpaceKind.Market, "Market"),
            (SpaceKind.Charity, "Charity"),
            (SpaceKind.BigDeal, "Big deal"),
            (SpaceKind.Payday, "Payday"),
            (SpaceKind.Doodad, "Doodad"),
            (SpaceKind.SmallDeal, "Small deal"),
            (SpaceKind.Payday, "Payday"),
            (SpaceKind.Downsized, "Downsized"),
            (SpaceKind.Market, "Market"),
            (SpaceKind.SmallDeal, "Small deal"),
            (SpaceKind.Payday, "Payday"),
            (SpaceKind.Baby, "Baby"),
            (SpaceKind.BigDeal, "Big deal"),
            (SpaceKind.Payday, "Payday"),
            (SpaceKind.Doodad, "Doodad"),
            (SpaceKind.Charity, "Charity"),
            (SpaceKind.SmallDeal, "Small deal"),
            (SpaceKind.Payday, "Payday"),
            (SpaceKind.Market, "Market"),
            (SpaceKind.BigDeal, "Big deal")
        ]);

    public static IReadOnlyList<BoardSpace> FastTrackSpaces { get; } = BuildTrack(
        TrackKind.FastTrack,
        [
            (SpaceKind.CashflowDay, "Cashflow day"),
            (SpaceKind.Opportunity, "Opportunity"),
            (SpaceKind.Market, "Market"),
            (SpaceKind.Dream, "Dream"),
            (SpaceKind.CashflowDay, "Cashflow day"),
            (SpaceKind.Charity, "Charity"),
            (SpaceKind.Opportunity, "Opportunity"),
            (SpaceKind.Market, "Market"),
            (SpaceKind.Dream, "Dream"),
            (SpaceKind.CashflowDay, "Cashflow day"),
            (SpaceKind.Opportunity, "Opportunity"),
            (SpaceKind.Market, "Market"),
            (SpaceKind.CashflowDay, "Cashflow day"),
            (SpaceKind.Dream, "Dream"),
            (SpaceKind.Opportunity, "Opportunity"),
            (SpaceKind.Charity, "Charity"),
            (SpaceKind.Market, "Market"),
            (SpaceKind.CashflowDay, "Cashflow day"),
            (SpaceKind.Opportunity, "Opportunity"),
            (SpaceKind.Dream, "Dream"),
            (SpaceKind.Market, "Market"),
            (SpaceKind.CashflowDay, "Cashflow day"),
            (SpaceKind.Opportunity, "Opportunity"),
            (SpaceKind.Dream, "Dream")
        ]);

    public static IReadOnlyList<DealCard> Deals { get; } =
    [
        new("small-index", DealSize.Small, "Index-fund units",
            "A small hypothetical holding linked to a broad Indian market index.",
            4_000m, 4_000m, 1_500m),
        new("small-stall", DealSize.Small, "Shared market stall",
            "Buy a share in a jointly managed neighborhood market stall.",
            5_000m, 5_000m, 2_000m),
        new("small-solar", DealSize.Small, "Rooftop solar share",
            "A small participation in a fictional rooftop lease portfolio.",
            3_000m, 3_000m, 1_000m),
        new("big-textile", DealSize.Big, "Surat textile-unit partnership",
            "A fictional partnership in a small commercial textile unit.",
            18_000m, 8_000m, 9_000m),
        new("big-rental", DealSize.Big, "Rental-property co-investment",
            "A fictional co-investment with rental income and a financed balance.",
            24_000m, 10_000m, 12_000m),
        new("big-logistics", DealSize.Big, "Local logistics route",
            "A fictional share in a managed last-mile delivery route.",
            15_000m, 7_000m, 7_000m),
        new("fast-food", DealSize.Big, "Neighborhood food venture",
            "A fictional, operator-managed food business.",
            50_000m, 15_000m, 25_000m)
    ];

    public static IReadOnlyList<EventCard> Doodads { get; } =
    [
        new("vehicle-repair", "Vehicle repair", "A one-time repair bill.", 2_000m),
        new("phone-upgrade", "Phone upgrade", "An optional upgrade becomes an impulse purchase.", 1_500m),
        new("festival-travel", "Festival travel", "A family trip adds an unexpected one-time cost.", 3_000m),
        new("home-appliance", "Home appliance", "A household appliance needs replacing.", 4_000m),
        new("medical-bill", "Clinic bill", "An out-of-pocket medical cost arrives.", 2_500m)
    ];

    public static IReadOnlyList<EventCard> MarketEvents { get; } =
    [
        new("buyer-offer", "Buyer interest", "An investor offers to buy one of your holdings.", 10m),
        new("market-growth", "Market growth", "Your investment values rise by 10% in this scenario.", 10m),
        new("market-correction", "Market correction", "Your investment values fall by 10% in this scenario.", -10m),
        new("cash-distribution", "One-time distribution", "A holding pays a one-time scenario distribution.", 3_000m)
    ];

    public static IReadOnlyList<EventCard> BabyEvents { get; } =
    [
        new("new-child", "A new family member", "Monthly household costs rise in this scenario.", 5_000m),
        new("childcare", "Childcare costs", "A recurring childcare expense is added.", 3_500m)
    ];

    private static IReadOnlyList<BoardSpace> BuildTrack(
        TrackKind track,
        IReadOnlyList<(SpaceKind Kind, string Label)> definitions)
    {
        if (definitions.Count != 24)
        {
            throw new InvalidOperationException($"{track} must contain exactly 24 spaces.");
        }

        return definitions
            .Select((space, index) => new BoardSpace(index, track, space.Kind, space.Label))
            .ToArray();
    }
}
