@echo off
echo ========================================================
echo   HE THONG AUTO LABEL 3D CUBOID CHO CVAT - BY KELY
echo ========================================================

echo.
echo [1/3] Kiem tra du lieu...
if not exist "pointcloud" (
    echo [!] Khong tim thay thu muc pointcloud. Dung lai!
    pause
    exit /b
)
if not exist "cbgs_pp_multihead.pth" (
    echo [!] Khong tim thay model cbgs_pp_multihead.pth. Dung lai!
    pause
    exit /b
)

echo.
echo [2/3] Khoi chay AI (OpenPCDet) qua Docker...
echo Qua trinh build Docker lan dau co the mat 5-10 phut (bien dich CUDA).
docker-compose up --build

echo.
echo [3/3] Upload ket qua len CVAT...
echo Dang goi upload_cvat.py tren may tinh host...
py upload_cvat.py

echo.
echo ========================================================
echo XONG! Moi thu da hoan tat, hay kiem tra tren CVAT cua anh!
echo ========================================================
pause
