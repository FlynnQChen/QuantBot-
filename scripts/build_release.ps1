<#
.SYNOPSIS 
  前端项目发布构建脚本
.DESCRIPTION
  执行以下操作：
  1. 清理旧的构建产物 
  2. 安装依赖
  3. 运行测试 
  4. 构建生产版本 
  5. 打包发布文件 
  6. 生成版本变更记录 
  7. 输出构建摘要 
.NOTES 
  版本: 1.2.0
  作者: DevOps Team
  日期: 2023-05-15 
#>
 
#region 初始化参数和配置 
param (
    [string]$Version = "",
    [string]$Environment = "production", 
    [switch]$SkipTests = $false,
    [switch]$DryRun = $false,
    [switch]$Help = $false 
)
 
# 显示帮助信息
if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed 
    exit 0
}
 
# 脚本元数据
$ScriptStartTime = Get-Date
$BuildScriptVersion = "1.2.0"
 
# 项目根目录
$ProjectRoot = $PSScriptRoot 
$FrontendDir = Join-Path $ProjectRoot "frontend"
 
# 输出目录配置 
$BuildOutputDir = Join-Path $ProjectRoot "dist"
$ArtifactsDir = Join-Path $ProjectRoot "artifacts"
$ReportsDir = Join-Path $ProjectRoot "reports"
 
# 确保使用正确的Node版本 
$RequiredNodeVersion = "v16.14.0"
$RequiredNpmVersion = "8.3.1"
 
# 环境配置 
$EnvConfig = @{
    production  = @{ NODE_ENV = "production"  }
    staging     = @{ NODE_ENV = "staging"; VUE_APP_API_BASE = "https://api.staging.example.com"  }
    development = @{ NODE_ENV = "development"; VUE_APP_API_BASE = "https://api.dev.example.com"  }
}
 
# 错误处理设置 
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
#endregion 
 
#region 辅助函数 
function Write-Step {
    param($Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan 
}
 
function Write-Success {
    param($Message)
    Write-Host "[✓] $Message" -ForegroundColor Green
}
 
function Write-Warning {
    param($Message)
    Write-Host "[!] $Message" -ForegroundColor Yellow 
}
 
function Write-Error {
    param($Message)
    Write-Host "[×] $Message" -ForegroundColor Red
}
 
function Test-CommandExists {
    param($Command)
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}
 
function Get-GitVersion {
    try {
        $tag = git describe --tags --abbrev=0 2>$null
        if (-not $tag) { return "0.0.0" }
        return $tag.Trim()
    } catch {
        return "0.0.0"
    }
}
 
function Get-GitChanges {
    try {
        $changes = git log --pretty=format:"- %h %s (%an)" HEAD...$(git describe --tags --abbrev=0 2>$null || echo "initial") 2>$null
        if (-not $changes) { return "No changes since last tag" }
        return $changes
    } catch {
        return "Unable to retrieve changes"
    }
}
 
function Invoke-SafeCommand {
    param(
        [ScriptBlock]$Command,
        [string]$ErrorMessage,
        [switch]$Fatal = $true 
    )
    
    try {
        Invoke-Command $Command 
    } catch {
        if ($Fatal) {
            Write-Error "$ErrorMessage`n$($_.Exception.Message)"
            exit 1
        } else {
            Write-Warning "$ErrorMessage`n$($_.Exception.Message)"
            return $false 
        }
    }
    return $true
}
#endregion
 
#region 主构建流程
try {
    Write-Step "CryptoTrader 前端构建脚本 v$BuildScriptVersion"
    Write-Host "开始时间: $($ScriptStartTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "构建环境: $Environment"
    
    # 检查必要的工具 
    Write-Step "检查系统依赖"
    $dependencies = @(
        @{ Name = "Node.js";  Version = $RequiredNodeVersion; Command = "node --version" },
        @{ Name = "npm"; Version = $RequiredNpmVersion; Command = "npm --version" },
        @{ Name = "git"; Version = ""; Command = "git --version" }
    )
    
    foreach ($dep in $dependencies) {
        if (-not (Test-CommandExists $dep.Command.Split(' ')[0])) {
            throw "缺少依赖: $($dep.Name) - 请先安装"
        }
        $version = Invoke-Expression $dep.Command 
        if ($dep.Version -and (-not $version.Contains($dep.Version))) {
            Write-Warning "$($dep.Name) 版本不匹配 (当前: $version, 需要: $($dep.Version))"
        }
        Write-Success "$($dep.Name) $version"
    }
    
    # 设置环境变量
    Write-Step "配置环境变量"
    foreach ($kv in $EnvConfig[$Environment].GetEnumerator()) {
        [Environment]::SetEnvironmentVariable($kv.Key, $kv.Value)
        Write-Host "  $($kv.Key)=$($kv.Value)"
    }
    
    # 清理旧构建
    Write-Step "清理旧构建"
    $directoriesToClean = @($BuildOutputDir, $ArtifactsDir, $ReportsDir)
    foreach ($dir in $directoriesToClean) {
        if (Test-Path $dir) {
            Remove-Item $dir -Recurse -Force
            Write-Success "已清理目录: $dir"
        }
    }
    New-Item -ItemType Directory -Path $BuildOutputDir -Force | Out-Null 
    New-Item -ItemType Directory -Path $ArtifactsDir -Force | Out-Null
    New-Item -ItemType Directory -Path $ReportsDir -Force | Out-Null
    
    # 获取版本信息 
    Write-Step "获取版本信息"
    if (-not $Version) {
        $Version = Get-GitVersion
    }
    $BuildNumber = "{0:yyyyMMddHHmmss}" -f $ScriptStartTime
    $FullVersion = "$Version.$BuildNumber"
    
    Write-Host "  版本号: $Version"
    Write-Host "  构建号: $BuildNumber"
    Write-Host "  完整版本: $FullVersion"
    
    # 安装依赖
    Write-Step "安装依赖"
    Set-Location $FrontendDir 
    Invoke-SafeCommand -Command { npm ci --prefer-offline --no-audit --progress=false } `
                       -ErrorMessage "npm依赖安装失败"
    Write-Success "依赖安装完成"
    
    # 运行测试 
    if (-not $SkipTests) {
        Write-Step "运行测试"
        try {
            $testResultsFile = Join-Path $ReportsDir "test-results.xml" 
            npm run test:ci -- --watchAll=false --ci --reporters=default --reporters=jest-junit --outputFile=$testResultsFile 
            if ($LASTEXITCODE -ne 0) {
                throw "测试失败"
            }
            Write-Success "所有测试通过"
        } catch {
            if (-not $DryRun) {
                throw "测试阶段失败，构建终止"
            }
            Write-Warning "测试失败 (DryRun模式下继续)"
        }
    } else {
        Write-Warning "跳过测试阶段"
    }
    
    # 构建项目 
    Write-Step "构建生产版本"
    if ($DryRun) {
        Write-Warning "DryRun模式 - 跳过实际构建"
    } else {
        Invoke-SafeCommand -Command { npm run build } `
                           -ErrorMessage "构建过程失败"
        
        # 生成版本文件 
        $versionFile = Join-Path $BuildOutputDir "version.txt" 
        @(
            "Build Version: $FullVersion",
            "Build Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
            "Environment: $Environment",
            "Git Commit: $(git rev-parse HEAD)"
        ) | Out-File $versionFile -Encoding UTF8
        
        Write-Success "构建成功完成"
    }
    
    # 打包发布文件
    Write-Step "打包发布文件"
    $artifactName = "cryptotrader-fe-$Version-$Environment.zip" 
    $artifactPath = Join-Path $ArtifactsDir $artifactName
    
    if ($DryRun) {
        Write-Warning "DryRun模式 - 跳过打包"
    } else {
        Compress-Archive -Path "$BuildOutputDir\*" -DestinationPath $artifactPath -CompressionLevel Optimal
        Write-Success "生成发布包: $artifactPath"
    }
    
    # 生成变更日志 
    Write-Step "生成变更记录"
    $changelogFile = Join-Path $ArtifactsDir "CHANGELOG.md" 
    @(
        "# CryptoTrader $Version",
        "构建日期: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
        "环境: $Environment",
        "",
        "## 变更记录",
        "",
        "$(Get-GitChanges)"
    ) | Out-File $changelogFile -Encoding UTF8
    
    Write-Success "变更记录已生成"
    
    # 构建完成 
    $duration = [math]::Round((New-TimeSpan -Start $ScriptStartTime).TotalMinutes, 2)
    Write-Step "构建完成!"
    Write-Host "构建结果概要:"
    Write-Host "  版本: $FullVersion"
    Write-Host "  环境: $Environment"
    Write-Host "  用时: $duration 分钟"
    Write-Host "  输出目录: $BuildOutputDir"
    if (-not $DryRun) {
        Write-Host "  发布包: $artifactPath"
    }
    Write-Host "  变更记录: $changelogFile"
    
} catch {
    Write-Error "构建过程中发生错误: $($_.Exception.Message)"
    Write-Error $_.ScriptStackTrace
    exit 1 
} finally {
    Set-Location $ProjectRoot
}
#endregion