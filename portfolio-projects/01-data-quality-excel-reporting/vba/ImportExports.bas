Attribute VB_Name = "ImportExports"
Option Explicit

'Import this module into a copy saved as .xlsm. Originals are opened read-only.
Public Sub ImportThreeExports()
    Dim names As Variant, sheets As Variant, capacities As Variant
    Dim stage(0 To 2) As Variant, i As Long, j As Long, n As Long, c As Long
    Dim source As Workbook, target As Worksheet, file As Variant, header As Variant
    Dim map As Object, input As Variant, output() As Variant, expected As String
    Dim oldCalculation As XlCalculation, oldEvents As Boolean, oldScreen As Boolean
    Dim failure As String
    names = Array("orders", "clients", "payments")
    sheets = Array("01_orders_raw", "02_clients_raw", "03_payments_raw")
    On Error GoTo Failed
    capacities = Array(ThisWorkbook.Worksheets("09_parameters").Range("B9").Value2, _
                       ThisWorkbook.Worksheets("09_parameters").Range("B10").Value2, _
                       ThisWorkbook.Worksheets("09_parameters").Range("B11").Value2)
    oldCalculation = Application.Calculation
    oldEvents = Application.EnableEvents
    oldScreen = Application.ScreenUpdating
    On Error GoTo Failed
    'Validate all three inputs before writing any destination cells.
    For i = 0 To 2
        file = Application.GetOpenFilename("Excel files (*.xlsx),*.xlsx", , "Select " & names(i) & " export")
        If VarType(file) = vbBoolean Then GoTo Finally
        Set source = Workbooks.Open(CStr(file), UpdateLinks:=0, ReadOnly:=True)
        input = source.Worksheets(1).UsedRange.Value2
        If Not IsArray(input) Then Err.Raise vbObjectError + 1, , "Export has no table"
        Set target = ThisWorkbook.Worksheets(sheets(i))
        c = target.ListObjects(1).ListColumns.Count
        Set map = CreateObject("Scripting.Dictionary")
        map.CompareMode = vbTextCompare
        For j = 1 To UBound(input, 2)
            expected = Trim$(CStr(input(1, j)))
            If map.Exists(expected) Then Err.Raise vbObjectError + 2, , "Duplicate header: " & expected
            map.Add expected, j
        Next j
        n = UBound(input, 1) - 1
        If n < 1 Or n > CLng(capacities(i)) Then Err.Raise vbObjectError + 3, , "Row count outside workbook capacity: " & names(i)
        ReDim output(1 To n, 1 To c)
        For j = 1 To c
            header = target.Cells(1, j).Value2
            If Not map.Exists(CStr(header)) Then Err.Raise vbObjectError + 4, , "Missing column: " & CStr(header)
            Dim row As Long
            For row = 1 To n
                output(row, j) = input(row + 1, map(CStr(header)))
            Next row
        Next j
        stage(i) = output
        source.Close SaveChanges:=False
        Set source = Nothing
    Next i
    Application.EnableEvents = False
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    For i = 0 To 2
        Set target = ThisWorkbook.Worksheets(sheets(i))
        target.ListObjects(1).DataBodyRange.ClearContents
        output = stage(i)
        target.Cells(2, 1).Resize(UBound(output, 1), UBound(output, 2)).Value2 = output
    Next i
    ThisWorkbook.Worksheets("09_parameters").Activate
    ThisWorkbook.Worksheets("09_parameters").Range("B2").Select
    Application.CalculateFull
    MsgBox "Imported. Set the reporting cutoff in 09_parameters!B2; inspect 05_errors and capacity status.", vbInformation
    GoTo Finally
Failed:
    failure = Err.Description
Finally:
    On Error Resume Next
    If Not source Is Nothing Then source.Close SaveChanges:=False
    Application.Calculation = oldCalculation
    Application.EnableEvents = oldEvents
    Application.ScreenUpdating = oldScreen
    On Error GoTo 0
    If Len(failure) > 0 Then MsgBox failure, vbExclamation
End Sub
