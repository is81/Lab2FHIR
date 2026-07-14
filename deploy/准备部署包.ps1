# 准备部署包 — 把服务器需要的文件拷贝到 deploy/ 目录
# 使用方法：在项目根目录右键 → "使用 PowerShell 运行"

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$deploy = "$root\deploy\Lab2FHIR"

Write-Host "正在准备部署包..." -ForegroundColor Green

# 清空旧的
if (Test-Path $deploy) { Remove-Item -Recurse $deploy }

# ====== 后端 ======
Write-Host "  后端源码..."
Copy-Item "$root\backend\src"            "$deploy\backend\src" -Recurse
Copy-Item "$root\backend\requirements.txt" "$deploy\backend\"
Copy-Item "$root\backend\alembic.ini"    "$deploy\backend\"
Copy-Item "$root\backend\alembic"        "$deploy\backend\alembic" -Recurse
Copy-Item "$root\backend\tools\seed_users.py" "$deploy\backend\tools\"

# 创建上传目录
New-Item -ItemType Directory -Force "$deploy\backend\src\uploads" | Out-Null
"" | Out-File "$deploy\backend\src\uploads\.gitkeep"

# ====== 前端（构建产物） ======
Write-Host "  前端构建..."
Push-Location "$root\frontend"
npm run build 2>&1 | Out-Null
Pop-Location
Copy-Item "$root\frontend\dist"           "$deploy\frontend\dist" -Recurse

# ====== nginx 配置 ======
Copy-Item "$root\frontend\nginx.conf"     "$deploy\nginx.conf"

# ====== 样本 PDF ======
Copy-Item "$root\docs\pdf_test"           "$deploy\docs\pdf_test" -Recurse

# ====== 文档 ======
Copy-Item "$root\docs\部署命令.txt"       "$deploy\"
Copy-Item "$root\.env.example"            "$deploy\.env.example"

# ====== 计算大小 ======
$size = (Get-ChildItem $deploy -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host ""
Write-Host "部署包已生成: $deploy" -ForegroundColor Green
Write-Host "大小: $([math]::Round($size, 1)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "拷贝此文件夹到 U 盘即可。"
