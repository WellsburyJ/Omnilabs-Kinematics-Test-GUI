Imports System.Net
Imports System.Net.Sockets
Imports System.Text
Public Class TcpSocket

    Public s As New Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp)
    Public parent As Main
    Public buf() As Byte
    Public l_buf As Integer
    Dim so As StateObject

    Public Class StateObject
        Public workSocket As Socket = Nothing
        Public Const BUFFER_SIZE As Integer = 1024
        Public buffer(BUFFER_SIZE) As Byte
        Public sb As New StringBuilder
    End Class 'StateObject

    Public Function TcpConnect(ByVal adr As String, ByVal p As Integer) As Boolean

        Dim lipa As IPHostEntry
        Dim lep As IPEndPoint

        If adr.Equals("127.0.0.1") Then
            lep = New IPEndPoint(Net.IPAddress.Loopback, p)
        Else
            lipa = Dns.GetHostEntry(adr)
            lep = New IPEndPoint(lipa.AddressList(0), p)
        End If

        s = New Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp)
        Try
            's.Connect(lep)
            so = New StateObject With {
                .workSocket = s
            }

            s.BeginConnect(lep, New AsyncCallback(AddressOf Connect_Callback), so)
            Return True
        Catch e As Exception
            Debug.Print(e.Message)
            Return False
        End Try

    End Function 'Connect
    Private Sub Connect_Callback(ByVal ar As IAsyncResult)

        Try
            s.BeginReceive(so.buffer, 0, StateObject.BUFFER_SIZE, 0, New AsyncCallback(AddressOf ReceiveCallback), so)
        Catch ex As Exception
            Debug.Print(ex.Message)
        End Try

    End Sub

    Sub TcpSend(ByVal b() As Byte, ByVal l As Integer)

        buf = b
        l_buf = l
        If s.Connected = True Then
            Try
                s.Send(buf, l_buf, SocketFlags.None)
            Catch ex As Exception
                Debug.Print(ex.Message)
            End Try
        End If

    End Sub

    Private Sub ReceiveCallback(ByVal ar As IAsyncResult)

        'Dim so As StateObject = CType(ar.AsyncState, StateObject)
        Dim s As Socket = so.workSocket

        Dim read As Integer
        Try
            read = s.EndReceive(ar)
        Catch ex As Exception
            Debug.Print(ex.Message)
            Return
        End Try

        If read > 0 Then
            so.sb.Append(Encoding.ASCII.GetString(so.buffer, 0, read))
            'parent.tcpRec(so.buffer, read)
            s.BeginReceive(so.buffer, 0, StateObject.BUFFER_SIZE, 0, New AsyncCallback(AddressOf ReceiveCallback), so)
        End If

    End Sub
End Class

