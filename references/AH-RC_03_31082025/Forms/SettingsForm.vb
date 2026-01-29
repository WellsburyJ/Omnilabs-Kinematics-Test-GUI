Public Class SettingsForm

    Private Sub SettingsForm_Load(sender As Object, e As EventArgs) Handles MyBase.Load

        Dim list As List(Of String) = GetSerialPortNames()
        ComboBox1.Items.Clear()
        ComboBox1.Items.Add("-")
        For Each sp As String In list
            ComboBox1.Items.Add(sp)
        Next

        If Not My.Settings.SerialPort.Equals("") Then
            ComboBox1.Text = My.Settings.SerialPort
        End If

        If My.Settings.Media.Equals("SerialPort") Then
            RadioButton1.Checked = True
        Else
            RadioButton2.Checked = True
        End If

        If Not My.Settings.ServerAddress.Equals("") Then
            ServerAddress.Text = My.Settings.ServerAddress
        End If
        If Not My.Settings.ServerPort.Equals("") Then
            ServerPort.Text = My.Settings.ServerPort
        End If

    End Sub

    Function GetSerialPortNames() As List(Of String)

        'Dim searcher As New System.Management.ManagementObjectSearcher("SELECT * FROM Win32_SerialPort")
        'Dim lst As List(Of String) = New List(Of String)
        'For Each queryObj As Management.ManagementObject In searcher.Get()
        'Dim s As String = queryObj("DeviceID") + " - " + queryObj("Name")
        'lst.Add(s)
        'Next

        ' Show all available COM ports.
        Dim list As List(Of String) = New List(Of String)
        For Each sp As String In My.Computer.Ports.SerialPortNames
            list.Add(sp)
        Next
        Return list

    End Function

    Private Sub Button2_Click(sender As Object, e As EventArgs) Handles Button2.Click

        Me.Close()

    End Sub

    Private Sub Button1_Click(sender As Object, e As EventArgs) Handles Button1.Click

        My.Settings.SerialPort = ComboBox1.Text

        If RadioButton1.Checked = True Then
            My.Settings.Media = "SerialPort"
        Else
            My.Settings.Media = "IP"
        End If

        My.Settings.ServerAddress = ServerAddress.Text
        My.Settings.ServerPort = ServerPort.Text

        Me.Close()

    End Sub

End Class