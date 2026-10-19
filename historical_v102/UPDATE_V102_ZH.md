# P2 v1.0.2 更新指南

本包在原链接失效后重新打包；SHA256 使用本次重新发送时给出的新校验值。文件名仍为 P2_v1.0.2_documentation_update_20261009.zip，前面聊天中的下载路径和操作命令继续适用。不要再使用旧 ZIP 的 8b921d... 校验值。

更新内容：说明场景缩放上下限，报告标题改为 Risk-averse，补全历史验证记录，调整风险图标签，同步版本 1.0.2。实验算法、数据、配置和已有快照保留；旧 manifest 的 1.0.1 记录其生成历史。

每次只运行一条命令，不复制 PS 提示符或 >>。遇到错误先停在该步。

## 1. 进入仓库，检查状态

```powershell
Set-Location -LiteralPath "C:\Users\40610\Desktop\博士申请材料\作品集\P2_WORKING_REPOSITORY"
git --no-pager status --short
Get-Content ".\pyproject.toml" | Select-String '^version\s*='
```

工作区应无输出，原版本应为 1.0.1。存在未提交工作或其他版本时先核对，不要覆盖。

## 2. 备份和解压

```powershell
$p2Backup = "..\P2_before_v102_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".zip"
git archive --format=zip --output=$p2Backup HEAD
Test-Path -LiteralPath $p2Backup
$p2Bundle = "C:\Users\40610\Downloads\P2_v1.0.2_documentation_update_20261009.zip"
Test-Path -LiteralPath $p2Bundle
$p2Extract = "C:\Users\40610\Downloads\P2_v102_update_" + (Get-Date -Format "yyyyMMdd_HHmmss")
Expand-Archive -LiteralPath $p2Bundle -DestinationPath $p2Extract -ErrorAction Stop
Test-Path -LiteralPath (Join-Path $p2Extract "apply_update.py")
```

三处 Test-Path 都应 True。本包只有一层 ZIP。备份仅包含已提交文件。

## 3. 检查，再替换

```powershell
& ".\.venv\Scripts\python.exe" (Join-Path $p2Extract "apply_update.py") --repository "."
```

预期 CHECK PASSED，且未写入文件。检查兼容 CRLF，核对所有原文件。

```powershell
& ".\.venv\Scripts\python.exe" (Join-Path $p2Extract "apply_update.py") --repository "." --apply
Get-Content ".\pyproject.toml" | Select-String '^version\s*='
Start-Process -FilePath ".\report\P2_Mini_Paper_Haorui_Cai.pdf"
```

预期 UPDATE APPLIED，版本 1.0.2。PDF 应为 8 页，封面 Risk-averse，第 3 页明确缩放范围，第 6 页图中标签完整，第 8 页有历史 Windows/CI 记录。

## 4. 用现有 Python 3.13 验证并保存日志

```powershell
$p2CheckDir = ".\evidence\personal_run\v102_check_" + (Get-Date -Format "yyyyMMdd_HHmmss")
New-Item -ItemType Directory -Path $p2CheckDir | Out-Null
(Get-Date -Format o) | Set-Content -Encoding ascii (Join-Path $p2CheckDir "actual_check_time.txt")
& ".\.venv\Scripts\python.exe" -m pip install -r requirements-lock.txt
& ".\.venv\Scripts\python.exe" -m pip check
cmd.exe /d /c ".venv\Scripts\python.exe --version > $p2CheckDir\python_version.txt 2>&1"
cmd.exe /d /c ".venv\Scripts\python.exe -m pip freeze > $p2CheckDir\installed_packages.txt 2>&1"
cmd.exe /d /c ".venv\Scripts\python.exe -m unittest discover -s tests -v > $p2CheckDir\unit_tests.txt 2>&1"
$p2TestExit = $LASTEXITCODE
$p2TestExit | Set-Content -Encoding ascii (Join-Path $p2CheckDir "unit_tests_exit_code.txt")
Get-Content -LiteralPath (Join-Path $p2CheckDir "unit_tests.txt")
$p2TestExit
```

预期依赖一致、11 tests、OK、退出码 0。

```powershell
cmd.exe /d /c ".venv\Scripts\python.exe scripts\verify_release.py > $p2CheckDir\verify_release.txt 2>&1"
$p2VerifyExit = $LASTEXITCODE
$p2VerifyExit | Set-Content -Encoding ascii (Join-Path $p2CheckDir "verify_release_exit_code.txt")
Get-Content -LiteralPath (Join-Path $p2CheckDir "verify_release.txt")
$p2VerifyExit
```

预期 9/9 release table comparisons passed，退出码 0。脚本临时重跑三组实验，不覆盖 saved baseline；不必安装另一个 Python。

## 5. 暂存、提交、推送

```powershell
git --no-pager diff --check
$p2ChangedPaths = & ".\.venv\Scripts\python.exe" -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); print('\n'.join(x['path'] for x in d['files']))" (Join-Path $p2Extract "CHANGE_MANIFEST.json")
git add -- $p2ChangedPaths
git add -- $p2CheckDir
git --no-pager diff --cached --check
git --no-pager diff --cached --stat
git commit -m "Clarify P2 report methods and verification for v1.0.2"
git push origin main
git status -sb
```

核对仅暂存清单文件及本次验证日志。diff --check 应通过；LF/CRLF warning 本身不等于失败。最终 status 应为 main...origin/main 且无修改。

## 6. 检查新 CI，再创建标签

打开 https://github.com/KeithCai1995/p2-storage-decision-under-forecast-uncertainty/actions ，确认新提交的 Ubuntu/Windows × Python 3.11/3.12/3.13 六个任务都绿色。不能用旧 c6155e7 那次代替新提交。

```powershell
git tag --list v1.0.2
git ls-remote --tags origin "refs/tags/v1.0.2*"
```

两条都无输出时才创建；已有标签先核对，不覆盖。

```powershell
git tag -a v1.0.2 -m "P2 v1.0.2 - report methods and verification clarification"
git --no-pager show --no-patch --decorate v1.0.2
git push origin v1.0.2
git ls-remote --tags origin "refs/tags/v1.0.2*"
```

确认标签指向新 CI 通过的提交。

## 7. Release 和申请定稿

在 Releases 选择 Draft a new release，标签 v1.0.2。
标题：P2 v1.0.2 - Report methods and verification clarification。
Description 可使用：

```text
This revision clarifies scenario scaling and the risk-averse objective, updates the report's verification chronology, and improves a figure label.

The numerical implementation, configurations, forecast input and saved experimental results are unchanged from v1.0.1. All financial values are simulated benchmark results.

Report: report/P2_Mini_Paper_Haorui_Cai.pdf
Reproduction and provenance: REFERENCE_RUNS.md
```

新 CI 全部通过后，可加入其工作流链接。将仓库中的新版 PDF 上传为 Release 附件方便下载；GitHub 的 Source code ZIP 已含标签对应仓库，无需另外上传源码 ZIP。本更新包是本机更新工具，不是申请提交包。

发布后用未登录窗口检查访问，并核对下载 PDF 与本机报告一致。

定稿条件：本机 11/11 测试和 9/9 表格核对通过，新 CI 六任务通过，报告/版本/Release 一致，来源与实际工作记录清楚，你能解释模型和局限，并按目标学校要求核对页数、格式、匿名及披露规则。真实市场数据、多种子和更多模型是后续增强方向。
