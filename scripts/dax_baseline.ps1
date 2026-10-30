# Runs the regression query of docs/dax-quality.md against the model open in Power BI Desktop and
# writes the result to a CSV: one row per year, one column per used numeric measure.
# Run it before a DAX change and after it, then compare the two files:
#   python scripts/dax_audit.py --baseline baseline.dax
#   powershell -File scripts/dax_baseline.ps1 -QueryFile baseline.dax -OutCsv before.csv
#   ... the change, Desktop reopened ...
#   powershell -File scripts/dax_baseline.ps1 -QueryFile baseline.dax -OutCsv after.csv
#   python scripts/dax_audit.py --compare before.csv after.csv
# Read-only: it only queries the local model. With one Desktop open, the port is found by itself.
param([string]$QueryFile, [string]$OutCsv, [int]$Port = 0)

$desktop = (Get-AppxPackage Microsoft.MicrosoftPowerBIDesktop | Select-Object -First 1).InstallLocation
if (-not $desktop) { throw "Power BI Desktop (Store) not found" }
Add-Type -Path (Join-Path $desktop "bin\Microsoft.PowerBI.AdomdClient.dll")
if ($Port -eq 0) {
    $engine = Get-Process msmdsrv -ErrorAction Stop | Select-Object -First 1
    $Port = (Get-NetTCPConnection -State Listen -OwningProcess $engine.Id | Select-Object -First 1).LocalPort
}

# one query: every measure of the baseline file in a single SUMMARIZECOLUMNS by year
$columns = Select-String -Path $QueryFile -Pattern '^\s+(".*", \[.*\]),?$' | ForEach-Object { $_.Matches[0].Groups[1].Value }
$query = "EVALUATE`nSUMMARIZECOLUMNS(`n    DimDate[Year],`n    " + ($columns -join ",`n    ") + "`n)"

$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$Port")
$conn.Open()
$cmd = $conn.CreateCommand()
$cmd.CommandText = $query
$cmd.CommandTimeout = 600
$reader = $cmd.ExecuteReader()
$inv = [Globalization.CultureInfo]::InvariantCulture
$sb = New-Object Text.StringBuilder
$names = @(); for ($i = 0; $i -lt $reader.FieldCount; $i++) { $names += $reader.GetName($i) }
[void]$sb.AppendLine(($names | ForEach-Object { '"' + $_.Replace('"', '""') + '"' }) -join ',')
while ($reader.Read()) {
    $vals = @()
    for ($i = 0; $i -lt $reader.FieldCount; $i++) {
        $v = $reader.GetValue($i)
        if ($v -is [DBNull] -or $null -eq $v) { $vals += '' }
        elseif ($v -is [double]) { $vals += '"' + $v.ToString('R', $inv) + '"' }
        elseif ($v -is [IFormattable]) { $vals += '"' + $v.ToString($null, $inv) + '"' }
        else { $vals += '"' + $v.ToString().Replace('"', '""') + '"' }
    }
    [void]$sb.AppendLine($vals -join ',')
}
$reader.Close(); $conn.Close()
[IO.File]::WriteAllText($OutCsv, $sb.ToString())
Write-Output "$($columns.Count) measures written to $OutCsv"
