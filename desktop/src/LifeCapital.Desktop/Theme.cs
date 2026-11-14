namespace LifeCapital.Desktop;

internal static class Theme
{
    public static readonly Color Background = Color.FromArgb(10, 14, 23);
    public static readonly Color Panel = Color.FromArgb(24, 34, 47);
    public static readonly Color PanelRaised = Color.FromArgb(32, 45, 59);
    public static readonly Color Text = Color.FromArgb(239, 244, 241);
    public static readonly Color Muted = Color.FromArgb(150, 166, 173);
    public static readonly Color Accent = Color.FromArgb(64, 214, 176);
    public static readonly Color Gold = Color.FromArgb(255, 197, 104);
    public static readonly Color Danger = Color.FromArgb(255, 112, 111);
    public static readonly Color Wood = Color.FromArgb(60, 42, 32);
    public static readonly Color[] Pawns =
    [
        Color.FromArgb(64, 214, 176),
        Color.FromArgb(255, 197, 104),
        Color.FromArgb(123, 151, 255),
        Color.FromArgb(255, 120, 151),
        Color.FromArgb(177, 220, 111)
    ];

    public static readonly Font BodyFont = new("Segoe UI", 9.5f, FontStyle.Regular);
    public static readonly Font SmallBoldFont = new("Segoe UI", 8f, FontStyle.Bold);
    public static readonly Font ButtonFont = new("Segoe UI", 9f, FontStyle.Bold);
    public static readonly Font TitleFont = new("Segoe UI", 17f, FontStyle.Bold);
}
