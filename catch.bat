@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ===================================================
echo   Airbnb Studio 价格查询 - MAG 318 Business Bay Dubai
echo ===================================================
echo.

:ASK_CHECKIN
set "CHECKIN="
set /p CHECKIN=请输入入住日期 (格式 YYYY-MM-DD, 例如 2026-08-01): 
if "%CHECKIN%"=="" (
    echo 入住日期不能为空，请重新输入。
    goto ASK_CHECKIN
)

:ASK_CHECKOUT
set "CHECKOUT="
set /p CHECKOUT=请输入退房日期 (格式 YYYY-MM-DD, 例如 2026-08-07): 
if "%CHECKOUT%"=="" (
    echo 退房日期不能为空，请重新输入。
    goto ASK_CHECKOUT
)

set "BUILDING="
set /p BUILDING=楼盘/地区 (直接回车使用默认 MAG 318, Business Bay, Dubai): 
if "%BUILDING%"=="" set "BUILDING=MAG 318, Business Bay, Dubai, United Arab Emirates"

set "KEYWORD="
set /p KEYWORD=标题筛选关键词 (直接回车使用默认 studio): 
if "%KEYWORD%"=="" set "KEYWORD=studio"

echo.
echo ---------------------------------------------------
echo 查询条件:
echo   入住: %CHECKIN%   退房: %CHECKOUT%
echo   楼盘: %BUILDING%
echo   关键词: %KEYWORD%
echo ---------------------------------------------------
echo.
echo 正在查询，请稍候（需要打开浏览器抓取数据，约 10-20 秒）...
echo.

python "%~dp0airbnb_studio_price_checker.py" --checkin "%CHECKIN%" --checkout "%CHECKOUT%" --building "%BUILDING%" --keyword "%KEYWORD%"

if errorlevel 1 (
    echo.
    echo [出错了] 脚本运行失败，请检查上面的报错信息。
    echo 常见原因: 没装 Python / 没装 playwright / 没跑 "playwright install chromium"
)

echo.
echo ===================================================
echo 查询完成，结果已保存为 CSV（同目录下 airbnb_studio_prices.csv）
echo ===================================================
pause
