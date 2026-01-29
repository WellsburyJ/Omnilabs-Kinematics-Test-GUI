Module Protocol

    Public mpuPresent As Boolean = False
    Public CLOSE As Boolean = False
    Public OPEN As Boolean = True


    Sub ProtoDecode(info As String)

        Debug.Print(info)
        AddLog(info)
        Main.ConsoleDisplay(info)

        'If info.Contains("MPU6050 Found!") Then
        mpuPresent = True
        'End If

        If info.StartsWith("values flex") Then
            Dim Data As String = info.Substring(12)
            Dim values() As String = Data.Split(",")
            Try
                FG1_FlexValue = Val(values(0))
                FG2_FlexValue = Val(values(1))
                FG3_FlexValue = Val(values(2))
                FG4_FlexValue = Val(values(3))
                FG5_FlexValue = Val(values(4))
            Catch ex As Exception
                Debug.Print(ex.Message)
            End Try
        End If

        If info.StartsWith("values press ") Then
            Dim Data As String = info.Substring(13)
            Dim values() As String = Data.Split(",")
            Try
                FG1_PresValue = Val(values(0))
                FG2_PresValue = Val(values(1))
                FG3_PresValue = Val(values(2))
                FG4_PresValue = Val(values(3))
                FG5_PresValue = Val(values(4))
            Catch ex As Exception
                Debug.Print(ex.Message)
            End Try
        End If

        If info.StartsWith("values gyro ") Then
            Dim Data As String = info.Substring(12)
            Dim values() As String = Data.Split(",")
            gyroX = Val(values(1))
            gyroY = Val(values(2))
            gyroZ = Val(values(3))

            accX = Val(values(4))
            accY = Val(values(5))
            accZ = Val(values(6))

            roll = Math.Atan2(accY, accZ)
            roll = Int(roll * 180 / Math.PI)

            'pitch = Math.Atan2(accY, accZ)
            'pitch = Int(pitch * 180 / Math.PI)

            pitch = -(Math.Atan2(accX, Math.Sqrt(accY * accY + accZ * accZ)) * 180.0) / Math.PI
            pitch = Int(pitch)

        End If

        If info.StartsWith("values ypr ") Then
            Dim Data As String = info.Substring(11)
            Dim values() As String = Data.Split(",")
            yaw = Int(Math.PI * Val(values(3)))
            pitch = Int(Math.PI * Val(values(1)))
            roll = Int(Math.PI * Val(values(2)))
        End If

        If info.StartsWith("BT") Then
            Dim infos() As String = info.Split(" ")
            If infos(1).StartsWith("ON") Then
                CConsole.btEnabled.Checked = True
            Else
                CConsole.btEnabled.Checked = False
            End If
        End If

        If info.StartsWith("WiFi") Then
            Dim infos() As String = info.Split(" ")
            If infos(1).StartsWith("ON") Then
                CConsole.btEnabled.Checked = True
            Else
                CConsole.btEnabled.Checked = False
            End If
        End If

    End Sub

End Module
