# rent_price_catch

- pip install playwright --break-system-packages

- playwright install chromium

- python airbnb_studio_price_checker.py --checkin 2026-08-01 --checkout 2026-08-07

# Bat execution

用法：

把这个 catch.bat 文件和 airbnb_studio_price_checker.py 放在同一个文件夹（脚本用 %~dp0 定位同目录的 py 文件，所以位置必须一致）。
双击运行，或者在 cmd 里输入文件名回车。
依次输入：

入住日期（比如 2026-08-01）
退房日期（比如 2026-08-03）
楼盘（直接回车用默认的 MAG 318）
关键词（直接回车用默认的 studio）


等 10-20 秒出结果，结果表格会打印在 cmd 窗口里，同时存一份 CSV。

几点说明：

chcp 65001 是切到 UTF-8 编码，不然中文提示在 cmd 里可能显示乱码。
前提是你电脑上已经装好了 Python 和 playwright（也就是上次说的 pip install playwright --break-system-packages + playwright install chromium 那两步，Windows 下去掉 --break-system-packages 就行，直接 pip install playwright）。如果没装，运行时会报错，脚本会提示常见原因。
如果你想让它记住"上次用过的楼盘/关键词"不用每次都输，或者想做成双击后自动用今天+7天当默认日期，告诉我，我可以再改。
