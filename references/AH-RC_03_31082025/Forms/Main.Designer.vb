<Global.Microsoft.VisualBasic.CompilerServices.DesignerGenerated()>
Partial Class Main
    Inherits System.Windows.Forms.Form

    'Form overrides dispose to clean up the component list.
    <System.Diagnostics.DebuggerNonUserCode()>
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
    <System.Diagnostics.DebuggerStepThrough()>
    Private Sub InitializeComponent()
        Me.components = New System.ComponentModel.Container()
        Dim resources As System.ComponentModel.ComponentResourceManager = New System.ComponentModel.ComponentResourceManager(GetType(Main))
        Me.Timer1 = New System.Windows.Forms.Timer(Me.components)
        Me.zeroBtn = New System.Windows.Forms.Button()
        Me.ToolStrip1 = New System.Windows.Forms.ToolStrip()
        Me.SettingsBtn = New System.Windows.Forms.ToolStripButton()
        Me.ToolStripSeparator1 = New System.Windows.Forms.ToolStripSeparator()
        Me.ConnectBtn = New System.Windows.Forms.ToolStripButton()
        Me.ToolStripSeparator2 = New System.Windows.Forms.ToolStripSeparator()
        Me.ToolStripButton2 = New System.Windows.Forms.ToolStripButton()
        Me.ToolStripSeparator5 = New System.Windows.Forms.ToolStripSeparator()
        Me.ScriptButton = New System.Windows.Forms.ToolStripButton()
        Me.ToolStripSeparator4 = New System.Windows.Forms.ToolStripSeparator()
        Me.LogBtn = New System.Windows.Forms.ToolStripButton()
        Me.ToolStripSeparator6 = New System.Windows.Forms.ToolStripSeparator()
        Me.AboutBtn = New System.Windows.Forms.ToolStripButton()
        Me.StatusStrip1 = New System.Windows.Forms.StatusStrip()
        Me.Status1 = New System.Windows.Forms.ToolStripStatusLabel()
        Me.Status2 = New System.Windows.Forms.ToolStripStatusLabel()
        Me.StatusLabel = New System.Windows.Forms.ToolStripStatusLabel()
        Me.SerialPort1 = New System.IO.Ports.SerialPort(Me.components)
        Me.GB_MPU = New System.Windows.Forms.GroupBox()
        Me.Label4 = New System.Windows.Forms.Label()
        Me.ext = New System.Windows.Forms.CheckBox()
        Me.Label2 = New System.Windows.Forms.Label()
        Me.Label1 = New System.Windows.Forms.Label()
        Me.MpuState = New System.Windows.Forms.Label()
        Me.TimerScript = New System.Windows.Forms.Timer(Me.components)
        Me.OpenFileDialog1 = New System.Windows.Forms.OpenFileDialog()
        Me.VB0 = New System.Windows.Forms.CheckBox()
        Me.ToolStrip1.SuspendLayout()
        Me.StatusStrip1.SuspendLayout()
        Me.GB_MPU.SuspendLayout()
        Me.SuspendLayout()
        '
        'Timer1
        '
        Me.Timer1.Enabled = True
        '
        'zeroBtn
        '
        Me.zeroBtn.Image = CType(resources.GetObject("zeroBtn.Image"), System.Drawing.Image)
        Me.zeroBtn.Location = New System.Drawing.Point(749, 291)
        Me.zeroBtn.Margin = New System.Windows.Forms.Padding(3, 2, 3, 2)
        Me.zeroBtn.Name = "zeroBtn"
        Me.zeroBtn.Size = New System.Drawing.Size(71, 64)
        Me.zeroBtn.TabIndex = 6
        Me.zeroBtn.UseVisualStyleBackColor = True
        '
        'ToolStrip1
        '
        Me.ToolStrip1.ImageScalingSize = New System.Drawing.Size(24, 24)
        Me.ToolStrip1.Items.AddRange(New System.Windows.Forms.ToolStripItem() {Me.SettingsBtn, Me.ToolStripSeparator1, Me.ConnectBtn, Me.ToolStripSeparator2, Me.ToolStripButton2, Me.ToolStripSeparator5, Me.ScriptButton, Me.ToolStripSeparator4, Me.LogBtn, Me.ToolStripSeparator6, Me.AboutBtn})
        Me.ToolStrip1.Location = New System.Drawing.Point(0, 0)
        Me.ToolStrip1.Name = "ToolStrip1"
        Me.ToolStrip1.Size = New System.Drawing.Size(878, 31)
        Me.ToolStrip1.TabIndex = 7
        Me.ToolStrip1.Text = "ToolStrip1"
        '
        'SettingsBtn
        '
        Me.SettingsBtn.Image = CType(resources.GetObject("SettingsBtn.Image"), System.Drawing.Image)
        Me.SettingsBtn.ImageTransparentColor = System.Drawing.Color.Magenta
        Me.SettingsBtn.Name = "SettingsBtn"
        Me.SettingsBtn.Size = New System.Drawing.Size(90, 28)
        Me.SettingsBtn.Text = "Settings"
        '
        'ToolStripSeparator1
        '
        Me.ToolStripSeparator1.Name = "ToolStripSeparator1"
        Me.ToolStripSeparator1.Size = New System.Drawing.Size(6, 31)
        '
        'ConnectBtn
        '
        Me.ConnectBtn.Image = CType(resources.GetObject("ConnectBtn.Image"), System.Drawing.Image)
        Me.ConnectBtn.ImageTransparentColor = System.Drawing.Color.Magenta
        Me.ConnectBtn.Name = "ConnectBtn"
        Me.ConnectBtn.Size = New System.Drawing.Size(91, 28)
        Me.ConnectBtn.Text = "Connect"
        '
        'ToolStripSeparator2
        '
        Me.ToolStripSeparator2.Name = "ToolStripSeparator2"
        Me.ToolStripSeparator2.Size = New System.Drawing.Size(6, 31)
        '
        'ToolStripButton2
        '
        Me.ToolStripButton2.Image = CType(resources.GetObject("ToolStripButton2.Image"), System.Drawing.Image)
        Me.ToolStripButton2.ImageTransparentColor = System.Drawing.Color.Magenta
        Me.ToolStripButton2.Name = "ToolStripButton2"
        Me.ToolStripButton2.Size = New System.Drawing.Size(90, 28)
        Me.ToolStripButton2.Text = "Console"
        '
        'ToolStripSeparator5
        '
        Me.ToolStripSeparator5.Name = "ToolStripSeparator5"
        Me.ToolStripSeparator5.Size = New System.Drawing.Size(6, 31)
        '
        'ScriptButton
        '
        Me.ScriptButton.Image = CType(resources.GetObject("ScriptButton.Image"), System.Drawing.Image)
        Me.ScriptButton.ImageTransparentColor = System.Drawing.Color.Magenta
        Me.ScriptButton.Name = "ScriptButton"
        Me.ScriptButton.Size = New System.Drawing.Size(96, 28)
        Me.ScriptButton.Text = "Exercises"
        '
        'ToolStripSeparator4
        '
        Me.ToolStripSeparator4.Name = "ToolStripSeparator4"
        Me.ToolStripSeparator4.Size = New System.Drawing.Size(6, 31)
        '
        'LogBtn
        '
        Me.LogBtn.Image = CType(resources.GetObject("LogBtn.Image"), System.Drawing.Image)
        Me.LogBtn.ImageTransparentColor = System.Drawing.Color.Magenta
        Me.LogBtn.Name = "LogBtn"
        Me.LogBtn.Size = New System.Drawing.Size(62, 28)
        Me.LogBtn.Text = "Log"
        '
        'ToolStripSeparator6
        '
        Me.ToolStripSeparator6.Name = "ToolStripSeparator6"
        Me.ToolStripSeparator6.Size = New System.Drawing.Size(6, 31)
        '
        'AboutBtn
        '
        Me.AboutBtn.Image = CType(resources.GetObject("AboutBtn.Image"), System.Drawing.Image)
        Me.AboutBtn.ImageTransparentColor = System.Drawing.Color.Magenta
        Me.AboutBtn.Name = "AboutBtn"
        Me.AboutBtn.Size = New System.Drawing.Size(87, 28)
        Me.AboutBtn.Text = "About..."
        Me.AboutBtn.ToolTipText = "About..."
        '
        'StatusStrip1
        '
        Me.StatusStrip1.ImageScalingSize = New System.Drawing.Size(20, 20)
        Me.StatusStrip1.Items.AddRange(New System.Windows.Forms.ToolStripItem() {Me.Status1, Me.Status2, Me.StatusLabel})
        Me.StatusStrip1.Location = New System.Drawing.Point(0, 425)
        Me.StatusStrip1.Name = "StatusStrip1"
        Me.StatusStrip1.Padding = New System.Windows.Forms.Padding(1, 0, 12, 0)
        Me.StatusStrip1.Size = New System.Drawing.Size(878, 24)
        Me.StatusStrip1.TabIndex = 8
        Me.StatusStrip1.Text = "StatusStrip1"
        '
        'Status1
        '
        Me.Status1.AutoSize = False
        Me.Status1.Enabled = False
        Me.Status1.Image = CType(resources.GetObject("Status1.Image"), System.Drawing.Image)
        Me.Status1.Name = "Status1"
        Me.Status1.Size = New System.Drawing.Size(70, 18)
        Me.Status1.Text = "X"
        '
        'Status2
        '
        Me.Status2.AutoSize = False
        Me.Status2.Enabled = False
        Me.Status2.Image = CType(resources.GetObject("Status2.Image"), System.Drawing.Image)
        Me.Status2.Name = "Status2"
        Me.Status2.Size = New System.Drawing.Size(70, 18)
        Me.Status2.Text = "X"
        '
        'StatusLabel
        '
        Me.StatusLabel.AutoSize = False
        Me.StatusLabel.BackColor = System.Drawing.SystemColors.Control
        Me.StatusLabel.BorderSides = CType((((System.Windows.Forms.ToolStripStatusLabelBorderSides.Left Or System.Windows.Forms.ToolStripStatusLabelBorderSides.Top) _
            Or System.Windows.Forms.ToolStripStatusLabelBorderSides.Right) _
            Or System.Windows.Forms.ToolStripStatusLabelBorderSides.Bottom), System.Windows.Forms.ToolStripStatusLabelBorderSides)
        Me.StatusLabel.DisplayStyle = System.Windows.Forms.ToolStripItemDisplayStyle.Text
        Me.StatusLabel.Font = New System.Drawing.Font("Segoe UI", 9.0!, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.StatusLabel.Name = "StatusLabel"
        Me.StatusLabel.Size = New System.Drawing.Size(370, 18)
        Me.StatusLabel.Text = "   "
        Me.StatusLabel.TextAlign = System.Drawing.ContentAlignment.MiddleLeft
        '
        'SerialPort1
        '
        Me.SerialPort1.BaudRate = 115200
        Me.SerialPort1.WriteTimeout = 1000
        '
        'GB_MPU
        '
        Me.GB_MPU.Controls.Add(Me.Label4)
        Me.GB_MPU.Controls.Add(Me.ext)
        Me.GB_MPU.Controls.Add(Me.Label2)
        Me.GB_MPU.Controls.Add(Me.Label1)
        Me.GB_MPU.Controls.Add(Me.MpuState)
        Me.GB_MPU.FlatStyle = System.Windows.Forms.FlatStyle.Popup
        Me.GB_MPU.Location = New System.Drawing.Point(715, 60)
        Me.GB_MPU.Margin = New System.Windows.Forms.Padding(3, 2, 3, 2)
        Me.GB_MPU.Name = "GB_MPU"
        Me.GB_MPU.Padding = New System.Windows.Forms.Padding(3, 2, 3, 2)
        Me.GB_MPU.Size = New System.Drawing.Size(155, 140)
        Me.GB_MPU.TabIndex = 10
        Me.GB_MPU.TabStop = False
        Me.GB_MPU.Text = "MPU"
        '
        'Label4
        '
        Me.Label4.AutoSize = True
        Me.Label4.Location = New System.Drawing.Point(25, 108)
        Me.Label4.Name = "Label4"
        Me.Label4.Size = New System.Drawing.Size(36, 17)
        Me.Label4.TabIndex = 4
        Me.Label4.Text = "yaw:"
        '
        'ext
        '
        Me.ext.AutoSize = True
        Me.ext.Location = New System.Drawing.Point(12, 26)
        Me.ext.Margin = New System.Windows.Forms.Padding(4)
        Me.ext.Name = "ext"
        Me.ext.Size = New System.Drawing.Size(48, 21)
        Me.ext.TabIndex = 3
        Me.ext.Text = "3D"
        Me.ext.UseVisualStyleBackColor = True
        '
        'Label2
        '
        Me.Label2.AutoSize = True
        Me.Label2.Location = New System.Drawing.Point(25, 87)
        Me.Label2.Name = "Label2"
        Me.Label2.Size = New System.Drawing.Size(42, 17)
        Me.Label2.TabIndex = 2
        Me.Label2.Text = "pitch:"
        '
        'Label1
        '
        Me.Label1.AutoSize = True
        Me.Label1.Location = New System.Drawing.Point(25, 64)
        Me.Label1.Name = "Label1"
        Me.Label1.Size = New System.Drawing.Size(31, 17)
        Me.Label1.TabIndex = 1
        Me.Label1.Text = "roll:"
        '
        'MpuState
        '
        Me.MpuState.BackColor = System.Drawing.SystemColors.Control
        Me.MpuState.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D
        Me.MpuState.FlatStyle = System.Windows.Forms.FlatStyle.Popup
        Me.MpuState.Location = New System.Drawing.Point(75, 30)
        Me.MpuState.Name = "MpuState"
        Me.MpuState.Size = New System.Drawing.Size(45, 15)
        Me.MpuState.TabIndex = 0
        '
        'TimerScript
        '
        Me.TimerScript.Interval = 1000
        '
        'OpenFileDialog1
        '
        Me.OpenFileDialog1.FileName = "OpenFileDialog1"
        '
        'VB0
        '
        Me.VB0.CheckAlign = System.Drawing.ContentAlignment.TopCenter
        Me.VB0.Location = New System.Drawing.Point(735, 229)
        Me.VB0.Margin = New System.Windows.Forms.Padding(4)
        Me.VB0.Name = "VB0"
        Me.VB0.Size = New System.Drawing.Size(99, 38)
        Me.VB0.TabIndex = 11
        Me.VB0.Text = "Palm Vibrator"
        Me.VB0.TextAlign = System.Drawing.ContentAlignment.MiddleCenter
        Me.VB0.UseVisualStyleBackColor = True
        '
        'Main
        '
        Me.AutoScaleDimensions = New System.Drawing.SizeF(8.0!, 16.0!)
        Me.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font
        Me.ClientSize = New System.Drawing.Size(878, 449)
        Me.Controls.Add(Me.VB0)
        Me.Controls.Add(Me.GB_MPU)
        Me.Controls.Add(Me.StatusStrip1)
        Me.Controls.Add(Me.ToolStrip1)
        Me.Controls.Add(Me.zeroBtn)
        Me.FormBorderStyle = System.Windows.Forms.FormBorderStyle.Fixed3D
        Me.Margin = New System.Windows.Forms.Padding(4)
        Me.MaximizeBox = False
        Me.Name = "Main"
        Me.Text = "AH-RC"
        Me.ToolStrip1.ResumeLayout(False)
        Me.ToolStrip1.PerformLayout()
        Me.StatusStrip1.ResumeLayout(False)
        Me.StatusStrip1.PerformLayout()
        Me.GB_MPU.ResumeLayout(False)
        Me.GB_MPU.PerformLayout()
        Me.ResumeLayout(False)
        Me.PerformLayout()

    End Sub
    Friend WithEvents Timer1 As Timer
    Friend WithEvents zeroBtn As Button
    Friend WithEvents ToolStrip1 As ToolStrip
    Friend WithEvents ConnectBtn As ToolStripButton
    Friend WithEvents SettingsBtn As ToolStripButton
    Friend WithEvents ToolStripSeparator1 As ToolStripSeparator
    Friend WithEvents StatusStrip1 As StatusStrip
    Friend WithEvents ToolStripSeparator2 As ToolStripSeparator
    Friend WithEvents AboutBtn As ToolStripButton
    Friend WithEvents Status1 As ToolStripStatusLabel
    Friend WithEvents SerialPort1 As IO.Ports.SerialPort
    Friend WithEvents Status2 As ToolStripStatusLabel
    Friend WithEvents StatusLabel As ToolStripStatusLabel
    Friend WithEvents ToolStripButton2 As ToolStripButton
    Friend WithEvents ToolStripSeparator4 As ToolStripSeparator
    Friend WithEvents GB_MPU As GroupBox
    Friend WithEvents MpuState As Label
    Friend WithEvents Label1 As Label
    Friend WithEvents Label2 As Label
    Friend WithEvents TimerScript As Timer
    Friend WithEvents ToolStripSeparator5 As ToolStripSeparator
    Friend WithEvents ScriptButton As ToolStripButton
    Friend WithEvents OpenFileDialog1 As OpenFileDialog
    Friend WithEvents ext As CheckBox
    Friend WithEvents LogBtn As ToolStripButton
    Friend WithEvents ToolStripSeparator6 As ToolStripSeparator
    Friend WithEvents VB0 As CheckBox
    Friend WithEvents Label4 As Label
End Class
