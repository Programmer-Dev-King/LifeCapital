using LifeCapital.Core;
using Microsoft.Data.Sqlite;
using System.Text.Json;

namespace LifeCapital.Desktop;

internal sealed class MainForm : Form
{
    private static readonly string[] PlayerStatNames =
    [
        "Salary / month",
        "Passive income",
        "Living expenses",
        "Debt cost / month",
        "Total debt",
        "Cash",
        "Net worth",
        "Net monthly cash flow"
    ];

    private readonly SqliteGameStore _store;
    private readonly BoardControl _board = new();
    private readonly Label _playerName = NewValueLabel(15f, FontStyle.Bold);
    private readonly Label _playerPhase = NewValueLabel(8.5f, FontStyle.Bold, Theme.Accent);
    private readonly Label[] _statValues = PlayerStatNames
        .Select(_ => NewValueLabel(10f, FontStyle.Bold))
        .ToArray();
    private readonly ProgressBar _freedomMeter = new();
    private readonly Label _freedomText = NewValueLabel(9f, FontStyle.Bold, Theme.Gold);
    private readonly Label _dreamText = NewValueLabel(9f, FontStyle.Regular);
    private readonly Label _creatorFundText = NewValueLabel(9f, FontStyle.Regular);
    private readonly ProgressBar _creatorFundMeter = new();
    private readonly Label _status = NewValueLabel(9f, FontStyle.Regular, Theme.Muted);
    private readonly ListBox _assets = new();
    private readonly ListBox _activity = new();
    private readonly Button _newGameButton;
    private readonly Button _loadButton;
    private readonly Button _saveButton;
    private readonly Button _rollButton;
    private readonly Button _nextPlayerButton;
    private readonly Button _loanButton;
    private readonly Button _repayButton;
    private readonly Button _statementButton;
    private readonly Button _creatorFundButton;
    private GameEngine? _game;
    private CreatorFundStatus? _creatorFund;
    private bool _databaseReady;

    public MainForm()
    {
        Text = "Life Capital | India-focused Financial Strategy Game";
        StartPosition = FormStartPosition.CenterScreen;
        MinimumSize = new Size(1180, 760);
        ClientSize = new Size(1440, 900);
        BackColor = Theme.Background;
        ForeColor = Theme.Text;
        Font = Theme.BodyFont;
        DoubleBuffered = true;

        var dataPath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "LifeCapital",
            "life-capital.db");
        _store = new SqliteGameStore(dataPath);

        _newGameButton = ActionButton("NEW GAME", StartNewGame, Theme.Accent, Theme.Background);
        _loadButton = ActionButton("LOAD", LoadGame, Theme.PanelRaised, Theme.Text);
        _saveButton = ActionButton("SAVE", SaveGame, Theme.PanelRaised, Theme.Text);
        _rollButton = ActionButton("ROLL DICE", RollTurn, Theme.Accent, Theme.Background);
        _nextPlayerButton = ActionButton("NEXT PLAYER", NextPlayer, Theme.PanelRaised, Theme.Text);
        _loanButton = ActionButton("BANK LOAN", TakeLoan, Theme.PanelRaised, Theme.Text);
        _repayButton = ActionButton("REPAY LOAN", RepayLoan, Theme.PanelRaised, Theme.Text);
        _statementButton = ActionButton("FINANCIAL STATEMENT", ShowStatement, Theme.PanelRaised, Theme.Text);
        _creatorFundButton = ActionButton("ADD TO FUND", AddCreatorFundContribution, Theme.PanelRaised, Theme.Text);

        BuildLayout();
        Shown += InitializeDatabase;
        RefreshView();
    }

    private void BuildLayout()
    {
        var root = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            BackColor = Theme.Background,
            ColumnCount = 1,
            RowCount = 2,
            Padding = new Padding(18, 12, 18, 14)
        };
        root.RowStyles.Add(new RowStyle(SizeType.Absolute, 56));
        root.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        Controls.Add(root);

        var header = new Panel { Dock = DockStyle.Fill, BackColor = Theme.Background };
        root.Controls.Add(header, 0, 0);
        var brand = new Label
        {
            Text = "LIFE CAPITAL",
            Font = Theme.TitleFont,
            ForeColor = Theme.Accent,
            AutoSize = true,
            Location = new Point(2, 8)
        };
        header.Controls.Add(brand);
        var subtitle = new Label
        {
            Text = "INDIA · FINANCIAL LITERACY BOARD GAME",
            Font = Theme.SmallBoldFont,
            ForeColor = Theme.Muted,
            AutoSize = true,
            Location = new Point(215, 21)
        };
        header.Controls.Add(subtitle);

        var headerButtons = new FlowLayoutPanel
        {
            Dock = DockStyle.Right,
            FlowDirection = FlowDirection.LeftToRight,
            WrapContents = false,
            AutoSize = true,
            BackColor = Theme.Background,
            Padding = new Padding(0, 4, 0, 0)
        };
        _newGameButton.Width = 118;
        _loadButton.Width = 80;
        _saveButton.Width = 90;
        var help = ActionButton("HOW TO PLAY", ShowRules, Theme.PanelRaised, Theme.Text);
        help.Width = 130;
        headerButtons.Controls.AddRange([_newGameButton, _loadButton, _saveButton, help]);
        header.Controls.Add(headerButtons);

        var body = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 2,
            RowCount = 1,
            BackColor = Theme.Background,
            Margin = Padding.Empty
        };
        body.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 69));
        body.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 31));
        root.Controls.Add(body, 0, 1);

        _board.Dock = DockStyle.Fill;
        _board.Margin = new Padding(0, 0, 14, 0);
        body.Controls.Add(_board, 0, 0);

        var sideScroll = new Panel
        {
            Dock = DockStyle.Fill,
            AutoScroll = true,
            BackColor = Theme.Background
        };
        body.Controls.Add(sideScroll, 1, 0);
        var sidebar = new FlowLayoutPanel
        {
            FlowDirection = FlowDirection.TopDown,
            WrapContents = false,
            AutoSize = true,
            AutoSizeMode = AutoSizeMode.GrowAndShrink,
            Location = Point.Empty,
            BackColor = Theme.Background,
            Padding = Padding.Empty,
            Margin = Padding.Empty
        };
        sideScroll.Controls.Add(sidebar);
        sideScroll.Resize += (_, _) => sidebar.Width = sideScroll.ClientSize.Width - 24;
        sidebar.Width = 410;

        BuildPlayerCard(sidebar);
        BuildFinancialCard(sidebar);
        BuildFreedomCard(sidebar);
        BuildActionCard(sidebar);
        BuildPortfolioCard(sidebar);
        BuildCreatorFundCard(sidebar);
        BuildActivityCard(sidebar);
        BuildStatusCard(sidebar);
    }

    private void BuildPlayerCard(Control parent)
    {
        var card = NewCard(parent, 410, 88);
        AddCaption(card, "CURRENT PLAYER", 14, 10);
        _playerName.Location = new Point(14, 30);
        _playerName.Size = new Size(375, 24);
        card.Controls.Add(_playerName);
        _playerPhase.Location = new Point(15, 58);
        _playerPhase.AutoSize = true;
        card.Controls.Add(_playerPhase);
    }

    private void BuildFinancialCard(Control parent)
    {
        var card = NewCard(parent, 410, 178);
        AddCaption(card, "FINANCIAL STATEMENT · PER MONTH", 14, 10);
        var grid = new TableLayoutPanel
        {
            Location = new Point(14, 34),
            Size = new Size(380, 132),
            ColumnCount = 2,
            RowCount = 4,
            BackColor = Theme.Panel
        };
        grid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 57));
        grid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 43));
        for (var row = 0; row < 4; row++)
        {
            grid.RowStyles.Add(new RowStyle(SizeType.Percent, 25));
            for (var column = 0; column < 2; column++)
            {
                var index = row * 2 + column;
                var cell = new Panel { Dock = DockStyle.Fill, BackColor = Theme.Panel };
                var name = new Label
                {
                    Text = PlayerStatNames[index],
                    ForeColor = Theme.Muted,
                    Font = Theme.SmallBoldFont,
                    AutoSize = true,
                    Location = new Point(2, 3)
                };
                _statValues[index].Location = new Point(2, 19);
                _statValues[index].AutoSize = true;
                cell.Controls.Add(name);
                cell.Controls.Add(_statValues[index]);
                grid.Controls.Add(cell, column, row);
            }
        }
        card.Controls.Add(grid);
    }

    private void BuildFreedomCard(Control parent)
    {
        var card = NewCard(parent, 410, 92);
        AddCaption(card, "FINANCIAL FREEDOM METER", 14, 9);
        _freedomText.Location = new Point(14, 30);
        _freedomText.AutoSize = true;
        card.Controls.Add(_freedomText);
        _freedomMeter.Location = new Point(14, 54);
        _freedomMeter.Size = new Size(380, 13);
        _freedomMeter.Maximum = 100;
        card.Controls.Add(_freedomMeter);
        _dreamText.Location = new Point(14, 70);
        _dreamText.AutoSize = true;
        card.Controls.Add(_dreamText);
    }

    private void BuildActionCard(Control parent)
    {
        var card = NewCard(parent, 410, 140);
        AddCaption(card, "YOUR MOVE", 14, 8);
        _rollButton.SetBounds(14, 32, 184, 42);
        _nextPlayerButton.SetBounds(208, 32, 186, 42);
        _loanButton.SetBounds(14, 83, 184, 40);
        _repayButton.SetBounds(208, 83, 186, 40);
        card.Controls.AddRange([_rollButton, _nextPlayerButton, _loanButton, _repayButton]);
    }

    private void BuildPortfolioCard(Control parent)
    {
        var card = NewCard(parent, 410, 112);
        AddCaption(card, "ASSETS & LIABILITIES", 14, 8);
        _assets.Location = new Point(12, 29);
        _assets.Size = new Size(382, 72);
        _assets.BackColor = Theme.Panel;
        _assets.ForeColor = Theme.Text;
        _assets.BorderStyle = BorderStyle.None;
        _assets.IntegralHeight = false;
        card.Controls.Add(_assets);
        _statementButton.SetBounds(227, 7, 167, 28);
        card.Controls.Add(_statementButton);
    }

    private void BuildCreatorFundCard(Control parent)
    {
        var card = NewCard(parent, 410, 91);
        AddCaption(card, "PERSONAL CREATOR GOAL · BMW FUND", 14, 8);
        _creatorFundText.Location = new Point(14, 31);
        _creatorFundText.AutoSize = true;
        card.Controls.Add(_creatorFundText);
        _creatorFundMeter.Location = new Point(14, 55);
        _creatorFundMeter.Size = new Size(245, 14);
        _creatorFundMeter.Maximum = 10_000;
        card.Controls.Add(_creatorFundMeter);
        _creatorFundButton.SetBounds(270, 47, 124, 32);
        card.Controls.Add(_creatorFundButton);
    }

    private void BuildActivityCard(Control parent)
    {
        var card = NewCard(parent, 410, 132);
        AddCaption(card, "TABLE LOG", 14, 8);
        _activity.Location = new Point(12, 29);
        _activity.Size = new Size(382, 91);
        _activity.BackColor = Theme.Panel;
        _activity.ForeColor = Theme.Text;
        _activity.BorderStyle = BorderStyle.None;
        _activity.IntegralHeight = false;
        card.Controls.Add(_activity);
    }

    private void BuildStatusCard(Control parent)
    {
        var card = NewCard(parent, 410, 54);
        _status.Location = new Point(14, 10);
        _status.Size = new Size(380, 38);
        _status.AutoEllipsis = true;
        card.Controls.Add(_status);
    }

    private void RefreshView()
    {
        _board.Game = _game;
        _board.Invalidate();
        if (_game is null)
        {
            _playerName.Text = "Choose a profession to begin";
            _playerPhase.Text = "1–5 players · pass-and-play · 24 spaces per track";
            for (var i = 0; i < _statValues.Length; i++)
            {
                _statValues[i].Text = "—";
            }
            _freedomText.Text = "Start a game to see your progress.";
            _freedomMeter.Value = 0;
            _dreamText.Text = string.Empty;
            _assets.Items.Clear();
            _rollButton.Enabled = false;
            _nextPlayerButton.Enabled = false;
            _loanButton.Enabled = false;
            _repayButton.Enabled = false;
            _statementButton.Enabled = false;
            _loadButton.Enabled = _databaseReady;
            _saveButton.Enabled = false;
            RefreshCreatorFund();
            return;
        }

        var player = _game.CurrentPlayer;
        _playerName.Text = $"{player.Name}  ·  {player.Profile.Profession}";
        _playerPhase.Text = $"{player.Profile.City}  ·  {player.Track.ToString().ToUpperInvariant()}";
        var stats = new[]
        {
            GameEngine.Money(player.Track == TrackKind.RatRace ? player.Salary : 0),
            GameEngine.Money(player.PassiveIncome),
            GameEngine.Money(player.MonthlyLivingExpenses),
            GameEngine.Money(player.MonthlyDebtPayments),
            GameEngine.Money(player.TotalDebt),
            GameEngine.Money(player.Cash),
            GameEngine.Money(player.NetWorth),
            GameEngine.Money(player.MonthlyNetCashflow)
        };
        for (var index = 0; index < stats.Length; index++)
        {
            _statValues[index].Text = stats[index];
            _statValues[index].ForeColor =
                index == 7 && player.MonthlyNetCashflow < 0 ? Theme.Danger : Theme.Text;
        }

        if (player.Track == TrackKind.RatRace)
        {
            var ratio = player.MonthlyOutgoings == 0
                ? 1m
                : Math.Clamp(player.PassiveIncome / player.MonthlyOutgoings, 0m, 1m);
            _freedomMeter.Value = (int)(ratio * 100);
            _freedomText.Text =
                $"{GameEngine.Money(player.PassiveIncome)} passive / {GameEngine.Money(player.MonthlyOutgoings)} outgoings";
        }
        else
        {
            var ratio = Math.Clamp(player.PassiveIncome / GameContent.FastTrackWinCashflow, 0m, 1m);
            _freedomMeter.Value = (int)(ratio * 100);
            _freedomText.Text =
                $"{GameEngine.Money(player.PassiveIncome)} / {GameEngine.Money(GameContent.FastTrackWinCashflow)} passive-income win goal";
        }
        _dreamText.Text = $"Dream: {player.Dream.Title}  ·  {GameEngine.Money(player.Dream.Price)}";

        _assets.Items.Clear();
        foreach (var asset in player.Assets)
        {
            _assets.Items.Add(
                $"{asset.Name} · +{GameEngine.Money(asset.MonthlyCashflow)}/mo · {GameEngine.Money(asset.MarketValue)}");
        }
        foreach (var liability in player.Liabilities)
        {
            _assets.Items.Add(
                $"{liability.Name} · −{GameEngine.Money(liability.Principal)}");
        }

        _rollButton.Enabled = !_game.TurnRolled && _game.Winner is null;
        _nextPlayerButton.Enabled = _game.TurnRolled && _game.Winner is null;
        _loanButton.Enabled = !_game.TurnRolled && _game.Winner is null;
        _repayButton.Enabled = !_game.TurnRolled
            && player.BankLoanBalance >= 1_000m
            && player.Cash >= 1_000m
            && _game.Winner is null;
        _statementButton.Enabled = true;
        _loadButton.Enabled = _databaseReady;
        _saveButton.Enabled = _databaseReady;
        RefreshCreatorFund();
    }

    private void StartNewGame(object? sender, EventArgs e)
    {
        if (_game is not null && _game.Winner is null
            && MessageBox.Show(this, "Start a new table and leave this game?",
                "New game", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes)
        {
            return;
        }

        using var dialog = new SetupDialog();
        if (dialog.ShowDialog(this) != DialogResult.OK)
        {
            return;
        }

        _game = new GameEngine(dialog.Players);
        _activity.Items.Clear();
        _status.Text = "New table started. Roll once per turn; loans are available before your roll.";
        RefreshView();
    }

    private void RollTurn(object? sender, EventArgs e)
    {
        if (_game is null)
        {
            return;
        }

        try
        {
            var result = _game.Roll();
            _status.Text = result.Summary;
            AddActivity(result.Summary);
            if (result.Deal is not null)
            {
                ResolveDeal(result.Deal);
            }
            if (result.Event is not null)
            {
                ResolveEvent(result.Event);
            }
            if (result.Dream is not null)
            {
                ResolveDream(result.Dream);
            }
            if (_game.Winner is not null)
            {
                MessageBox.Show(this,
                    $"{_game.Winner.Name} has reached the goal.\n\n{_game.WinReason}",
                    "Game won", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
        }
        catch (InvalidOperationException error)
        {
            MessageBox.Show(this, error.Message, "Turn could not be completed",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        catch (ArgumentOutOfRangeException error)
        {
            MessageBox.Show(this, error.Message, "Invalid game action",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }

        RefreshView();
    }

    private void ResolveDeal(DealCard deal)
    {
        if (_game is null)
        {
            return;
        }
        var player = _game.CurrentPlayer;
        var shortfall = Math.Max(0m, deal.DownPayment - player.Cash);
        var details = $"{deal.Description}\n\n"
            + $"Price: {GameEngine.Money(deal.Price)}\n"
            + $"Down payment: {GameEngine.Money(deal.DownPayment)}\n"
            + $"Financed portion: {GameEngine.Money(deal.Price - deal.DownPayment)}\n"
            + $"Scenario cash flow: +{GameEngine.Money(deal.MonthlyCashflow)} / month";
        if (shortfall > 0)
        {
            var requiredLoan = decimal.Ceiling(shortfall / 1_000m) * 1_000m;
            details += $"\n\nCash shortfall: {GameEngine.Money(shortfall)}."
                + $"\nA {GameEngine.Money(requiredLoan)} emergency bank loan is required.";
        }

        if (MessageBox.Show(this, $"{deal.Title}\n\n{details}\n\nBuy this deal?",
            deal.Size == DealSize.Small ? "Small deal" : "Investment opportunity",
            MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes)
        {
            _game.PassPendingDeal();
            _status.Text = $"Passed on {deal.Title}.";
            return;
        }

        try
        {
            _game.BuyPendingDeal(borrowForDownPayment: shortfall > 0);
            _status.Text = $"Bought {deal.Title}; added {GameEngine.Money(deal.MonthlyCashflow)} / month to passive income.";
        }
        catch (InvalidOperationException error)
        {
            MessageBox.Show(this, error.Message, "Deal not completed",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    private void ResolveEvent(EventCard card)
    {
        if (_game is null)
        {
            return;
        }

        if (card.Id == "charity-choice")
        {
            var donation = decimal.Round(_game.CurrentPlayer.Salary * 0.10m, 0);
            var answer = MessageBox.Show(this,
                $"{card.Description}\n\nOne-time donation: {GameEngine.Money(donation)}.",
                "Charity space", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
            _game.ResolveCharity(answer == DialogResult.Yes);
            _status.Text = answer == DialogResult.Yes
                ? "Charity accepted: the next three rolls get one extra die."
                : "Charity declined.";
            return;
        }

        if (card.Id == "buyer-offer")
        {
            ResolveBuyerOffer(card);
            return;
        }

        MessageBox.Show(this,
            $"{card.Title}\n\n{card.Description}\n\nScenario amount: {GameEngine.Money(card.Amount)}.",
            card.Title, MessageBoxButtons.OK, MessageBoxIcon.Information);
        _status.Text = $"{card.Title}: {card.Description}";
    }

    private void ResolveBuyerOffer(EventCard card)
    {
        if (_game is null)
        {
            return;
        }
        var player = _game.CurrentPlayer;
        if (player.Assets.Count == 0)
        {
            MessageBox.Show(this, $"{card.Description}\n\nNo holdings are available to sell.",
                card.Title, MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        var asset = player.Assets.OrderByDescending(item => item.MarketValue).First();
        var offer = decimal.Round(asset.MarketValue * (1 + card.Amount / 100m), 0);
        if (MessageBox.Show(this,
            $"{card.Description}\n\nOffer for {asset.Name}: {GameEngine.Money(offer)}\n"
            + $"Remaining financing: {GameEngine.Money(asset.Financing?.Principal ?? 0m)}\n"
            + $"Monthly income given up: {GameEngine.Money(asset.MonthlyCashflow)}\n\nSell the highest-value holding?",
            card.Title, MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes)
        {
            return;
        }

        _game.SellAsset(asset, card.Amount);
        _status.Text = $"Sold {asset.Name} for {GameEngine.Money(offer)} before clearing its financing.";
    }

    private void ResolveDream(DreamCard dream)
    {
        if (_game is null)
        {
            return;
        }
        var player = _game.CurrentPlayer;
        if (player.Cash < dream.Price)
        {
            MessageBox.Show(this,
                $"{dream.Title} costs {GameEngine.Money(dream.Price)}.\n"
                + $"You have {GameEngine.Money(player.Cash)}; "
                + $"you need {GameEngine.Money(dream.Price - player.Cash)} more.",
                "Dream space", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        if (MessageBox.Show(this,
            $"Fund {dream.Title} for {GameEngine.Money(dream.Price)}?",
            "Dream space", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes)
        {
            _game.BuyDream();
        }
    }

    private void NextPlayer(object? sender, EventArgs e)
    {
        if (_game is null)
        {
            return;
        }
        try
        {
            _game.EndTurn();
            var text = $"{_game.CurrentPlayer.Name}'s turn. Take or repay a loan before rolling.";
            _status.Text = text;
            AddActivity(text);
        }
        catch (InvalidOperationException error)
        {
            MessageBox.Show(this, error.Message, "Turn could not end",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        RefreshView();
    }

    private void TakeLoan(object? sender, EventArgs e)
    {
        if (_game is null)
        {
            return;
        }
        var amount = PromptAmount(
            "Bank Loan Center",
            "Borrow in multiples of ₹1,000. In-game interest is 10% per month.",
            1_000m,
            100_000_000m,
            1_000m);
        if (amount is null)
        {
            return;
        }
        try
        {
            _game.BorrowBankLoan(amount.Value);
            _status.Text =
                $"Borrowed {GameEngine.Money(amount.Value)}; monthly interest is {GameEngine.Money(amount.Value * GameContent.BankLoanMonthlyInterestRate)}.";
            AddActivity(_status.Text);
        }
        catch (ArgumentOutOfRangeException error)
        {
            MessageBox.Show(this, error.Message, "Loan not completed",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        RefreshView();
    }

    private void RepayLoan(object? sender, EventArgs e)
    {
        if (_game is null)
        {
            return;
        }
        var player = _game.CurrentPlayer;
        var maximum = Math.Min(player.Cash, player.BankLoanBalance);
        maximum = decimal.Floor(maximum / 1_000m) * 1_000m;
        if (maximum < 1_000m)
        {
            MessageBox.Show(this, "At least ₹1,000 of cash and bank-loan balance is required.",
                "Repay loan", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        var amount = PromptAmount(
            "Repay Bank Loan",
            $"Available cash: {GameEngine.Money(player.Cash)}\n"
            + $"Bank-loan balance: {GameEngine.Money(player.BankLoanBalance)}\n"
            + "Enter a principal repayment in ₹1,000 units.",
            1_000m,
            maximum,
            1_000m);
        if (amount is null)
        {
            return;
        }
        try
        {
            _game.RepayBankLoan(amount.Value);
            _status.Text =
                $"Repaid {GameEngine.Money(amount.Value)}. The next month's interest will be lower.";
            AddActivity(_status.Text);
        }
        catch (InvalidOperationException error)
        {
            MessageBox.Show(this, error.Message, "Repayment not completed",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        catch (ArgumentOutOfRangeException error)
        {
            MessageBox.Show(this, error.Message, "Invalid repayment",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        RefreshView();
    }

    private void ShowStatement(object? sender, EventArgs e)
    {
        if (_game is not null)
        {
            using var dialog = new FinancialStatementDialog(_game.CurrentPlayer);
            dialog.ShowDialog(this);
        }
    }

    private void ShowRules(object? sender, EventArgs e)
    {
        MessageBox.Show(this,
            "RAT RACE\n"
            + "Roll one die per turn, resolve the space, and collect monthly net cash flow when crossing Payday. "
            + "Small deals cost up to ₹5,000; Big Deals start at ₹6,000. Charity optionally costs 10% of salary "
            + "and gives one extra die on the next three turns.\n\n"
            + "FAST TRACK\n"
            + "Passive income must exceed monthly outgoings. Entry multiplies cash by 100 and clears consumer "
            + "debt. Roll two dice, or three while a charity bonus is active. Buy your selected dream on a Dream "
            + "space, or win when passive income reaches ₹50,000 per month.\n\n"
            + "LOANS\n"
            + "Bank loans are in ₹1,000 units and accrue 10% monthly interest in this game. Emergency loans "
            + "prevent negative cash. These are game rules, not real-world lending terms.\n\n"
            + "The Indian professions and their salary/debt figures come from the supplied project summary. "
            + "Living budgets and card returns are scenario assumptions, not market forecasts or financial advice.",
            "How to play Life Capital", MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    private async void SaveGame(object? sender, EventArgs e)
    {
        if (_game is null || !_databaseReady)
        {
            return;
        }
        try
        {
            await _store.SaveAsync(_game);
            var text = $"Game saved locally at {DateTime.Now:t}.";
            _status.Text = text;
            AddActivity(text);
        }
        catch (SqliteException error)
        {
            MessageBox.Show(this, error.Message, "SQLite save failed",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        catch (IOException error)
        {
            MessageBox.Show(this, error.Message, "Save file error",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        catch (UnauthorizedAccessException error)
        {
            MessageBox.Show(this, error.Message, "Save file permission",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        RefreshView();
    }

    private async void LoadGame(object? sender, EventArgs e)
    {
        if (!_databaseReady)
        {
            return;
        }
        if (_game is not null
            && MessageBox.Show(this, "Replace the current table? Unsaved progress will be lost.",
                "Load saved game", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes)
        {
            return;
        }

        try
        {
            var loaded = await _store.LoadAsync();
            if (loaded is null)
            {
                MessageBox.Show(this, "There is no saved game yet.", "Load saved game",
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            _game = loaded;
            _activity.Items.Clear();
            _status.Text = "Saved game restored. Continue the current player's turn.";
            AddActivity(_status.Text);
        }
        catch (SqliteException error)
        {
            MessageBox.Show(this, error.Message, "SQLite load failed",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        catch (InvalidDataException error)
        {
            MessageBox.Show(this, error.Message, "Saved game could not be restored",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        catch (JsonException error)
        {
            MessageBox.Show(this, error.Message, "Saved game data is invalid",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        catch (IOException error)
        {
            MessageBox.Show(this, error.Message, "Save file error",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        catch (UnauthorizedAccessException error)
        {
            MessageBox.Show(this, error.Message, "Save file permission",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        RefreshView();
    }

    private async void InitializeDatabase(object? sender, EventArgs e)
    {
        try
        {
            await _store.InitializeAsync();
            _creatorFund = await _store.GetCreatorFundAsync();
            _databaseReady = true;
            _status.Text = "Local SQLite save and creator-fund database is ready.";
        }
        catch (SqliteException error)
        {
            _status.Text = "SQLite could not be initialized.";
            MessageBox.Show(this, error.Message, "Local database error",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        catch (IOException error)
        {
            _status.Text = "The local data folder could not be created.";
            MessageBox.Show(this, error.Message, "Local data-folder error",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        catch (UnauthorizedAccessException error)
        {
            _status.Text = "The local data folder is not writable.";
            MessageBox.Show(this, error.Message, "Local data-folder permission",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        RefreshView();
    }

    private async void AddCreatorFundContribution(object? sender, EventArgs e)
    {
        if (!_databaseReady)
        {
            MessageBox.Show(this, "The local SQLite database is unavailable.",
                "Contribution not saved", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }
        var amount = PromptAmount(
            "Add to the BMW Creator Fund",
            $"Current balance: {GameEngine.Money(_creatorFund?.Saved ?? 0m)}",
            1m,
            5_500_000m,
            1_000m);
        if (amount is null)
        {
            return;
        }
        try
        {
            _creatorFund = await _store.AddCreatorFundContributionAsync(amount.Value);
            _status.Text = $"Added {GameEngine.Money(amount.Value)} to the local creator-fund tracker.";
        }
        catch (SqliteException error)
        {
            MessageBox.Show(this, error.Message, "Contribution not saved",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        catch (IOException error)
        {
            MessageBox.Show(this, error.Message, "Contribution file error",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        catch (UnauthorizedAccessException error)
        {
            MessageBox.Show(this, error.Message, "Contribution file permission",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        RefreshView();
    }

    private void RefreshCreatorFund()
    {
        if (_creatorFund is null)
        {
            _creatorFundText.Text = _databaseReady ? "Fund data unavailable." : "Opening local database…";
            _creatorFundMeter.Value = 0;
            _creatorFundButton.Enabled = _databaseReady;
            return;
        }

        var ratio = Math.Clamp(_creatorFund.Saved / _creatorFund.Target, 0m, 1m);
        _creatorFundText.Text =
            $"{GameEngine.Money(_creatorFund.Saved)} / {GameEngine.Money(_creatorFund.Target)}  ·  {ratio:P2}";
        _creatorFundMeter.Value = (int)(ratio * _creatorFundMeter.Maximum);
        _creatorFundButton.Enabled = _databaseReady;
    }

    private void AddActivity(string entry)
    {
        _activity.Items.Insert(0, $"{DateTime.Now:HH:mm}  ·  {entry}");
        while (_activity.Items.Count > 10)
        {
            _activity.Items.RemoveAt(_activity.Items.Count - 1);
        }
    }

    private decimal? PromptAmount(
        string title,
        string description,
        decimal minimum,
        decimal maximum,
        decimal increment)
    {
        using var dialog = new Form
        {
            Text = title,
            StartPosition = FormStartPosition.CenterParent,
            FormBorderStyle = FormBorderStyle.FixedDialog,
            MaximizeBox = false,
            MinimizeBox = false,
            ClientSize = new Size(410, 190),
            BackColor = Theme.Background,
            ForeColor = Theme.Text,
            Font = Theme.BodyFont
        };
        var prompt = new Label
        {
            Text = description,
            Location = new Point(18, 16),
            Size = new Size(374, 68),
            ForeColor = Theme.Text
        };
        var input = new NumericUpDown
        {
            Location = new Point(18, 94),
            Size = new Size(374, 30),
            Minimum = minimum,
            Maximum = maximum,
            Increment = increment,
            ThousandsSeparator = true,
            DecimalPlaces = 0,
            BackColor = Theme.Panel,
            ForeColor = Theme.Text
        };
        var accept = new Button
        {
            Text = "CONFIRM",
            DialogResult = DialogResult.OK,
            Location = new Point(254, 140),
            Size = new Size(138, 34),
            BackColor = Theme.Accent,
            ForeColor = Theme.Background,
            FlatStyle = FlatStyle.Flat
        };
        var cancel = new Button
        {
            Text = "CANCEL",
            DialogResult = DialogResult.Cancel,
            Location = new Point(108, 140),
            Size = new Size(138, 34),
            BackColor = Theme.PanelRaised,
            ForeColor = Theme.Text,
            FlatStyle = FlatStyle.Flat
        };
        dialog.Controls.AddRange([prompt, input, cancel, accept]);
        dialog.AcceptButton = accept;
        dialog.CancelButton = cancel;
        return dialog.ShowDialog(this) == DialogResult.OK ? input.Value : null;
    }

    private static Panel NewCard(Control parent, int width, int height)
    {
        var card = new Panel
        {
            Width = width,
            Height = height,
            BackColor = Theme.Panel,
            Margin = new Padding(0, 0, 0, 9)
        };
        parent.Controls.Add(card);
        return card;
    }

    private static void AddCaption(Control parent, string text, int x, int y)
    {
        parent.Controls.Add(new Label
        {
            Text = text,
            ForeColor = Theme.Gold,
            Font = Theme.SmallBoldFont,
            AutoSize = true,
            Location = new Point(x, y)
        });
    }

    private static Label NewValueLabel(
        float size,
        FontStyle style,
        Color? color = null) => new()
    {
        Font = new Font("Segoe UI", size, style),
        ForeColor = color ?? Theme.Text,
        AutoEllipsis = true
    };

    private static Button ActionButton(
        string text,
        EventHandler handler,
        Color background,
        Color foreground)
    {
        var button = new Button
        {
            Text = text,
            BackColor = background,
            ForeColor = foreground,
            FlatStyle = FlatStyle.Flat,
            Font = Theme.ButtonFont,
            Cursor = Cursors.Hand,
            Margin = new Padding(4),
            UseVisualStyleBackColor = false
        };
        button.FlatAppearance.BorderSize = 0;
        button.Click += handler;
        return button;
    }
}
