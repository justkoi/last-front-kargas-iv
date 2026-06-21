param(
    [string]$InputPath = (Join-Path $PSScriptRoot '..\최후의 전선 카르가스 IV\map.bmp'),
    [string]$OutputPath = (Join-Path $PSScriptRoot '..\최후의 전선 카르가스 IV\map_infographic_v2.png'),
    [int]$Size = 4096
)

Add-Type -AssemblyName System.Drawing

function New-Color([int]$a, [int]$r, [int]$g, [int]$b) {
    return [System.Drawing.Color]::FromArgb($a, $r, $g, $b)
}

function New-Path([float[][]]$points) {
    $path = [System.Drawing.Drawing2D.GraphicsPath]::new()
    $drawingPoints = [System.Drawing.PointF[]]@($points | ForEach-Object {
        [System.Drawing.PointF]::new($_[0], $_[1])
    })
    $path.AddPolygon($drawingPoints)
    return $path
}

function Draw-Zone($graphics, [float[][]]$points, $fillColor, $lineColor) {
    $path = New-Path $points
    $fill = [System.Drawing.SolidBrush]::new($fillColor)
    $outer = [System.Drawing.Pen]::new((New-Color 90 0 0 0), 30)
    $line = [System.Drawing.Pen]::new($lineColor, 15)
    $line.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
    $graphics.FillPath($fill, $path)
    $graphics.DrawPath($outer, $path)
    $graphics.DrawPath($line, $path)
    $fill.Dispose(); $outer.Dispose(); $line.Dispose(); $path.Dispose()
}

function Draw-Card($graphics, [float]$x, [float]$y, [float]$w, [float]$h, [string]$title, [string]$subtitle, $accent, [float]$titleSize = 86) {
    $radius = 28.0
    $path = [System.Drawing.Drawing2D.GraphicsPath]::new()
    $path.AddArc($x, $y, $radius, $radius, 180, 90)
    $path.AddArc($x + $w - $radius, $y, $radius, $radius, 270, 90)
    $path.AddArc($x + $w - $radius, $y + $h - $radius, $radius, $radius, 0, 90)
    $path.AddArc($x, $y + $h - $radius, $radius, $radius, 90, 90)
    $path.CloseFigure()

    $shadowPath = [System.Drawing.Drawing2D.GraphicsPath]::new()
    $shadowPath.AddPath($path, $false)
    $matrix = [System.Drawing.Drawing2D.Matrix]::new()
    $matrix.Translate(14, 16)
    $shadowPath.Transform($matrix)
    $shadow = [System.Drawing.SolidBrush]::new((New-Color 125 0 0 0))
    $panel = [System.Drawing.SolidBrush]::new((New-Color 225 10 15 25))
    $border = [System.Drawing.Pen]::new($accent, 7)
    $graphics.FillPath($shadow, $shadowPath)
    $graphics.FillPath($panel, $path)
    $graphics.DrawPath($border, $path)
    $bar = [System.Drawing.SolidBrush]::new($accent)
    $graphics.FillRectangle($bar, $x, $y, 18, $h)

    $titleFont = [System.Drawing.Font]::new('Malgun Gothic', $titleSize, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $subFont = [System.Drawing.Font]::new('Malgun Gothic', 50, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
    $white = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::White)
    $muted = [System.Drawing.SolidBrush]::new((New-Color 255 210 220 232))
    $graphics.DrawString($title, $titleFont, $white, $x + 56, $y + 25)
    if ($subtitle) { $graphics.DrawString($subtitle, $subFont, $muted, $x + 60, $y + $h - 78) }

    $titleFont.Dispose(); $subFont.Dispose(); $white.Dispose(); $muted.Dispose()
    $shadow.Dispose(); $panel.Dispose(); $border.Dispose(); $bar.Dispose()
    $shadowPath.Dispose(); $matrix.Dispose(); $path.Dispose()
}

function Draw-Callout($graphics, [float]$x, [float]$y, [float]$w, [string]$text, $accent, [float]$targetX, [float]$targetY) {
    $h = 132.0
    $line = [System.Drawing.Pen]::new($accent, 10)
    $line.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $line.EndCap = [System.Drawing.Drawing2D.LineCap]::ArrowAnchor
    if ($targetY -lt $y) {
        $startX = $x + $w / 2; $startY = $y
    } elseif ($targetY -gt $y + $h) {
        $startX = $x + $w / 2; $startY = $y + $h
    } elseif ($targetX -lt $x) {
        $startX = $x; $startY = $y + $h / 2
    } else {
        $startX = $x + $w; $startY = $y + $h / 2
    }
    $graphics.DrawLine($line, $startX, $startY, $targetX, $targetY)
    Draw-Card $graphics $x $y $w $h $text '' $accent 59
    $line.Dispose()
}

function Draw-Entrance($graphics, [float]$x, [float]$y, [float]$targetX, [float]$targetY, $accent) {
    $line = [System.Drawing.Pen]::new($accent, 18)
    $line.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $line.EndCap = [System.Drawing.Drawing2D.LineCap]::ArrowAnchor
    $graphics.DrawLine($line, $x + 230, $y + 65, $targetX, $targetY)
    Draw-Card $graphics $x $y 470 130 '입구' '' $accent 66
    $line.Dispose()
}

$source = [System.Drawing.Image]::FromFile((Resolve-Path $InputPath))
$canvas = [System.Drawing.Bitmap]::new($Size, $Size, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$graphics = [System.Drawing.Graphics]::FromImage($canvas)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$graphics.DrawImage($source, 0, 0, $Size, $Size)

$cyan = New-Color 255 40 220 255
$orange = New-Color 255 255 145 35
$crimson = New-Color 255 245 70 85
$brown = New-Color 255 195 120 70
$whiteAccent = New-Color 255 232 240 255

# Mission 1: upper-left orange Zerg territory.
Draw-Zone $graphics @(@(75,300),@(180,150),@(620,55),@(1320,55),@(1580,150),@(1660,650),@(1640,1160),@(1510,1340),@(1020,1460),@(520,1480),@(80,1360)) (New-Color 34 255 128 20) $orange

# Mission 2: broad right-side upper/lower hive territory.
Draw-Zone $graphics @(@(2200,70),@(4015,70),@(4015,4015),@(2410,4015),@(2170,3490),@(2190,2940),@(2080,2240),@(2180,1640),@(2110,800)) (New-Color 24 225 40 55) $crimson

# Player base and starting area in the lower-left.
Draw-Zone $graphics @(@(70,2440),@(900,2420),@(1430,2530),@(1580,2780),@(1580,3470),@(1450,3640),@(920,3720),@(810,4020),@(70,4020)) (New-Color 30 20 205 255) $cyan

Draw-Card $graphics 170 2510 830 245 '플레이어 기지' '시작 지점' $cyan 78
Draw-Entrance $graphics 1260 2110 820 2415 $cyan

Draw-Card $graphics 190 210 820 245 '미션 1 구역' '주황색 저그' $orange 78
Draw-Card $graphics 2750 180 930 170 '미션 2 구역' '' $crimson 82
Draw-Callout $graphics 2840 560 850 '갈색 저그 군락' $brown 3420 370
Draw-Callout $graphics 2820 2810 900 '하양색 저그 군락' $whiteAccent 3710 3480

$directory = Split-Path -Parent $OutputPath
if ($directory -and -not (Test-Path -LiteralPath $directory)) { New-Item -ItemType Directory -Path $directory | Out-Null }
$canvas.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)

$graphics.Dispose(); $canvas.Dispose(); $source.Dispose()
Write-Output (Resolve-Path $OutputPath)
