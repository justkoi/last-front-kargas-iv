@echo off
chcp 949 >nul
setlocal

set SRC=%~dp0최후의 전선 카르가스 IV
set DST=C:\Users\justk\Documents\StarCraft\Maps

echo [복사] "%SRC%\*.scx"
echo [대상] "%DST%"
echo.

if not exist "%DST%" (
    echo 대상 폴더가 없습니다. 생성합니다.
    mkdir "%DST%"
)

copy /Y "%SRC%\*.scx" "%DST%\"
if errorlevel 1 (
    echo.
    echo [실패] 복사 실패. 경로 또는 권한 확인.
) else (
    echo.
    echo [완료] 복사 완료.
)

echo.
pause
