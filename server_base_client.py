# -*- coding: utf-8 -*-
# @Time    : 1/7/23 12:29 PM
# @FileName: run_server.py
# @Software: PyCharm
# @Github    ：sudoskys
import uvicorn

if __name__ == '__main__':
    uvicorn.run('App.Server:app', host='127.0.0.1', port=9557, reload=True, log_level="debug", workers=1)
