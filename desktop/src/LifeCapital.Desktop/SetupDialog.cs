using LifeCapital.Core;

namespace LifeCapital.Desktop;

internal sealed class SetupDialog : Form
{
    private readonly NumericUpDown _playerCount = new();
    private readonly TableLayoutPanel _playerRows = new();
    private readonly List<(ComboBox Profession, ComboBox Dream)> _choices = [];

    public SetupDialog()
    {
        Text = "Set up Life Capital";
        StartPosition = FormStartPosition.CenterParent;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        ClientSize = new Size(800, 570);
        BackColor = Theme.Background;
        ForeColor = Theme.Text;
        Font = Theme.BodyFont;

        var title = new Label
        {
            Text = "Choose your players",
            Font = Theme.TitleFont,
            ForeColor = Theme.Accent,
            AutoSize = true,
            Location = new Point(28, 22)
        };
        Controls.Add(title);

        var note = new Label
        {
            Text = "Five India-based professions · scenario budgets are estimates, not financial advice.",
            ForeColor = Theme.Muted,
            AutoSize = true,
            Location = new Point(30, 65)
        };
        Controls.Add(note);

        _playerCount.Minimum = 1;
        _playerCount.Maximum = 5;
        _playerCount.Value = 1;
        _playerCount.Location = new Point(30, 108);
        _playerCount.Width = 100;
        _playerCount.BackColor = Theme.Panel;
        _playerCount.ForeColor = Theme.Text;
        _playerCount.ValueChanged += (_, _) => BuildRows();
        Controls.Add(_playerCount);

        Controls.Add(new Label
        {
            Text = "Players",
            AutoSize = true,
            ForeColor = Theme.Text,
            Location = new Point(142, 111)
        });

        _playerRows.Location = new Point(28, 150);
        _playerRows.Size = new Size(744, 330);
        _playerRows.ColumnCount = 3;
        _playerRows.RowCount = 1;
        _playerRows.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 90));
        _playerRows.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 55));
        _playerRows.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 45));
        _playerRows.RowStyles.Add(new RowStyle(SizeType.Absolute, 42));
        Controls.Add(_playerRows);
        BuildRows();

        var start = new Button
        {
            Text = "START GAME",
            Location = new Point(610, 505),
            Size = new Size(160, 42),
            BackColor = Theme.Accent,
            ForeColor = Theme.Background,
            FlatStyle = FlatStyle.Flat,
            Font = Theme.ButtonFont
        };
        start.FlatAppearance.BorderSize = 0;
        start.Click += (_, _) => CreatePlayers();
        Controls.Add(start);

        var cancel = new Button
        {
            Text = "CANCEL",
            Location = new Point(445, 505),
            Size = new Size(150, 42),
            BackColor = Theme.Panel,
            ForeColor = Theme.Text,
            FlatStyle = FlatStyle.Flat
        };
        cancel.FlatAppearance.BorderSize = 0;
        cancel.Click += (_, _) => DialogResult = DialogResult.Cancel;
        Controls.Add(cancel);
    }

    public IReadOnlyList<Player> Players { get; private set; } = [];

    private void BuildRows()
    {
        _playerRows.SuspendLayout();
        _playerRows.Controls.Clear();
        _playerRows.RowStyles.Clear();
        _choices.Clear();
        _playerRows.RowCount = (int)_playerCount.Value + 1;

        AddHeader("PLAYER", 0);
        AddHeader("PROFESSION", 1);
        AddHeader("DREAM", 2);

        for (var index = 0; index < _playerCount.Value; index++)
        {
            _playerRows.RowStyles.Add(new RowStyle(SizeType.Absolute, 54));
            _playerRows.Controls.Add(new Label
            {
                Text = $"PLAYER {index + 1}",
                TextAlign = ContentAlignment.MiddleLeft,
                ForeColor = Theme.Accent,
                AutoSize = true
            }, 0, index + 1);

            var profession = NewComboBox();
            profession.DisplayMember = nameof(ProfessionProfile.Name);
            profession.Items.AddRange(GameContent.Professions.Cast<object>().ToArray());
            profession.SelectedIndex = index % GameContent.Professions.Count;
            _playerRows.Controls.Add(profession, 1, index + 1);

            var dream = NewComboBox();
            dream.DisplayMember = nameof(DreamCard.Title);
            dream.Items.AddRange(GameContent.Dreams.Cast<object>().ToArray());
            dream.SelectedIndex = index % GameContent.Dreams.Count;
            _playerRows.Controls.Add(dream, 2, index + 1);
            _choices.Add((profession, dream));
        }

        _playerRows.ResumeLayout();
    }

    private void CreatePlayers()
    {
        var players = new List<Player>(_choices.Count);
        foreach (var choice in _choices)
        {
            if (choice.Profession.SelectedItem is not ProfessionProfile profile
                || choice.Dream.SelectedItem is not DreamCard dream)
            {
                MessageBox.Show(this, "Choose a profession and a dream for each player.",
                    "Incomplete setup", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            players.Add(new Player(profile, dream));
        }

        Players = players;
        DialogResult = DialogResult.OK;
    }

    private void AddHeader(string text, int column)
    {
        _playerRows.Controls.Add(new Label
        {
            Text = text,
            ForeColor = Theme.Muted,
            Font = Theme.SmallBoldFont,
            TextAlign = ContentAlignment.MiddleLeft,
            Dock = DockStyle.Fill
        }, column, 0);
    }

    private static ComboBox NewComboBox() => new()
    {
        Dock = DockStyle.Fill,
        DropDownStyle = ComboBoxStyle.DropDownList,
        BackColor = Theme.Panel,
        ForeColor = Theme.Text,
        FlatStyle = FlatStyle.Flat,
        Margin = new Padding(6)
    };
}
