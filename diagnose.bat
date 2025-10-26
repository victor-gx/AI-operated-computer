@echo off

REM 显示系统信息
echo 系统信息 > diagnose_output.txt
echo =========== >> diagnose_output.txt
ver >> diagnose_output.txt
echo. >> diagnose_output.txt

REM 显示Python信息
echo Python信息 >> diagnose_output.txt
echo =========== >> diagnose_output.txt
python --version >> diagnose_output.txt 2>&1
python -c "import sys; print('Python版本:', sys.version); print('Python路径:', sys.executable)" >> diagnose_output.txt 2>&1
echo. >> diagnose_output.txt

REM 检查pip安装的包
echo 已安装的Python包 >> diagnose_output.txt
echo =============== >> diagnose_output.txt
python -m pip list | findstr /i "PyQt5" >> diagnose_output.txt 2>&1
echo. >> diagnose_output.txt

REM 尝试简单的PyQt5导入
echo PyQt5导入测试 >> diagnose_output.txt
echo ============= >> diagnose_output.txt
python -c "try: import PyQt5; print('PyQt5成功导入'); print('版本:', PyQt5.__version__); except Exception as e: print('导入失败:', e)" >> diagnose_output.txt 2>&1
echo. >> diagnose_output.txt

echo 诊断完成，结果已保存到 diagnose_output.txt