Module GuiFunctions

    Public app_path As String
    Public infoList As String = ""
    Public defaultStatusBackColor As Color
    Public defaultStatusForeColor As Color

    Sub RefreshPB(pb As ProgressBar, label As Label, value As Integer)

        If value > pb.Maximum Then
            pb.Value = pb.Maximum
            label.ForeColor = Color.Red
            Return
        End If

        If value < pb.Minimum Then
            pb.Value = pb.Minimum
            label.ForeColor = Color.Blue
            Return
        End If

        pb.Value = value
        label.ForeColor = Color.Black

    End Sub

    Public Sub Report(type As String, message As String)

        Main.StatusLabel.Text = message
        Main.StatusLabel.BackColor = defaultStatusBackColor
        Main.StatusLabel.ForeColor = defaultStatusForeColor

        If type.Equals("E") Then
            Main.StatusLabel.BackColor = Color.Red
            Main.StatusLabel.ForeColor = Color.White
        End If

        If type.Equals("W") Then
            Main.StatusLabel.BackColor = Color.Orange
            Main.StatusLabel.ForeColor = Color.White
        End If

        If type.Equals("X") Then
            Main.StatusLabel.BackColor = Color.Blue
            Main.StatusLabel.ForeColor = Color.White
        End If

    End Sub

End Module
