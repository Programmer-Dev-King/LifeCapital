using LifeCapital.Core;

namespace LifeCapital.Desktop;

internal sealed class FinancialStatementDialog : Form
{
    public FinancialStatementDialog(Player player)
    {
        Text = $"Financial statement · {player.Name}";
        StartPosition = FormStartPosition.CenterParent;
        ClientSize = new Size(840, 620);
        MinimumSize = new Size(720, 500);
        BackColor = Theme.Background;
        ForeColor = Theme.Text;
        Font = Theme.BodyFont;

        var tabs = new TabControl
        {
            Dock = DockStyle.Fill,
            Padding = new Point(14, 6)
        };
        tabs.TabPages.Add(CreateCashflowTab(player));
        tabs.TabPages.Add(CreateBalanceTab(player));
        tabs.TabPages.Add(CreateLedgerTab(player));
        Controls.Add(tabs);
    }

    private static TabPage CreateCashflowTab(Player player)
    {
        var page = NewTab("Monthly cash flow");
        var salary = player.Track == TrackKind.RatRace ? player.Salary : 0m;
        var debtPayments = player.MonthlyDebtPayments;
        var rows = new (string Label, decimal Amount)[]
        {
            ("Salary income", salary),
            ("Passive asset income", player.PassiveIncome),
            ("Monthly living expenses", -player.MonthlyLivingExpenses),
            ("Consumer-debt payments", -player.Liabilities
                .Where(item => item.Kind == LiabilityKind.Consumer)
                .Sum(item => Math.Min(item.Principal, item.MonthlyPayment))),
            ("Bank and asset-loan interest", -player.Liabilities
                .Where(item => item.Kind != LiabilityKind.Consumer)
                .Sum(item => decimal.Round(item.Principal * item.MonthlyInterestRate, 0))),
            ("Net monthly cash flow", player.MonthlyNetCashflow)
        };
        AddGrid(page, ["Category", "Monthly amount"],
            rows.Select(row => new[] { row.Label, GameEngine.Money(row.Amount) }));
        return page;
    }

    private static TabPage CreateBalanceTab(Player player)
    {
        var page = NewTab("Balance sheet");
        string[][] rows =
        [
            ["Cash", GameEngine.Money(player.Cash)],
            ["Investment assets", GameEngine.Money(player.Assets.Sum(asset => asset.MarketValue))],
            ["Total assets", GameEngine.Money(player.Cash + player.Assets.Sum(asset => asset.MarketValue))],
            ["Consumer debts", GameEngine.Money(player.ConsumerDebt)],
            ["Bank loans", GameEngine.Money(player.BankLoanBalance)],
            ["Asset financing", GameEngine.Money(player.AssetDebt)],
            ["Total liabilities", GameEngine.Money(player.TotalDebt)],
            ["Net worth", GameEngine.Money(player.NetWorth)]
        ];
        AddGrid(page, ["Account", "Balance"], rows);
        return page;
    }

    private static TabPage CreateLedgerTab(Player player)
    {
        var page = NewTab("Double-entry journal");
        var rows = player.Ledger
            .TakeLast(250)
            .Reverse()
            .Select(entry => new[]
            {
                entry.PostedAt.ToLocalTime().ToString("dd MMM HH:mm"),
                entry.Description,
                entry.DebitAccount,
                entry.CreditAccount,
                GameEngine.Money(entry.Amount)
            });
        AddGrid(page, ["Date", "Description", "Debit", "Credit", "Amount"], rows);
        return page;
    }

    private static TabPage NewTab(string text)
    {
        var tab = new TabPage(text)
        {
            BackColor = Theme.Background,
            ForeColor = Theme.Text,
            Padding = new Padding(12)
        };
        return tab;
    }

    private static void AddGrid(
        TabPage page,
        string[] columns,
        IEnumerable<string[]> rows)
    {
        var grid = new DataGridView
        {
            Dock = DockStyle.Fill,
            ReadOnly = true,
            AllowUserToAddRows = false,
            AllowUserToDeleteRows = false,
            AllowUserToResizeRows = false,
            AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
            BackgroundColor = Theme.Panel,
            BorderStyle = BorderStyle.None,
            EnableHeadersVisualStyles = false,
            RowHeadersVisible = false,
            SelectionMode = DataGridViewSelectionMode.FullRowSelect,
            GridColor = Color.FromArgb(49, 64, 77)
        };
        grid.ColumnHeadersDefaultCellStyle.BackColor = Theme.PanelRaised;
        grid.ColumnHeadersDefaultCellStyle.ForeColor = Theme.Text;
        grid.ColumnHeadersDefaultCellStyle.Font = Theme.SmallBoldFont;
        grid.DefaultCellStyle.BackColor = Theme.Panel;
        grid.DefaultCellStyle.ForeColor = Theme.Text;
        grid.DefaultCellStyle.SelectionBackColor = Color.FromArgb(39, 80, 74);
        grid.DefaultCellStyle.SelectionForeColor = Theme.Text;
        grid.DefaultCellStyle.Padding = new Padding(5);
        foreach (var column in columns)
        {
            grid.Columns.Add(column, column);
        }
        foreach (var row in rows)
        {
            grid.Rows.Add(row);
        }
        page.Controls.Add(grid);
    }
}
