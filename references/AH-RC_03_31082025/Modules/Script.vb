Module Script

    Public commandsList As List(Of String)
    Dim loopIndex As List(Of Integer)
    Dim wloop As Integer
    Dim worg As Integer = 0
    Public scriptIndex As Integer

    Public Function ReadScriptFile(file As String) As Boolean

        commandsList = New List(Of String)
        loopIndex = New List(Of Integer)
        Dim reader As IO.StreamReader = My.Computer.FileSystem.OpenTextFileReader(file)
        Dim line As String
        Do
            line = reader.ReadLine
            If line IsNot Nothing Then
                Do
                    If line.StartsWith(vbTab) Then
                        line = Mid(line, 2)
                    Else
                        Exit Do
                    End If
                Loop
                If Not LTrim(line).StartsWith("#") Then
                    commandsList.Add(LTrim(line))
                End If
            End If
        Loop Until line Is Nothing
        reader.Close()
        scriptIndex = 0
        Return True

    End Function

    Public Sub ExecuteLine()

        Debug.Print(commandsList(scriptIndex))

        Dim args() As String
        Try
            args = commandsList(scriptIndex).Split(" ")
        Catch ex As Exception
            Return
        End Try

        If args(0).StartsWith("target") Then

        End If

        If args(0).StartsWith("reset") Then
            Main.Reset()
        End If

        If args(0).StartsWith("release") Then
            Dim finger As Integer = 0
            If args(1).StartsWith("finger") Then
                finger = Val(args(2))
                Main.Release(finger)
            End If
        End If

        If args(0).StartsWith("do") Then
            loopIndex.Add(scriptIndex)
            wloop = 0
        End If

        If args(0).StartsWith("loop") Then
            Dim i As Integer = loopIndex.Count - 1
            Dim w As Integer = Val(args(1))
            If wloop < w Then wloop = w
            w -= 1
            If w > 0 Then
                commandsList(scriptIndex) = "loop" + Str(w)
                scriptIndex = loopIndex.Item(i)
            Else
                commandsList(scriptIndex) = "loop" + Str(wloop)
                loopIndex.RemoveAt(i)
            End If
        End If

        If args(0).StartsWith("wait") Then
            Dim w As Integer = Val(args(1))
            If (w > worg) Then worg = w
            w -= 1
            If w > 0 Then
                commandsList(scriptIndex) = "wait" + Str(w)
                Return
            Else
                commandsList(scriptIndex) = "wait" + Str(worg)
                worg = 0
            End If
        End If

        '
        ' set functions
        ' 
        'ex: set pump 1 to 2
        If args(0).StartsWith("set") Then
            Dim finger As Integer = Val(args(2))

            If args(1).StartsWith("pump") Then
                Main.SetPumpOrder(finger, Val(args(4)))
            End If

            If args(1).StartsWith("valve") Then
                Main.SetValve(finger, Left(args(4), 1))
            End If

            If args(1).StartsWith("vibr") Then
                Dim status As Boolean = False
                If args(4) = "on" Then
                    status = True
                End If
                Main.SetVibrator(finger, status)
            End If

        End If

        scriptIndex += 1

    End Sub

End Module
