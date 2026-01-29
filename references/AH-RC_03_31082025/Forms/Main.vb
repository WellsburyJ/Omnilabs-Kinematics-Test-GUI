Imports System.ComponentModel
Imports System.IO.Ports

Public Class Main

    Dim updateValues As Boolean = False
    Dim updateVB As Boolean = False
    Dim connected As Boolean = False
    Private tcpSck As TcpSocket    ' 3D view socket
    Private udpSck As UdpSocket

    Private groupBox(5) As GroupBox
    Private labelFlexion(5) As Label
    Private pbFlex(5) As ProgressBar
    Private labelForce(5) As Label
    Private pbForce(5) As ProgressBar
    Private labelPress(5) As Label
    Private pbPress(5) As ProgressBar
    Private vacuumValve(5) As CheckBox
    Private pressValve(5) As CheckBox
    Private pumpOrder(5) As TrackBar
    Private vibrator(5) As CheckBox
    Private releaseBtn(5) As Button

    Public Sub ConsoleDisplay(info)

        CConsole.consoleDisplay(info)

    End Sub
    Sub Reset()

        VB0.Checked = False
        VB0.Enabled = False

        Dim n As Integer
        For n = 1 To 5
            vacuumValve(n).Enabled = False
            vacuumValve(n).Checked = False
            pressValve(n).Enabled = False
            pressValve(n).Checked = False
            pumpOrder(n).Enabled = False
            pumpOrder(n).Value = 0
            vibrator(n).Enabled = False
            vibrator(n).Checked = False
            releaseBtn(n).Enabled = False
        Next

        ConnectBtn.Enabled = True

    End Sub

    Private Sub Timer1_Tick(sender As Object, e As EventArgs) Handles Timer1.Tick

        If mpuPresent Then
            MpuState.BackColor = Color.LimeGreen
            Label1.Text = "roll:" + Str(roll)
            Label2.Text = "pitch:" + Str(pitch)
            Label4.Text = "yaw:" + Str(yaw)
        Else
            MpuState.BackColor = Color.Gray
        End If

        If SerialPort1.IsOpen Then
            Status1.Text = "..."
        Else
            Status1.Text = "X"
        End If

        If Not My.Settings.Media.Equals("SerialPort") Then
            Status2.Enabled = True
            Status1.Enabled = False
            If connected Then
                Status2.Text = "..."
            Else
                Status2.Text = "X"
            End If
        Else
            Status2.Enabled = False
            Status1.Enabled = True
        End If

        If Not connected Then
            Reset()
            ConnectBtn.Enabled = True
            ToolStripButton2.Enabled = False
            Return
        Else
            VB0.Enabled = True
            Dim n As Integer
            For n = 1 To 5
                vacuumValve(n).Enabled = True
                pressValve(n).Enabled = True
                pumpOrder(n).Enabled = True
                vibrator(n).Enabled = True
                releaseBtn(n).Enabled = True
            Next
            ConnectBtn.Enabled = False
            ToolStripButton2.Enabled = True
        End If

        If updateValues Then
            If connected Then
                Dim command = GetUpdateBytes()
                Dim b(command.Length) As Byte
                For n = 0 To command.Length - 1
                    b(n) = Asc(command.Chars(n))
                Next
                If My.Settings.Media.Equals("SerialPort") Then
                    Try
                        SerialPort1.Write(b, 0, b.Length - 1)
                    Catch ex As Exception
                        Report("E", ex.ToString)
                        connected = False
                        SerialPort1.Close()
                    End Try
                Else
                    udpSck.Send(b, b.Length, My.Settings.ServerAddress, My.Settings.ServerPort)
                End If
            End If
        End If

        updateValues = False

        If updateVB Then
            If connected Then
                Dim command = GetUpdateVB()
                Dim b(command.Length) As Byte
                For n = 0 To command.Length - 1
                    b(n) = Asc(command.Chars(n))
                Next
                If My.Settings.Media.Equals("SerialPort") Then
                    Try
                        SerialPort1.Write(b, 0, b.Length - 1)
                    Catch ex As Exception
                        Report("E", ex.ToString)
                        connected = False
                        SerialPort1.Close()
                    End Try
                Else
                    udpSck.Send(b, b.Length, My.Settings.ServerAddress, My.Settings.ServerPort)
                End If
            End If

        End If
        updateVB = False

        Dim viewUpdate As String = ""
        Dim a3 As Double
        viewUpdate += LTrim(Str(Int(a3)))
        viewUpdate += "," + LTrim(Str(Int(a3)))
        viewUpdate += "," + LTrim(Str(roll))
        viewUpdate += "," + LTrim(Str(pitch))
        viewUpdate += "," + LTrim(Str(yaw)) + vbCrLf

        If ext.Checked Then
            Try
                If Not tcpSck.s.Connected Then
                    tcpSck.TcpConnect("127.0.0.1", 12345)
                Else
                    Dim b(viewUpdate.Length) As Byte
                    Dim n As Integer
                    For n = 1 To viewUpdate.Length
                        b(n - 1) = Asc(Mid(viewUpdate, n, 1))
                    Next
                    tcpSck.TcpSend(b, b.Length)
                End If
            Catch ex As Exception
                Stop
            End Try
        End If

        Try
            pbPress(1).Value = FG1_PresValue
            pbPress(2).Value = FG2_PresValue
            pbPress(3).Value = FG3_PresValue
            pbPress(4).Value = FG4_PresValue
            pbPress(5).Value = FG5_PresValue

            pbFlex(1).Value = FG1_FlexValue
            pbFlex(2).Value = FG2_FlexValue
            pbFlex(3).Value = FG3_FlexValue
            pbFlex(4).Value = FG4_FlexValue
            pbFlex(5).Value = FG5_FlexValue
        Catch ex As Exception

        End Try

    End Sub

    Private Sub Main_Load(sender As Object, e As EventArgs) Handles MyBase.Load

        app_path = System.IO.Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly.GetName.CodeBase)
        If app_path.StartsWith("file:") Then
            app_path = app_path.Substring(6)
        End If

        Dim w As Integer = 100
        For n = 1 To 5
            GroupBox(n) = New GroupBox()
            groupBox(n).Text = "FG" + LTrim(Str(n))
            groupBox(n).Width = w
            groupBox(n).Height = 295
            groupBox(n).Top = 40
            groupBox(n).Left = 10 + ((w + 5) * (n - 1))

            labelFlexion(n) = New Label With {
                .Top = 20,
                .Left = 10,
                .Height = 15,
                .Width = w - 20,
                .Text = "Flexion"
            }

            pbFlex(n) = New ProgressBar With {
                .Width = w - 20,
                .Height = 10,
                .Left = 10,
                .Top = 40
            }

            labelForce(n) = New Label With {
                .Top = 60,
                .Left = 10,
                .Height = 15,
                .Width = w - 20,
                .Text = "Force"
            }

            pbForce(n) = New ProgressBar With {
                .Width = w - 20,
                .Height = 10,
                .Left = 10,
                .Top = 80
            }

            labelPress(n) = New Label With {
                .Top = 100,
                .Left = 10,
                .Height = 15,
                .Width = w - 20,
                .Text = "Press."
            }

            pbPress(n) = New ProgressBar With {
                .Width = w - 20,
                .Height = 10,
                .Left = 10,
                .Top = 120
            }

            vacuumValve(n) = New CheckBox With {
                .Top = 140,
                .Left = 10,
                .Width = w - 20,
                .Enabled = False,
                .Text = "Vacuum"
            }
            AddHandler vacuumValve(n).Click, AddressOf vacuumValve_Click

            pressValve(n) = New CheckBox With {
                .Top = 160,
                .Left = 10,
                .Width = w - 20,
                .Enabled = False,
                .Text = "Press."
            }
            AddHandler pressValve(n).Click, AddressOf pressValve_Click

            pumpOrder(n) = New TrackBar With {
                .Top = 190,
                .Left = 10,
                .Width = w - 20,
                .Height = w - 20,
                .Maximum = 3,
                .Enabled = False
            }
            AddHandler pumpOrder(n).MouseUp, AddressOf pumpOrder_Changed

            vibrator(n) = New CheckBox With {
                .Top = 230,
                .Left = 10,
                .Width = w - 20,
                .Enabled = False,
                .Text = "Vibrator"
            }
            AddHandler vibrator(n).Click, AddressOf vibrator_Click

            releaseBtn(n) = New Button With {
                .Top = 260,
                .Left = 10,
                .Width = w - 20,
                .Height = 30,
                .Enabled = False,
                .Name = LTrim(Str(n)),
                .Text = "Release"
            }
            AddHandler releaseBtn(n).Click, AddressOf release_Click

            groupBox(n).Controls.Add(labelFlexion(n))
            groupBox(n).Controls.Add(pbFlex(n))
            groupBox(n).Controls.Add(labelForce(n))
            groupBox(n).Controls.Add(pbForce(n))
            groupBox(n).Controls.Add(labelPress(n))
            groupBox(n).Controls.Add(pbPress(n))
            groupBox(n).Controls.Add(vacuumValve(n))
            groupBox(n).Controls.Add(pressValve(n))
            groupBox(n).Controls.Add(pumpOrder(n))
            groupBox(n).Controls.Add(vibrator(n))
            groupBox(n).Controls.Add(releaseBtn(n))
            Me.Controls.Add(groupBox(n))
        Next

        CreateLog()

        defaultStatusBackColor = StatusLabel.BackColor
        defaultStatusForeColor = StatusLabel.ForeColor

        tcpSck = New TcpSocket With {
            .parent = Me
        }

    End Sub
    Private Sub vacuumValve_Click(sender As Object, e As EventArgs)

        updateValues = True

    End Sub
    Private Sub pressValve_Click(sender As Object, e As EventArgs)

        updateValues = True

    End Sub
    Private Sub pumpOrder_Changed(sender As Object, e As EventArgs)

        updateValues = True

    End Sub

    Private Sub vibrator_Click(sender As Object, e As EventArgs)

        updateVB = True

    End Sub
    Private Sub release_Click(sender As Object, e As EventArgs)

        Dim btn As Button = sender
        Release(Val(btn.Name))

    End Sub

    Private Sub ZeroBtn_Click(sender As Object, e As EventArgs) Handles zeroBtn.Click

        Reset()
        updateValues = True
        updateVB = True

    End Sub

    Private Sub SettingsBtn_Click(sender As Object, e As EventArgs) Handles SettingsBtn.Click

        SettingsForm.ShowDialog()

    End Sub

    Private Sub AboutBtn_Click(sender As Object, e As EventArgs) Handles AboutBtn.Click

        AboutBox1.ShowDialog()

    End Sub

    Private Sub ConnectBtn_Click(sender As Object, e As EventArgs) Handles ConnectBtn.Click

        If My.Settings.Media.Equals("SerialPort") Then
            Try
                If SerialPort1.IsOpen Then
                    SerialPort1.Close()
                    connected = False
                End If
                SerialPort1.PortName = My.Settings.SerialPort
                SerialPort1.Open()
                SerialPort1.Write("reset" + vbLf)
                connected = True
            Catch ex As Exception
                Report("E", ex.ToString)
            End Try
        Else

            udpSck.Init(My.Settings.ServerPort)
            connected = True

        End If

    End Sub

    Private Sub Main_Closing(sender As Object, e As CancelEventArgs) Handles Me.Closing

        CloseLog()

        If SerialPort1.IsOpen Then
            SerialPort1.Close()
        End If
        If tcpSck.s.Connected Then
            tcpSck.s.Close()
        End If

    End Sub

    Private Sub SerialPort1_DataReceived(sender As Object, e As SerialDataReceivedEventArgs) Handles SerialPort1.DataReceived

        Dim data(200) As Byte
        Dim l As Integer = SerialPort1.Read(data, 0, 200)
        ReDim Preserve data(l)
        CommReceive(data)

    End Sub

    Private Sub StatusLabel_Click(sender As Object, e As EventArgs) Handles StatusLabel.Click

        StatusLabel.Text = ""
        StatusLabel.BackColor = defaultStatusBackColor
        StatusLabel.ForeColor = defaultStatusForeColor

    End Sub

    Function GetUpdateBytes() As String

        Dim command As String = "set outputs "

        Dim n As Integer
        For n = 1 To 5
            If (vacuumValve(n).Checked = False) And (pressValve(n).Checked = False) Then
                command += "O"
            End If
            If (vacuumValve(n).Checked = False) And (pressValve(n).Checked = True) Then
                command += "P"
            End If
            If (vacuumValve(n).Checked = True) And (pressValve(n).Checked = False) Then
                command += "V"
            End If
            If (vacuumValve(n).Checked = True) And (pressValve(n).Checked = True) Then
                command += "C"
            End If
            command += LTrim(Str(3 * pumpOrder(n).Value))
        Next
        Return command + vbCrLf

    End Function

    Function GetUpdateVB() As String

        Dim command As String = "set vibrators "
        If VB0.Checked = True Then
            command += "1"
        Else
            command += "0"
        End If
        Dim n As Integer
        For n = 1 To 5
            If vibrator(n).Checked = True Then
                command += "1"
            Else
                command += "0"
            End If
        Next
        Return command + vbCrLf

    End Function

    Private Sub ToolStripButton2_Click(sender As Object, e As EventArgs) Handles ToolStripButton2.Click

        CConsole.ShowDialog()

    End Sub

    Private Sub Timer2_Tick(sender As Object, e As EventArgs) Handles TimerScript.Tick

        If scriptIndex < commandsList.Count Then
            ExecuteLine()
        Else
            TimerScript.Enabled = False
            ScriptButton.Enabled = True
            Reset()
            Report("I", "Exercise finished !")
        End If

    End Sub

    Private Sub ScriptButton_Click(sender As Object, e As EventArgs) Handles ScriptButton.Click

        OpenFileDialog1.InitialDirectory = app_path
        OpenFileDialog1.Title = "Select exercise"
        OpenFileDialog1.FileName = ""
        OpenFileDialog1.Filter = "Text files (*.txt)|*.txt|All files (*.*)|*.*" '

        Dim res As DialogResult = OpenFileDialog1.ShowDialog()
        If res = DialogResult.OK Then
            Dim filename = OpenFileDialog1.FileName
            Dim f() As String = filename.Split("\")
            ReadScriptFile(filename)
            TimerScript.Enabled = True
            ScriptButton.Enabled = False
            If f.Length > 0 Then
                Report("X", "Executing exercise: " + f(f.Length - 1) + " ...")
            Else
                Report("X", "Executing exercise: " + filename + " ...")
            End If
        End If

    End Sub

    Private Sub LogBtn_Click(sender As Object, e As EventArgs) Handles LogBtn.Click

        OpenFileDialog1.InitialDirectory = app_path + "\log\"
        OpenFileDialog1.Title = "View log"
        OpenFileDialog1.FileName = ""
        OpenFileDialog1.Filter = "Log files (*.log)|*.log|All files (*.*)|*.*"

        Dim res As DialogResult = OpenFileDialog1.ShowDialog()
        If res = DialogResult.OK Then
            Dim filename = OpenFileDialog1.FileName
            Shell("notepad " + filename, AppWinStyle.NormalFocus)
        End If

    End Sub

    Private Sub VB0_CheckedChanged(sender As Object, e As EventArgs) Handles VB0.CheckedChanged

        updateVB = True

    End Sub

    Private Sub SerialPort1_ErrorReceived(sender As Object, e As SerialErrorReceivedEventArgs) Handles SerialPort1.ErrorReceived

        Stop

    End Sub

    Public Sub SetPumpOrder(finger As Integer, value As Integer)

        pumpOrder(finger).Value = value
        updateValues = True

    End Sub

    Public Sub SetValve(finger As Integer, status As Char)

        vacuumValve(finger).Checked = False
        pressValve(finger).Checked = False

        If status = "V" Then
            vacuumValve(finger).Checked = True

        End If

        If status = "P" Then
            pressValve(finger).Checked = True

        End If

        If status = "C" Then
            vacuumValve(finger).Checked = True
            pressValve(finger).Checked = True
        End If

        updateValues = True

    End Sub

    Public Sub SetVibrator(finger As Integer, status As Boolean)

        If finger = 0 Then
            VB0.Checked = status
        Else
            vibrator(finger).Checked = status
        End If

        updateVB = True

    End Sub

    Public Sub Release(finger As Integer)

        SetPumpOrder(finger, 0)
        SetValve(finger, "O")

        pressValve(finger).Checked = False
        vacuumValve(finger).Checked = False
        pumpOrder(finger).Value = 0

        Dim cmd As String = "release"
        cmd += Str(finger)
        cmd += vbCrLf
        Try
            SerialPort1.Write(cmd)
        Catch ex As Exception
            Debug.Print(ex.Message)
        End Try
    End Sub

End Class
