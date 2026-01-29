Module Log

    Dim LogWriter As IO.StreamWriter

    Public Sub CreateLog()

        Dim file As String = app_path
        file += "/log/"

        Try
            MkDir(file)
        Catch ex As Exception
            Debug.Print(ex.ToString)
        End Try

        file += Format(DateTime.Now.Year, "0000")
        file += "_"
        file += Format(DateTime.Now.Month, "00")
        file += "_"
        file += Format(DateTime.Now.Day, "00")
        file += "_"
        file += Format(DateTime.Now.Hour, "00")
        file += "_"
        file += Format(DateTime.Now.Minute, "00")
        file += "_"
        file += Format(DateTime.Now.Second, "00")
        file += ".log"
        Try
            LogWriter = My.Computer.FileSystem.OpenTextFileWriter(file, False)
        Catch ex As Exception
            Report("E", ex.ToString)
        End Try

    End Sub

    Public Sub AddLog(info As String)

        Try
            LogWriter.WriteLine(info)
        Catch ex As Exception
            Debug.Print(ex.ToString)
        End Try

    End Sub

    Public Sub CloseLog()

        Try
            LogWriter.Close()
        Catch ex As Exception
            Debug.Print(ex.ToString)
        End Try

    End Sub

End Module
