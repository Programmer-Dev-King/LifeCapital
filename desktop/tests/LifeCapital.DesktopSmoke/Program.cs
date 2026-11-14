using System.Windows.Forms;
using System.Reflection;
using LifeCapital.Core;

internal static class Program
{
    [STAThread]
    private static int Main()
    {
        var dialogType = Assembly.Load("LifeCapital.Desktop")
            .GetType("LifeCapital.Desktop.SetupDialog", throwOnError: true)!;
        using var dialog = (Form)Activator.CreateInstance(dialogType, nonPublic: true)!;
        var playerCount = Descendants(dialog).OfType<NumericUpDown>().Single();
        playerCount.Value = 2;

        var choices = Descendants(dialog).OfType<ComboBox>().ToArray();
        if (choices.Length != 4
            || choices[0].Items.Count != 5
            || choices[1].Items.Count != 4
            || choices.Any(choice => choice.SelectedItem is null))
        {
            Console.Error.WriteLine("Player setup did not populate profession and dream choices.");
            return 1;
        }

        dialogType.GetMethod("CreatePlayers", BindingFlags.Instance | BindingFlags.NonPublic)!
            .Invoke(dialog, null);
        var players = (IReadOnlyList<Player>)dialogType.GetProperty("Players")!.GetValue(dialog)!;
        if (players.Count != 2 || players[0].Profile == players[1].Profile)
        {
            Console.Error.WriteLine("Player setup did not create the selected players.");
            return 1;
        }

        Console.WriteLine("PASS  Player setup creates valid profession and dream choices.");
        return 0;
    }

    private static IEnumerable<Control> Descendants(Control parent) =>
        parent.Controls.Cast<Control>()
            .SelectMany(child => Descendants(child).Prepend(child));
}
