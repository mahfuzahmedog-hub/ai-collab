try {
    $r = Invoke-WebRequest -Uri "https://ai-collab-13pv.vercel.app/?t=$(Get-Random)" -TimeoutSec 15 -UseBasicParsing

    if ($r.Content -match '"buildId":"([^"]+)"') {
        Write-Output "Build: $($matches[1])"
    }
    if ($r.Content -match 'src="(/_next/static/chunks/fd9d1056[^"]+)"') {
        $url = "https://ai-collab-13pv.vercel.app$($matches[1])"
        $js = Invoke-WebRequest -Uri $url -TimeoutSec 10 -UseBasicParsing
        $c = $js.Content
        if ($c -match "j6xe") { Write-Output "Backend URL: NEW (j6xe)" }
        if ($c -match "49ld") { Write-Output "Backend URL: OLD (49ld)" }
        # Find onrender URLs
        $idx = $c.IndexOf("onrender")
        while ($idx -gt -1) {
            $start = [Math]::Max(0, $idx - 30)
            $end = [Math]::Min($c.Length, $idx + 40)
            Write-Output "...$($c.Substring($start, $end - $start))..."
            $idx = $c.IndexOf("onrender", $idx + 1)
        }
    }
} catch { Write-Output "Error: $_" }
