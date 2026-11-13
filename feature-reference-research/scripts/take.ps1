# Move captured YouTube frames from Downloads into the research yt folder as <Prefix>_<t>.jpg.
# Takes finished files named <Prefix>_<t>.jpg when all are present; otherwise the newest *.tmp/<Prefix>* files, oldest first.
# usage (from PowerShell): & take.ps1 -Prefix game_yt -Times 40,95,180 -Dest T:\Work\docs\<slug>\yt
param([string]$Prefix, [int[]]$Times, [string]$Dest)
$d = Join-Path $env:USERPROFILE 'Downloads'
New-Item -ItemType Directory -Force $Dest | Out-Null
$named = $Times | ForEach-Object { Join-Path $d ("{0}_{1}.jpg" -f $Prefix, $_) }
if (($named | Where-Object { Test-Path $_ }).Count -eq $Times.Count) {
    $files = $named | ForEach-Object { Get-Item $_ }
} else {
    $files = Get-ChildItem $d | Where-Object { ($_.Extension -eq '.tmp' -or $_.Name -like "$Prefix*") -and $_.LastWriteTime -gt (Get-Date).AddMinutes(-15) } |
        Sort-Object LastWriteTime | Select-Object -Last $Times.Count
}
for ($i = 0; $i -lt $files.Count; $i++) {
    $dst = Join-Path $Dest ("{0}_{1}.jpg" -f $Prefix, $Times[$i])
    $size = $files[$i].Length
    Move-Item $files[$i].FullName $dst -Force
    "{0} <- {1} ({2} bytes)" -f (Split-Path $dst -Leaf), $files[$i].Name, $size
}
