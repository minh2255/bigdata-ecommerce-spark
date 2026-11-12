$ErrorActionPreference = 'Stop'
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new()
$root = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$ev = Join-Path $root 'docs/evidence/tv2'
$checks = [Collections.Generic.List[object]]::new()
function ReadJson($path) { Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json }
function Check($name, $ok) {
    $checks.Add([PSCustomObject]@{ check = $name; passed = [bool]$ok })
    if (!$ok) { throw "Failed: $name" }
}
function Cells($text, $prefix) {
    $line = @($text.Split("`n") | Where-Object { $_.StartsWith($prefix) })[0]
    if (!$line) { throw "Missing row: $prefix" }
    ,$line.Trim().Trim('|').Split('|').ForEach({ $_.Trim().Replace('**', '') })
}
function IntValue($s) { [long]$s.Replace('.', '') }
function Grouped($n) { ([long]$n).ToString('N0', [Globalization.CultureInfo]::GetCultureInfo('de-DE')) }
$raw = ReadJson "$ev/profiling_raw.json"
$clean = ReadJson "$ev/profiling_clean.json"
$merged = ReadJson "$ev/cleaning_metrics_merged.json"
$kb = Import-Csv "$ev/kb3.csv"
$doc = Get-Content "$root/docs/tv2/ch06_kb3_kb5.md" -Raw -Encoding UTF8
foreach ($metric in @('count_seconds', 'sum_price_seconds')) {
    $label = if ($metric -eq 'count_seconds') { '`count()`' } else { '`sum(price)`' }
    foreach ($fmt in @('csv', 'parquet')) {
        $caption = if ($fmt -eq 'csv') { 'CSV' } else { 'Parquet' }
        $row = Cells $doc "| $label | $caption |"
        $runs = @('1', '2', '3', 'mean')
        for ($i = 0; $i -lt 4; $i++) {
            $v = @($kb | Where-Object { $_.metric -eq $metric -and $_.format -eq $fmt -and $_.run -eq $runs[$i] })[0].value
            Check "KB3 $metric/$fmt/$($runs[$i])" ($row[$i + 2] -ceq $v)
        }
    }
}
foreach ($metric in @('size_ratio', 'count_speedup', 'sum_price_speedup')) {
    $v = @($kb | Where-Object { $_.metric -eq $metric })[0].value
    Check "KB3 $metric precision" ($doc.Contains($v))
}
foreach ($fmt in @('csv', 'parquet')) {
    $v = @($kb | Where-Object { $_.metric -eq 'size' -and $_.format -eq $fmt })[0].value
    Check "KB3 $fmt bytes" ($doc.Contains((Grouped $v) + ' byte'))
}
$ingest = Import-Csv "$ev/ingest_log.csv"
Check 'Ingest seconds' ($doc.Contains($ingest.seconds + ' giây'))
$steps = @(@('raw', 'raw'), @('sau dedup', 'after_dedup'), @('sau lọc `event_time`', 'after_timestamp'), @('sau lọc `event_type`', 'after_event_type'), @('sau lọc giá > 0', 'after_price'), @('sau lọc định danh', 'after_identity'))
foreach ($step in $steps) {
    $row = Cells $doc ('| ' + $step[0] + ' |')
    Check ('KB5 ' + $step[1]) ((IntValue $row[1]) -eq $merged.counts.($step[1]))
}
foreach ($item in @(@('Số dòng', 'rows'), @('Dòng trùng', 'duplicate_rows'))) {
    $row = Cells $doc ('| ' + $item[0] + ' |')
    Check ('KB5 raw/clean ' + $item[1]) (((IntValue $row[1]) -eq $raw.($item[1])) -and ((IntValue $row[2]) -eq $clean.($item[1])))
}
$row = Cells $doc '| Giá ≤ 0 |'
Check 'KB5 raw/clean price_le_0' (((IntValue $row[1]) -eq $raw.price.price_le_0) -and ((IntValue $row[2]) -eq $clean.price.price_le_0))
foreach ($event in @('view', 'cart', 'purchase')) {
    $row = Cells $doc ('| `' + $event + '` |')
    Check "KB5 $event" (((IntValue $row[1]) -eq $raw.event_type_counts.$event) -and ((IntValue $row[2]) -eq $clean.event_type_counts.$event))
}
Check 'Raw/clean counts match merged endpoints' (($raw.rows -eq $merged.counts.raw) -and ($clean.rows -eq $merged.counts.written))
foreach ($prop in $merged.counts.PSObject.Properties) {
    $sum = ($merged.slices | ForEach-Object { $_.counts.($prop.Name) } | Measure-Object -Sum).Sum
    Check ('Slice sum ' + $prop.Name) ($sum -eq $prop.Value)
}
Check 'Full clean seven invariants pass' ((@($clean.invariants.PSObject.Properties).Count -eq 8) -and !(@($clean.invariants.PSObject.Properties | ForEach-Object { $_.Value }) -contains $false))
foreach ($i in 1..8) {
    $profile = ReadJson "$ev/slices/s${i}_profiling_clean.json"
    Check "Slice $i invariants, duplicates, price" ($profile.invariants.all_pass -and $profile.duplicate_rows -eq 0 -and $profile.price.price_le_0 -eq 0)
}
Check 'Cleaning seconds precision' ($doc.Replace('**', '').Contains(([string]$merged.cleaning_seconds_total) + ' giây'))
$snapshot = ReadJson "$ev/audit_5b_sources_20261111.json"
$appendix = Get-Content "$root/docs/tv2/phu_luc_schema.md" -Raw -Encoding UTF8
foreach ($item in @(@('landing', 'landing'), @('raw', 'raw/events'), @('clean', 'clean/events'))) {
    $dir = Join-Path $root ('data/real_sample3m_run01/' + $item[1])
    $actual = (Get-ChildItem -LiteralPath $dir -File -Recurse -Force | Where-Object { $_.FullName.Substring($dir.Length) -notmatch '(^|[\\/])\.' } | Measure-Object Length -Sum).Sum
    Check ('Appendix bytes ' + $item[0]) (($actual -eq $snapshot.sizes.($item[0] + '_visible_bytes')) -and $appendix.Contains((Grouped $actual) + ' byte'))
}
$small = ReadJson "$ev/audit_5b_sample3m/profiling_clean.json"
foreach ($key in @('brand', 'cat_l1')) {
    Check "Appendix unknown ratio $key" ($appendix.Contains([string]$clean.unknown_ratio.$key) -and $appendix.Contains([string]$small.unknown_ratio.$key))
}
Check 'Full-month partition dates' ($snapshot.full_clean_partition_dates.Count -eq 31)
foreach ($item in @(@('profiling_raw.json', 'data/real_oct_run01/reports/profiling_raw.json'), @('profiling_clean.json', 'data/real_oct_full/reports/profiling_clean.json'))) {
    Check ('Evidence parsed JSON ' + $item[0]) (((ReadJson "$ev/$($item[0])" | ConvertTo-Json -Depth 12) -ceq (ReadJson (Join-Path $root $item[1]) | ConvertTo-Json -Depth 12)))
}
foreach ($name in @('ch03_du_lieu.md', 'ch06_kb3_kb5.md', 'phu_luc_schema.md', 'ch08_bai_hoc_ai.md')) {
    $t = Get-Content "$root/docs/tv2/$name" -Raw -Encoding UTF8
    Check "Removed stale claims: $name" ($t -notmatch '68\.523|36\.242|28\.074|ba lần thử|hai lần liên tiếp|2\.553 giây|31,8%|14,4%|17,7×')
}
$documents = @('ch02_1_bigdata.md', 'ch03_du_lieu.md', 'ch06_kb3_kb5.md', 'phu_luc_schema.md', 'ch08_bai_hoc_ai.md') | ForEach-Object {
    [PSCustomObject]@{ path = "docs/tv2/$_"; sha256 = (Get-FileHash "$root/docs/tv2/$_").Hash.ToLowerInvariant() }
}
$result = [ordered]@{ scope = 'Five TV2 report Markdown files; selected source comparisons plus manual review in README.md, no new Spark run'; documents = @($documents); checks = $checks.ToArray(); all_pass = $true }
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'checks.json'), ($result | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
Write-Output "Passed $($checks.Count) source comparisons."
