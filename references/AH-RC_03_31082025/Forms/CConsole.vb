Public Class CConsole

    Public Sub New()

        ' This call is required by the designer.
        InitializeComponent()

        ' Add any initialization after the InitializeComponent() call.

    End Sub

    Private Sub console_Load(sender As Object, e As EventArgs) Handles MyBase.Load

        ComboBox1.Items.Clear()
        ComboBox1.Items.Add("get version")
        ComboBox1.Items.Add("get wifi status")
        ComboBox1.Items.Add("get bt status")
        ComboBox1.Items.Add("set outputs")

        infoList = ""
        Try
            Main.SerialPort1.Write("stop values" + vbCrLf)
            Main.SerialPort1.Write("get bt status" + vbCrLf)
            Main.SerialPort1.Write("get wifi status" + vbCrLf)
        Catch ex As Exception
            Debug.Print(ex.Message)
        End Try

    End Sub

    Public Sub consoleDisplay(info As String)

        infoList += info

    End Sub

    Private Sub Button1_Click(sender As Object, e As EventArgs) Handles Button1.Click

        Try
            Dim cmd As String = ComboBox1.Text + vbLf
            Main.SerialPort1.Write(cmd)
        Catch ex As Exception
            Debug.Print(ex.Message)
        End Try

    End Sub

    Private Sub Timer1_Tick(sender As Object, e As EventArgs) Handles Timer1.Tick

        If infoList.Length > 0 Then
            Dim infos() As String
            infos = infoList.Split(vbCrLf)
            Dim n As Integer
            For n = 0 To infos.Length - 1
                ListBox1.Items.Add(infos(n))
                If ListBox1.Items.Count > 75 Then
                    ListBox1.Items.RemoveAt(0)
                End If
            Next
            ListBox1.SelectedIndex = ListBox1.Items.Count - 1
            infoList = ""
        End If

    End Sub

    Private Sub CConsole_FormClosing(sender As Object, e As FormClosingEventArgs) Handles Me.FormClosing

        Try
            Main.SerialPort1.Write("start values" + vbCrLf)
        Catch ex As Exception
            Debug.Print(ex.Message)
        End Try

    End Sub

    Private Sub TextBox1_KeyPress(sender As Object, e As KeyPressEventArgs)

        If e.KeyChar = vbCr Then
            Button1_Click(sender, e)
        End If

    End Sub

    Private Sub GetSsid_Click(sender As Object, e As EventArgs) Handles GetWifiSsid.Click
        Try
            Main.SerialPort1.Write("get wifi ssid" + vbCrLf)
        Catch ex As Exception
            Debug.Print(ex.Message)
        End Try

    End Sub

    Private Sub GetPwd_Click(sender As Object, e As EventArgs) Handles GetWifiPwd.Click

        Try
            Main.SerialPort1.Write("get wifi password" + vbCrLf)
        Catch ex As Exception
            Debug.Print(ex.Message)
        End Try

    End Sub

    Private Sub SetSsid_Click(sender As Object, e As EventArgs) Handles SetWifiSsid.Click
        Try
            Main.SerialPort1.Write("set wifi ssid " + DeviceWiFiSsid.Text + vbCrLf)
        Catch ex As Exception

        End Try
    End Sub

    Private Sub SetPwd_Click(sender As Object, e As EventArgs) Handles SetWifiPwd.Click

        Try
            Main.SerialPort1.Write("set wifi password " + DeviceWiFiPwd.Text + vbCrLf)
        Catch ex As Exception
            Debug.Print(ex.Message)
        End Try

    End Sub

    Private Sub getBtSsid_Click(sender As Object, e As EventArgs) Handles getBtSsid.Click

        Try
            Main.SerialPort1.Write("get bt name" + vbCrLf)
        Catch ex As Exception
            Debug.Print(ex.Message)
        End Try

    End Sub

    Private Sub getBtPin_Click(sender As Object, e As EventArgs) Handles getBtPin.Click

        Try
            Main.SerialPort1.Write("get bt pin" + vbCrLf)
        Catch ex As Exception
            Debug.Print(ex.Message)
        End Try

    End Sub

    Private Sub setBtSsid_Click(sender As Object, e As EventArgs) Handles setBtSsid.Click

        Try
            Main.SerialPort1.Write("set bt name " + btSsid.Text + vbCrLf)
        Catch ex As Exception
            Debug.Print(ex.Message)
        End Try

    End Sub

    Private Sub setBtPin_Click(sender As Object, e As EventArgs) Handles setBtPin.Click

        Try
            Main.SerialPort1.Write("set bt pin " + btPin.Text + vbCrLf)
        Catch ex As Exception
            Debug.Print(ex.Message)
        End Try

    End Sub

    Private Sub wifiEnabled_CheckedChanged(sender As Object, e As EventArgs) Handles wifiEnabled.CheckedChanged

        Try
            If wifiEnabled.Checked Then
                Main.SerialPort1.Write("set wifi on" + vbCrLf)
            Else
                Main.SerialPort1.Write("set wifi off" + vbCrLf)
            End If
        Catch ex As Exception
            Debug.Print(ex.Message)
        End Try

    End Sub

    Private Sub btEnabled_CheckedChanged(sender As Object, e As EventArgs) Handles btEnabled.CheckedChanged

        Try
            If btEnabled.Checked Then
                Main.SerialPort1.Write("set bt on" + vbCrLf)
            Else
                Main.SerialPort1.Write("set bt off" + vbCrLf)
            End If
        Catch ex As Exception
            Debug.Print(ex.Message)
        End Try

    End Sub

    Private Sub Button2_Click(sender As Object, e As EventArgs) Handles Button2.Click

        ListBox1.Items.Clear()

    End Sub

End Class