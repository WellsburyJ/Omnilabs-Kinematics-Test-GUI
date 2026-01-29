Imports System.Net
Imports System.Net.Sockets
Imports System.Text
Imports System.Net.Sockets.MulticastOption
Public Class UdpSocket

    Public s As Socket
    Public parent As Main
    Public ttl As Integer
    Public tos As Integer

    Public Class StateObject
        Public workSocket As Socket = Nothing
        Public Const BUFFER_SIZE As Integer = 1024
        Public buffer(BUFFER_SIZE) As Byte
        Public sb As New StringBuilder
    End Class 'StateObject

    Sub Init(ByVal port As Integer)

        ' Create the UDP socket

        s = New Socket(AddressFamily.InterNetwork, SocketType.Dgram, ProtocolType.Udp)

        Dim ad As IPAddress
        Dim ep As IPEndPoint
        ad = IPAddress.Any
        ep = New IPEndPoint(ad, port)

        Try
            s.Bind(ep)

            Dim so As New StateObject With {
                .workSocket = s
            }
            s.BeginReceive(so.buffer, 0, StateObject.BUFFER_SIZE, 0, New AsyncCallback(AddressOf ReceiveCallback), so)

        Catch ex As Exception
            Debug.Print(ex.ToString)
        End Try

    End Sub
    Private Sub ReceiveCallback(ByVal ar As IAsyncResult)

        Dim so As StateObject = CType(ar.AsyncState, StateObject)
        Dim s As Socket = so.workSocket

        Try

            Dim read As Integer = s.EndReceive(ar)

            If read > 0 Then
                so.sb.Append(Encoding.ASCII.GetString(so.buffer, 0, read))

                Dim strContent As String
                strContent = so.sb.ToString()
                strContent = Encoding.ASCII.GetString(so.buffer, 0, read)

                s.BeginReceive(so.buffer, 0, StateObject.BUFFER_SIZE, 0, New AsyncCallback(AddressOf ReceiveCallback), so)
            Else
                If so.sb.Length > 1 Then
                    'All the data has been read, so displays it to the console
                    'Dim strContent As String
                    'strContent = so.sb.ToString()
                End If
                s.Close()
            End If

        Catch ex As Exception
            Debug.Print(ex.ToString)
        End Try

    End Sub

    Sub Send(ByVal buf() As Byte, ByVal l As Integer, ByVal adr As String, ByVal p As Integer)


        Dim so2 As New StateObject()
        Dim rep As IPEndPoint

        so2.workSocket = s

        Dim ipadr As IPAddress
        ipadr = IPAddress.Parse(adr)
        rep = New IPEndPoint(ipadr, p)

        's.SetSocketOption(SocketOptionLevel.IP, SocketOptionName.MulticastTimeToLive, ttl)
        's.SetSocketOption(SocketOptionLevel.IP, SocketOptionName.TypeOfService, tos)

        Try
            s.BeginSendTo(buf, 0, l, 0, rep, New AsyncCallback(AddressOf SendCallback), so2)
        Catch ex As Exception

        End Try

    End Sub

    Private Sub SendCallback(ByVal ar As IAsyncResult)


    End Sub

    Sub AddMulticast(ByVal m As String)

        Dim group As IPAddress

        group = IPAddress.Parse(m)
        Dim mo As New MulticastOption(group)

        Try
            s.SetSocketOption(SocketOptionLevel.IP, SocketOptionName.AddMembership, mo)
        Catch ex As Exception
            MsgBox("Unable to receive " + m + " !" +
                    vbCrLf + "Please check IP connection," +
                    vbCrLf + "application will close", MsgBoxStyle.Critical)
            parent.Close()
        End Try

    End Sub


End Class
