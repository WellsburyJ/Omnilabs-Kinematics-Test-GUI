<Global.Microsoft.VisualBasic.CompilerServices.DesignerGenerated()> _
Partial Class CConsole
    Inherits System.Windows.Forms.Form

    'Form overrides dispose to clean up the component list.
    <System.Diagnostics.DebuggerNonUserCode()> _
    Protected Overrides Sub Dispose(ByVal disposing As Boolean)
        Try
            If disposing AndAlso components IsNot Nothing Then
                components.Dispose()
            End If
        Finally
            MyBase.Dispose(disposing)
        End Try
    End Sub

    'Required by the Windows Form Designer
    Private components As System.ComponentModel.IContainer

    'NOTE: The following procedure is required by the Windows Form Designer
    'It can be modified using the Windows Form Designer.  
    'Do not modify it using the code editor.
    <System.Diagnostics.DebuggerStepThrough()> _
    Private Sub InitializeComponent()
        Me.components = New System.ComponentModel.Container()
        Me.ListBox1 = New System.Windows.Forms.ListBox()
        Me.Button1 = New System.Windows.Forms.Button()
        Me.Timer1 = New System.Windows.Forms.Timer(Me.components)
        Me.GroupBox1 = New System.Windows.Forms.GroupBox()
        Me.wifiEnabled = New System.Windows.Forms.CheckBox()
        Me.SetWifiPwd = New System.Windows.Forms.Button()
        Me.GetWifiPwd = New System.Windows.Forms.Button()
        Me.SetWifiSsid = New System.Windows.Forms.Button()
        Me.GetWifiSsid = New System.Windows.Forms.Button()
        Me.DeviceWiFiPwd = New System.Windows.Forms.TextBox()
        Me.DeviceWiFiSsid = New System.Windows.Forms.TextBox()
        Me.Label2 = New System.Windows.Forms.Label()
        Me.Label1 = New System.Windows.Forms.Label()
        Me.GroupBox2 = New System.Windows.Forms.GroupBox()
        Me.btEnabled = New System.Windows.Forms.CheckBox()
        Me.setBtPin = New System.Windows.Forms.Button()
        Me.getBtPin = New System.Windows.Forms.Button()
        Me.setBtSsid = New System.Windows.Forms.Button()
        Me.getBtSsid = New System.Windows.Forms.Button()
        Me.btPin = New System.Windows.Forms.TextBox()
        Me.btSsid = New System.Windows.Forms.TextBox()
        Me.LabelPin = New System.Windows.Forms.Label()
        Me.Label4 = New System.Windows.Forms.Label()
        Me.Button2 = New System.Windows.Forms.Button()
        Me.ComboBox1 = New System.Windows.Forms.ComboBox()
        Me.GroupBox1.SuspendLayout()
        Me.GroupBox2.SuspendLayout()
        Me.SuspendLayout()
        '
        'ListBox1
        '
        Me.ListBox1.FormattingEnabled = True
        Me.ListBox1.ItemHeight = 16
        Me.ListBox1.Location = New System.Drawing.Point(12, 10)
        Me.ListBox1.Name = "ListBox1"
        Me.ListBox1.Size = New System.Drawing.Size(1017, 260)
        Me.ListBox1.TabIndex = 0
        '
        'Button1
        '
        Me.Button1.Location = New System.Drawing.Point(551, 426)
        Me.Button1.Name = "Button1"
        Me.Button1.Size = New System.Drawing.Size(130, 50)
        Me.Button1.TabIndex = 1
        Me.Button1.Text = "Send"
        Me.Button1.UseVisualStyleBackColor = True
        '
        'Timer1
        '
        Me.Timer1.Enabled = True
        '
        'GroupBox1
        '
        Me.GroupBox1.Controls.Add(Me.wifiEnabled)
        Me.GroupBox1.Controls.Add(Me.SetWifiPwd)
        Me.GroupBox1.Controls.Add(Me.GetWifiPwd)
        Me.GroupBox1.Controls.Add(Me.SetWifiSsid)
        Me.GroupBox1.Controls.Add(Me.GetWifiSsid)
        Me.GroupBox1.Controls.Add(Me.DeviceWiFiPwd)
        Me.GroupBox1.Controls.Add(Me.DeviceWiFiSsid)
        Me.GroupBox1.Controls.Add(Me.Label2)
        Me.GroupBox1.Controls.Add(Me.Label1)
        Me.GroupBox1.Location = New System.Drawing.Point(12, 276)
        Me.GroupBox1.Name = "GroupBox1"
        Me.GroupBox1.Size = New System.Drawing.Size(502, 131)
        Me.GroupBox1.TabIndex = 3
        Me.GroupBox1.TabStop = False
        Me.GroupBox1.Text = "WiFi"
        '
        'wifiEnabled
        '
        Me.wifiEnabled.AutoSize = True
        Me.wifiEnabled.Location = New System.Drawing.Point(100, 95)
        Me.wifiEnabled.Name = "wifiEnabled"
        Me.wifiEnabled.Size = New System.Drawing.Size(82, 21)
        Me.wifiEnabled.TabIndex = 8
        Me.wifiEnabled.Text = "Enabled"
        Me.wifiEnabled.UseVisualStyleBackColor = True
        '
        'SetWifiPwd
        '
        Me.SetWifiPwd.Location = New System.Drawing.Point(396, 58)
        Me.SetWifiPwd.Name = "SetWifiPwd"
        Me.SetWifiPwd.Size = New System.Drawing.Size(75, 25)
        Me.SetWifiPwd.TabIndex = 7
        Me.SetWifiPwd.Text = "SET"
        Me.SetWifiPwd.UseVisualStyleBackColor = True
        '
        'GetWifiPwd
        '
        Me.GetWifiPwd.Location = New System.Drawing.Point(315, 58)
        Me.GetWifiPwd.Name = "GetWifiPwd"
        Me.GetWifiPwd.Size = New System.Drawing.Size(75, 25)
        Me.GetWifiPwd.TabIndex = 6
        Me.GetWifiPwd.Text = "GET"
        Me.GetWifiPwd.UseVisualStyleBackColor = True
        '
        'SetWifiSsid
        '
        Me.SetWifiSsid.Location = New System.Drawing.Point(396, 26)
        Me.SetWifiSsid.Name = "SetWifiSsid"
        Me.SetWifiSsid.Size = New System.Drawing.Size(75, 25)
        Me.SetWifiSsid.TabIndex = 5
        Me.SetWifiSsid.Text = "SET"
        Me.SetWifiSsid.UseVisualStyleBackColor = True
        '
        'GetWifiSsid
        '
        Me.GetWifiSsid.Location = New System.Drawing.Point(315, 26)
        Me.GetWifiSsid.Name = "GetWifiSsid"
        Me.GetWifiSsid.Size = New System.Drawing.Size(75, 25)
        Me.GetWifiSsid.TabIndex = 4
        Me.GetWifiSsid.Text = "GET"
        Me.GetWifiSsid.UseVisualStyleBackColor = True
        '
        'DeviceWiFiPwd
        '
        Me.DeviceWiFiPwd.Location = New System.Drawing.Point(99, 58)
        Me.DeviceWiFiPwd.Name = "DeviceWiFiPwd"
        Me.DeviceWiFiPwd.Size = New System.Drawing.Size(200, 22)
        Me.DeviceWiFiPwd.TabIndex = 3
        '
        'DeviceWiFiSsid
        '
        Me.DeviceWiFiSsid.Location = New System.Drawing.Point(100, 27)
        Me.DeviceWiFiSsid.Name = "DeviceWiFiSsid"
        Me.DeviceWiFiSsid.Size = New System.Drawing.Size(200, 22)
        Me.DeviceWiFiSsid.TabIndex = 2
        '
        'Label2
        '
        Me.Label2.AutoSize = True
        Me.Label2.Location = New System.Drawing.Point(18, 62)
        Me.Label2.Name = "Label2"
        Me.Label2.Size = New System.Drawing.Size(69, 17)
        Me.Label2.TabIndex = 1
        Me.Label2.Text = "Password"
        '
        'Label1
        '
        Me.Label1.AutoSize = True
        Me.Label1.Location = New System.Drawing.Point(18, 30)
        Me.Label1.Name = "Label1"
        Me.Label1.Size = New System.Drawing.Size(39, 17)
        Me.Label1.TabIndex = 0
        Me.Label1.Text = "SSID"
        '
        'GroupBox2
        '
        Me.GroupBox2.Controls.Add(Me.btEnabled)
        Me.GroupBox2.Controls.Add(Me.setBtPin)
        Me.GroupBox2.Controls.Add(Me.getBtPin)
        Me.GroupBox2.Controls.Add(Me.setBtSsid)
        Me.GroupBox2.Controls.Add(Me.getBtSsid)
        Me.GroupBox2.Controls.Add(Me.btPin)
        Me.GroupBox2.Controls.Add(Me.btSsid)
        Me.GroupBox2.Controls.Add(Me.LabelPin)
        Me.GroupBox2.Controls.Add(Me.Label4)
        Me.GroupBox2.Location = New System.Drawing.Point(530, 276)
        Me.GroupBox2.Name = "GroupBox2"
        Me.GroupBox2.Size = New System.Drawing.Size(502, 131)
        Me.GroupBox2.TabIndex = 4
        Me.GroupBox2.TabStop = False
        Me.GroupBox2.Text = "BT"
        '
        'btEnabled
        '
        Me.btEnabled.AutoSize = True
        Me.btEnabled.Location = New System.Drawing.Point(100, 95)
        Me.btEnabled.Name = "btEnabled"
        Me.btEnabled.Size = New System.Drawing.Size(82, 21)
        Me.btEnabled.TabIndex = 8
        Me.btEnabled.Text = "Enabled"
        Me.btEnabled.UseVisualStyleBackColor = True
        '
        'setBtPin
        '
        Me.setBtPin.Location = New System.Drawing.Point(396, 58)
        Me.setBtPin.Name = "setBtPin"
        Me.setBtPin.Size = New System.Drawing.Size(75, 25)
        Me.setBtPin.TabIndex = 7
        Me.setBtPin.Text = "SET"
        Me.setBtPin.UseVisualStyleBackColor = True
        '
        'getBtPin
        '
        Me.getBtPin.Location = New System.Drawing.Point(315, 58)
        Me.getBtPin.Name = "getBtPin"
        Me.getBtPin.Size = New System.Drawing.Size(75, 25)
        Me.getBtPin.TabIndex = 6
        Me.getBtPin.Text = "GET"
        Me.getBtPin.UseVisualStyleBackColor = True
        '
        'setBtSsid
        '
        Me.setBtSsid.Location = New System.Drawing.Point(396, 26)
        Me.setBtSsid.Name = "setBtSsid"
        Me.setBtSsid.Size = New System.Drawing.Size(75, 25)
        Me.setBtSsid.TabIndex = 5
        Me.setBtSsid.Text = "SET"
        Me.setBtSsid.UseVisualStyleBackColor = True
        '
        'getBtSsid
        '
        Me.getBtSsid.Location = New System.Drawing.Point(315, 26)
        Me.getBtSsid.Name = "getBtSsid"
        Me.getBtSsid.Size = New System.Drawing.Size(75, 25)
        Me.getBtSsid.TabIndex = 4
        Me.getBtSsid.Text = "GET"
        Me.getBtSsid.UseVisualStyleBackColor = True
        '
        'btPin
        '
        Me.btPin.Location = New System.Drawing.Point(99, 58)
        Me.btPin.Name = "btPin"
        Me.btPin.Size = New System.Drawing.Size(200, 22)
        Me.btPin.TabIndex = 3
        '
        'btSsid
        '
        Me.btSsid.Location = New System.Drawing.Point(100, 27)
        Me.btSsid.Name = "btSsid"
        Me.btSsid.Size = New System.Drawing.Size(200, 22)
        Me.btSsid.TabIndex = 2
        '
        'LabelPin
        '
        Me.LabelPin.AutoSize = True
        Me.LabelPin.Location = New System.Drawing.Point(18, 62)
        Me.LabelPin.Name = "LabelPin"
        Me.LabelPin.Size = New System.Drawing.Size(28, 17)
        Me.LabelPin.TabIndex = 1
        Me.LabelPin.Text = "Pin"
        '
        'Label4
        '
        Me.Label4.AutoSize = True
        Me.Label4.Location = New System.Drawing.Point(18, 30)
        Me.Label4.Name = "Label4"
        Me.Label4.Size = New System.Drawing.Size(39, 17)
        Me.Label4.TabIndex = 0
        Me.Label4.Text = "SSID"
        '
        'Button2
        '
        Me.Button2.Location = New System.Drawing.Point(899, 426)
        Me.Button2.Name = "Button2"
        Me.Button2.Size = New System.Drawing.Size(130, 50)
        Me.Button2.TabIndex = 5
        Me.Button2.Text = "Clear"
        Me.Button2.UseVisualStyleBackColor = True
        '
        'ComboBox1
        '
        Me.ComboBox1.FormattingEnabled = True
        Me.ComboBox1.Location = New System.Drawing.Point(12, 440)
        Me.ComboBox1.Name = "ComboBox1"
        Me.ComboBox1.Size = New System.Drawing.Size(502, 24)
        Me.ComboBox1.TabIndex = 6
        '
        'CConsole
        '
        Me.AutoScaleDimensions = New System.Drawing.SizeF(8.0!, 16.0!)
        Me.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font
        Me.ClientSize = New System.Drawing.Size(1041, 496)
        Me.Controls.Add(Me.ComboBox1)
        Me.Controls.Add(Me.Button2)
        Me.Controls.Add(Me.GroupBox2)
        Me.Controls.Add(Me.GroupBox1)
        Me.Controls.Add(Me.Button1)
        Me.Controls.Add(Me.ListBox1)
        Me.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedToolWindow
        Me.MaximizeBox = False
        Me.MinimizeBox = False
        Me.Name = "CConsole"
        Me.Text = "Console"
        Me.GroupBox1.ResumeLayout(False)
        Me.GroupBox1.PerformLayout()
        Me.GroupBox2.ResumeLayout(False)
        Me.GroupBox2.PerformLayout()
        Me.ResumeLayout(False)

    End Sub

    Friend WithEvents ListBox1 As ListBox
    Friend WithEvents Button1 As Button
    Friend WithEvents Timer1 As Timer
    Friend WithEvents GroupBox1 As GroupBox
    Friend WithEvents SetWifiPwd As Button
    Friend WithEvents GetWifiPwd As Button
    Friend WithEvents SetWifiSsid As Button
    Friend WithEvents GetWifiSsid As Button
    Friend WithEvents DeviceWiFiPwd As TextBox
    Friend WithEvents DeviceWiFiSsid As TextBox
    Friend WithEvents Label2 As Label
    Friend WithEvents Label1 As Label
    Friend WithEvents wifiEnabled As CheckBox
    Friend WithEvents GroupBox2 As GroupBox
    Friend WithEvents btEnabled As CheckBox
    Friend WithEvents setBtPin As Button
    Friend WithEvents getBtPin As Button
    Friend WithEvents setBtSsid As Button
    Friend WithEvents getBtSsid As Button
    Friend WithEvents btPin As TextBox
    Friend WithEvents btSsid As TextBox
    Friend WithEvents LabelPin As Label
    Friend WithEvents Label4 As Label
    Friend WithEvents Button2 As Button
    Friend WithEvents ComboBox1 As ComboBox
End Class
