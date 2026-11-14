using System.Drawing.Drawing2D;
using System.ComponentModel;
using LifeCapital.Core;

namespace LifeCapital.Desktop;

internal sealed class BoardControl : Control
{
    private static readonly Color[] SpaceColors =
    [
        Color.FromArgb(33, 99, 83),
        Color.FromArgb(116, 87, 47),
        Color.FromArgb(136, 88, 52),
        Color.FromArgb(57, 82, 126),
        Color.FromArgb(129, 70, 81),
        Color.FromArgb(77, 97, 63),
        Color.FromArgb(153, 94, 60),
        Color.FromArgb(83, 91, 126),
        Color.FromArgb(44, 113, 101),
        Color.FromArgb(121, 92, 48),
        Color.FromArgb(61, 93, 132)
    ];

    public BoardControl()
    {
        DoubleBuffered = true;
        ResizeRedraw = true;
        BackColor = Theme.Wood;
        MinimumSize = new Size(620, 620);
    }

    [Browsable(false)]
    [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
    public GameEngine? Game { get; set; }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        var graphics = e.Graphics;
        graphics.SmoothingMode = SmoothingMode.AntiAlias;
        graphics.TextRenderingHint = System.Drawing.Text.TextRenderingHint.ClearTypeGridFit;
        graphics.Clear(Theme.Wood);

        if (Game is null)
        {
            DrawWelcome(graphics);
            return;
        }

        var center = new PointF(ClientSize.Width / 2f, ClientSize.Height / 2f);
        var radius = Math.Min(ClientSize.Width, ClientSize.Height) * 0.39f;
        DrawTrack(graphics, center, radius, TrackKind.FastTrack);
        DrawTrack(graphics, center, radius * 0.64f, TrackKind.RatRace);
        DrawCenter(graphics, center);
        DrawPawns(graphics, center, radius);
        DrawLegend(graphics);
    }

    private void DrawTrack(Graphics graphics, PointF center, float radius, TrackKind track)
    {
        using var ringPen = new Pen(track == TrackKind.RatRace ? Color.FromArgb(127, 92, 64) : Color.FromArgb(82, 138, 119), 2f);
        graphics.DrawEllipse(ringPen, center.X - radius, center.Y - radius, radius * 2f, radius * 2f);

        var spaces = GameEngine.SpacesFor(track);
        var current = Game!.CurrentPlayer;
        var tileWidth = track == TrackKind.FastTrack ? 70f : 60f;
        var tileHeight = track == TrackKind.FastTrack ? 40f : 34f;
        for (var index = 0; index < spaces.Count; index++)
        {
            var space = spaces[index];
            var angle = -Math.PI / 2 + Math.Tau * index / spaces.Count;
            var point = new PointF(
                center.X + radius * (float)Math.Cos(angle),
                center.Y + radius * (float)Math.Sin(angle));
            var active = current.Track == track && current.Position == index;
            var rectangle = new RectangleF(
                point.X - tileWidth / 2f,
                point.Y - tileHeight / 2f,
                tileWidth,
                tileHeight);
            var color = SpaceColors[(int)space.Kind];

            using var brush = new SolidBrush(color);
            using var outline = new Pen(active ? Theme.Text : Color.FromArgb(27, 24, 22), active ? 2f : 1f);
            using var path = RoundedRectangle(rectangle, 7f);
            graphics.FillPath(brush, path);
            graphics.DrawPath(outline, path);

            var label = ShortLabel(space.Kind);
            var fontSize = track == TrackKind.FastTrack ? 6.7f : 6.2f;
            using var font = new Font("Segoe UI", fontSize, FontStyle.Bold);
            using var textBrush = new SolidBrush(Theme.Text);
            using var format = new StringFormat
            {
                Alignment = StringAlignment.Center,
                LineAlignment = StringAlignment.Center
            };
            graphics.DrawString($"{space.Index + 1:00}\n{label}", font, textBrush, rectangle, format);
        }
    }

    private void DrawPawns(Graphics graphics, PointF center, float radius)
    {
        foreach (var (player, playerIndex) in Game!.Players.Select((player, index) => (player, index)))
        {
            var trackRadius = player.Track == TrackKind.FastTrack ? radius : radius * 0.64f;
            var spaces = GameEngine.SpacesFor(player.Track);
            var angle = -Math.PI / 2 + Math.Tau * player.Position / spaces.Count;
            var angleOffset = (playerIndex - (Game.Players.Count - 1) / 2f) * 0.06f;
            angle += angleOffset;
            var point = new PointF(
                center.X + trackRadius * (float)Math.Cos(angle),
                center.Y + trackRadius * (float)Math.Sin(angle));
            var color = Theme.Pawns[playerIndex % Theme.Pawns.Length];
            using var brush = new SolidBrush(color);
            using var outline = new Pen(Theme.Background, 2f);
            graphics.FillEllipse(brush, point.X - 9, point.Y - 9, 18, 18);
            graphics.DrawEllipse(outline, point.X - 9, point.Y - 9, 18, 18);
            using var font = new Font("Segoe UI", 7f, FontStyle.Bold);
            using var textBrush = new SolidBrush(Theme.Background);
            using var format = new StringFormat
            {
                Alignment = StringAlignment.Center,
                LineAlignment = StringAlignment.Center
            };
            graphics.DrawString((playerIndex + 1).ToString(), font, textBrush,
                new RectangleF(point.X - 8, point.Y - 8, 16, 16), format);
        }
    }

    private void DrawCenter(Graphics graphics, PointF center)
    {
        var player = Game!.CurrentPlayer;
        var box = new RectangleF(center.X - 130, center.Y - 104, 260, 208);
        using var path = RoundedRectangle(box, 18);
        using var background = new SolidBrush(Color.FromArgb(19, 28, 38));
        using var border = new Pen(Color.FromArgb(101, 137, 124), 2f);
        graphics.FillPath(background, path);
        graphics.DrawPath(border, path);

        DrawCentered(graphics, "LIFE CAPITAL", Theme.Accent, 15f, FontStyle.Bold,
            new RectangleF(box.X, box.Y + 17, box.Width, 25));
        DrawCentered(graphics, player.Name, Theme.Text, 11f, FontStyle.Bold,
            new RectangleF(box.X + 8, box.Y + 55, box.Width - 16, 22));
        DrawCentered(graphics, player.Track == TrackKind.RatRace ? "RAT RACE" : "FAST TRACK",
            Theme.Gold, 9f, FontStyle.Bold,
            new RectangleF(box.X + 8, box.Y + 82, box.Width - 16, 20));
        DrawCentered(graphics, $"Cash  {GameEngine.Money(player.Cash)}",
            Theme.Text, 9f, FontStyle.Regular,
            new RectangleF(box.X + 8, box.Y + 116, box.Width - 16, 18));
        DrawCentered(graphics, $"Passive  {GameEngine.Money(player.PassiveIncome)} / mo",
            Theme.Accent, 9f, FontStyle.Bold,
            new RectangleF(box.X + 8, box.Y + 139, box.Width - 16, 18));
        DrawCentered(graphics, $"Net worth  {GameEngine.Money(player.NetWorth)}",
            Theme.Muted, 8f, FontStyle.Regular,
            new RectangleF(box.X + 8, box.Y + 161, box.Width - 16, 18));
    }

    private void DrawLegend(Graphics graphics)
    {
        using var font = new Font("Segoe UI", 8f, FontStyle.Regular);
        using var brush = new SolidBrush(Theme.Text);
        graphics.DrawString("OUTER  FAST TRACK     ·     INNER  RAT RACE     ·     24 SPACES EACH",
            font, brush, 18, ClientSize.Height - 26);
    }

    private void DrawWelcome(Graphics graphics)
    {
        var text = "LIFE CAPITAL";
        using var titleFont = new Font("Segoe UI", 25f, FontStyle.Bold);
        using var noteFont = new Font("Segoe UI", 11f, FontStyle.Regular);
        using var titleBrush = new SolidBrush(Theme.Accent);
        using var noteBrush = new SolidBrush(Theme.Text);
        using var format = new StringFormat
        {
            Alignment = StringAlignment.Center,
            LineAlignment = StringAlignment.Center
        };
        graphics.DrawString(text, titleFont, titleBrush,
            new RectangleF(0, ClientSize.Height / 2f - 35, ClientSize.Width, 42), format);
        graphics.DrawString("An India-focused financial strategy board game",
            noteFont, noteBrush,
            new RectangleF(20, ClientSize.Height / 2f + 16, ClientSize.Width - 40, 30), format);
    }

    private static void DrawCentered(
        Graphics graphics,
        string text,
        Color color,
        float size,
        FontStyle style,
        RectangleF bounds)
    {
        using var font = new Font("Segoe UI", size, style);
        using var brush = new SolidBrush(color);
        using var format = new StringFormat
        {
            Alignment = StringAlignment.Center,
            LineAlignment = StringAlignment.Center,
            Trimming = StringTrimming.EllipsisCharacter
        };
        graphics.DrawString(text, font, brush, bounds, format);
    }

    private static string ShortLabel(SpaceKind kind) => kind switch
    {
        SpaceKind.Payday => "PAYDAY",
        SpaceKind.SmallDeal => "SMALL",
        SpaceKind.BigDeal => "BIG DEAL",
        SpaceKind.Market => "MARKET",
        SpaceKind.Doodad => "DOODAD",
        SpaceKind.Charity => "CHARITY",
        SpaceKind.Downsized => "DOWNSIZED",
        SpaceKind.Baby => "BABY",
        SpaceKind.CashflowDay => "CASHFLOW",
        SpaceKind.Dream => "DREAM",
        SpaceKind.Opportunity => "VENTURE",
        _ => kind.ToString().ToUpperInvariant()
    };

    private static GraphicsPath RoundedRectangle(RectangleF rectangle, float radius)
    {
        var diameter = radius * 2;
        var path = new GraphicsPath();
        path.AddArc(rectangle.X, rectangle.Y, diameter, diameter, 180, 90);
        path.AddArc(rectangle.Right - diameter, rectangle.Y, diameter, diameter, 270, 90);
        path.AddArc(rectangle.Right - diameter, rectangle.Bottom - diameter, diameter, diameter, 0, 90);
        path.AddArc(rectangle.X, rectangle.Bottom - diameter, diameter, diameter, 90, 90);
        path.CloseFigure();
        return path;
    }
}
