# P2 v1.0.1 替换、验证与发布指南

这份指南供你更新已有的 P2 仓库使用。新版本修正经验 CVaR 的报告计算，并同步代码、测试、输出、图和 PDF。原来的个人复现记录保留不动，新的辅助核验另行记录。

请一次只复制一个代码框，按 Enter，等重新出现 `PS ...>` 再执行下一个。不要复制提示符，也不要把两条命令粘成一条。下面使用 `git --no-pager` 的查看命令，避免再次进入分页器。

## 1. 下载并解压总包

把 `P2_v1.0.1_CVAR_FIXED_20261004.zip` 下载到 Windows 的 Downloads 文件夹。总包包含四项：新版 PDF、替换包、完整项目备份和本指南。

在 PowerShell 执行：

```powershell
$p2Bundle = "C:\Users\40610\Downloads\P2_v1.0.1_CVAR_FIXED_20261004.zip"
```

```powershell
Test-Path -LiteralPath $p2Bundle
```

应显示 `True`。若浏览器把文件改名为带 `(1)` 的文件，请先改回上述文件名，或修改变量中的文件名。

```powershell
$p2Extract = "C:\Users\40610\Downloads\P2_v101_" + (Get-Date -Format "yyyyMMdd_HHmmss")
```

```powershell
Expand-Archive -LiteralPath $p2Bundle -DestinationPath $p2Extract
```

```powershell
Get-ChildItem -LiteralPath $p2Extract | Select-Object Name,Length
```

## 2. 进入已有仓库并备份

```powershell
Set-Location -LiteralPath "C:\Users\40610\Desktop\博士申请材料\作品集\P2_WORKING_REPOSITORY"
```

```powershell
git status --short
```

如果没有输出，可以继续。如果有尚未保存的修改，请先保留这些修改，不要用新文件直接覆盖它们。

```powershell
$p2Backup = "..\P2_before_v101_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".zip"
```

```powershell
git archive --format=zip --output=$p2Backup HEAD
```

这个备份保存当前已提交的文件；Git 历史仍在原仓库中。

## 3. 复制替换文件

使用总包中的小替换包更新已有仓库。完整项目压缩包供备份或另建工作目录使用，不要用它覆盖已有仓库的 Git 历史。

```powershell
$p2PatchFolder = Join-Path $p2Extract "changed_files"
```

```powershell
Expand-Archive -LiteralPath (Join-Path $p2Extract "P2_v1.0.1_changed_files.zip") -DestinationPath $p2PatchFolder
```

```powershell
Copy-Item -Path "$p2PatchFolder\*" -Destination "." -Recurse -Force
```

```powershell
git status --short
```

这次会有多处文件变化，这是正常的：经验 CVaR 数字变化需要同步表格、图、报告和说明。替换包不包含虚拟环境和 Git 目录，也不删除你的个人复现日志。

## 4. 使用现有 Python 3.13 虚拟环境

```powershell
& ".\.venv\Scripts\python.exe" --version
```

你的环境应仍显示 `Python 3.13.15`。无需安装另一个 Python。

```powershell
& ".\.venv\Scripts\python.exe" -m pip install -r requirements-lock.txt
```

```powershell
$LASTEXITCODE
```

安装退出码应为 `0`。锁定版本为 NumPy 2.3.5、pandas 2.2.3、SciPy 1.17.0、Matplotlib 3.10.8、PyYAML 6.0.3。

```powershell
& ".\.venv\Scripts\python.exe" -m pip check
```

应显示 `No broken requirements found.`。

## 5. 留下你实际执行的新核验记录

新记录使用当前真实时间，不修改 2 October 2026 的旧记录。

```powershell
$p2CheckDir = "evidence\personal_run\v101_check_" + (Get-Date -Format "yyyyMMdd_HHmmss")
```

```powershell
New-Item -ItemType Directory -Path $p2CheckDir | Out-Null
```

```powershell
(Get-Date -Format o) | Set-Content -Encoding ascii (Join-Path $p2CheckDir "actual_check_time.txt")
```

```powershell
cmd.exe /d /c ".venv\Scripts\python.exe --version > $p2CheckDir\python_version.txt 2>&1"
```

```powershell
cmd.exe /d /c ".venv\Scripts\python.exe -m unittest discover -s tests -v > $p2CheckDir\unit_tests.txt 2>&1"
```

```powershell
$p2TestExit = $LASTEXITCODE
```

```powershell
$p2TestExit | Set-Content -Encoding ascii (Join-Path $p2CheckDir "unit_tests_exit_code.txt")
```

```powershell
Get-Content -LiteralPath (Join-Path $p2CheckDir "unit_tests.txt")
```

```powershell
$p2TestExit
```

预期是 **11 个测试通过、OK、退出码 0**。若报错，请保留日志，并先解决错误再发布。

## 6. 一次验证三组实验

下面的命令会实际重跑 CVaR weight 0.55、0.70、0.85，并将每组的三个关键表与新的参考快照比较。运行时可能暂时没有屏幕输出，请等待 PowerShell 提示符重新出现。临时输出由程序单独管理，不覆盖仓库中的 `outputs`。

```powershell
cmd.exe /d /c ".venv\Scripts\python.exe scripts\verify_release.py > $p2CheckDir\verify_release.txt 2>&1"
```

```powershell
$p2VerifyExit = $LASTEXITCODE
```

```powershell
$p2VerifyExit | Set-Content -Encoding ascii (Join-Path $p2CheckDir "verify_release_exit_code.txt")
```

```powershell
Get-Content -LiteralPath (Join-Path $p2CheckDir "verify_release.txt")
```

```powershell
$p2VerifyExit
```

预期是 **9 项 PASS、9/9 release table comparisons passed、退出码 0**。绝对数值容差仍为 `1e-10`。如果没有全部通过，不要删除失败日志、放宽容差或把失败写成成功。

## 7. 检查新报告

```powershell
Start-Process -FilePath ".\report\P2_Mini_Paper_Haorui_Cai.pdf"
```

核对报告为 8 页，封面版本为 v1.0.1。主结果中的 Adaptive CVaR loss 为 **16.23 EUR**；敏感性表中 0.55、0.70、0.85 的 CVaR loss 分别为 **16.23、15.03、12.59 EUR**。图的来源说明为 regenerated v1.0.1 baseline。

这些变化是报告计算定义的修正。Linux/Python 3.12.14 辅助核验中，3,744 次成对求解的调度、期望利润和 LP 目标均未变化。你原先在 Windows/Python 3.13.15 的复现经历也保留在记录中。本指南第 5、6 步完成后，才有本次修订的 Windows 核验结果。

无需向学校提交 Word 或虚拟环境。PDF 和学校允许的仓库/Release 链接即可；具体上传格式仍按申请系统要求。

## 8. 提交并推送修改

```powershell
git diff --check
```

```powershell
git --no-pager diff --stat
```

```powershell
git status --short
```

确认只包含项目修改和你刚生成的核验记录，没有误生成的无关文件。

```powershell
git add .
```

```powershell
git diff --cached --check
```

```powershell
git --no-pager diff --cached --stat
```

```powershell
git commit -m "Correct empirical CVaR reporting and verify P2 v1.0.1"
```

```powershell
git push origin main
```

```powershell
git status -sb
```

应显示 `main...origin/main`，没有未提交文件，也没有 ahead 提示。PDF 和 PNG 设置了 binary 属性，避免换行转换改变文件字节。

## 9. 检查 GitHub Actions

打开 P2 的 GitHub 仓库，点击 **Actions**，查看最新的 **P2 reproducibility** 工作流。六个组合为 Ubuntu/Windows × Python 3.11/3.12/3.13，每个都会跑测试及三组实验比较。

这些组合在本次辅助核验时仅已配置，尚未执行。应以推送后的真实执行状态为准；若失败，打开失败任务的日志并保留错误信息，先修复再发布。

## 10. 建立 v1.0.1 标签和 Release

先检查这个标签是否已经存在：

```powershell
git tag --list v1.0.1
```

```powershell
git ls-remote --tags origin "refs/tags/v1.0.1*"
```

若两条都没有输出，可以创建新标签。若已有输出，先核对它是否已经发布、指向哪个提交；确认如何保留已有版本后，再执行创建标签的步骤。

```powershell
git tag -a v1.0.1 -m "P2 v1.0.1 - empirical CVaR reporting correction"
```

```powershell
git push origin v1.0.1
```

在 GitHub 的 **Releases** 新建发布，选择现有标签 `v1.0.1`，标题建议：

```text
P2 v1.0.1 - Empirical CVaR reporting correction
```

说明可复制以下内容；额外的 Windows/Actions 成功说明只能在实际通过之后加入：

```text
This release corrects empirical CVaR reporting using a fixed worst-tail probability mass, with fractional boundary observations and ties. The LP optimisation formulation is unchanged. Three experiment configurations (weights 0.55, 0.70 and 0.85), output snapshots, figures and the PDF report are synchronised.

Report: report/P2_Mini_Paper_Haorui_Cai.pdf

Assisted Linux/Python 3.12.14 verification passed 11 unit tests and 9 rerun table comparisons. Across 3,744 paired solves, schedules, expected profit and LP objectives were unchanged. The original Windows/Python 3.13.15 personal reproduction records are retained separately.

All prices, schedules, profits, losses and regret values are simulated. This is a research portfolio benchmark, not evidence of real-market trading performance.
```

上传新版 PDF 作为 Release 附件。若也想上传最终完整项目，可用下述命令从你刚提交的文件生成压缩包；这样会包含你新做的本地核验日志：

```powershell
git archive --format=zip --prefix=P2_WORKING_REPOSITORY/ --output="..\P2_Portfolio_v1.0.1_verified.zip" v1.0.1
```

旧标签、旧报告和旧复现记录无需改成新数字。新 Release 清楚说明修订内容即可。
