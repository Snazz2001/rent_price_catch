@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   Airbnb Studio Price Checker - MAG 318 Business Bay Dubai
echo ===================================================
echo.

:ASK_CHECKIN
set "CHECKIN="
set /p CHECKIN=Check-in date (YYYY-MM-DD, e.g. 2026-08-01): 
if "%CHECKIN%"=="" (
    echo Check-in date cannot be empty, try again.
    goto ASK_CHECKIN
)

:ASK_CHECKOUT
set "CHECKOUT="
set /p CHECKOUT=Check-out date (YYYY-MM-DD, e.g. 2026-08-07): 
if "%CHECKOUT%"=="" (
    echo Check-out date cannot be empty, try again.
    goto ASK_CHECKOUT
)

set "BUILDING="
set /p BUILDING=Building/area (press Enter for default MAG 318, Business Bay, Dubai): 
if "%BUILDING%"=="" set "BUILDING=MAG 318, Business Bay, Dubai, United Arab Emirates"

set "KEYWORD="
set /p KEYWORD=Title keyword filter (press Enter for default "studio"): 
if "%KEYWORD%"=="" set "KEYWORD=studio"

echo.
echo ---------------------------------------------------
echo Search parameters:
echo   Check-in:  %CHECKIN%
echo   Check-out: %CHECKOUT%
echo   Building:  %BUILDING%
echo   Keyword:   %KEYWORD%
echo ---------------------------------------------------
echo.
echo Searching, please wait (opens a browser to scrape data, ~10-20 sec)...
echo.

python "%~dp0airbnb_studio_price_checker.py" --checkin "%CHECKIN%" --checkout "%CHECKOUT%" --building "%BUILDING%" --keyword "%KEYWORD%"

if errorlevel 1 (
    echo.
    echo [ERROR] Script failed. Check the error message above.
    echo Common causes: Python not installed / playwright not installed / did not run "playwright install chromium"
)

echo.
echo ===================================================
echo Done. Results saved as CSV in this folder: airbnb_studio_prices.csv
echo ===================================================
pause
