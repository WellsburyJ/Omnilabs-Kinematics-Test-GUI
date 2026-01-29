Module Comm

    Dim CommBuffer As String = ""

    Sub CommTransmit(buffer() As Byte)

        Main.SerialPort1.Write(buffer, 0, buffer.Length)

    End Sub

    Sub CommReceive(buffer() As Byte)

        Dim n As Integer
        For n = 0 To buffer.Length - 1
            If buffer(n) > 0 Then CommBuffer += Chr(buffer(n))
            If CommBuffer.EndsWith(vbLf) Then
                ProtoDecode(Left(CommBuffer, CommBuffer.Length - 1))

                '                Dim info() As String = serialBuffer.Split(vbLf)
                '                Dim i As Integer
                '                For i = 0 To info.Length - 1
                '                ProtoDecode(info(i))
                '        Next

                CommBuffer = ""

            End If
        Next

    End Sub

End Module
