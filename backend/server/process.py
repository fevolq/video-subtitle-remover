import shutil
import os
import sys
import time

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import main
from backend.server import thread_pool, util

workers = {}


class TestWorker:

    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = input_path
        self.progress_total = 0
        self.progress_remover = 0
        self.isFinished = False

    def run(self):
        while self.progress_total < 100:
            time.sleep(1)
            self.progress_total += 1
            self.progress_remover += 1
            print(f'进度：{self.progress_total}')

        self.isFinished = True


class Worker:

    def __init__(self, filename: str, file):
        self.filename = filename
        current_date = util.get_current_date()

        self.sd = None
        self.process_id = util.hash256(f'{time.time()}-{filename}')
        self.input_path = os.path.join(get_input_dir(), f'{current_date}_{self.process_id[:6]}_{filename}')
        self.output_path = os.path.join(get_output_dir(), f'{current_date}_{self.process_id[:6]}_{filename}')
        self._save_input_file(file)

        self.__isFinished = False
        self.__progress = 0

    def _save_input_file(self, file):
        with open(self.input_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)

    @property
    def isFinished(self):
        return self.sd.isFinished if self.sd is not None else self.__isFinished

    @property
    def progress(self):
        return self.sd.progress_total if self.sd is not None else self.__progress

    def set_sd(self, sub_area: tuple = None):
        self.sd = main.SubtitleRemover(self.input_path, sub_area=sub_area, output_path=self.output_path)
        # self.sd = TestWorker(self.input_path, output_path=self.output_path)   # 用于本地测试服务

    def run(self):
        if torch.cuda.is_available() or isinstance(self.sd, TestWorker):
            print(f'开始执行任务：{self.process_id}')
            self.sd.run()
        else:
            print(f'无可用gpu，等待尝试中... ：{self.process_id}')
            time.sleep(10)
            return self.run()
        print(f'任务结束：{self.process_id}')
        self.release()

    def release(self):
        """清除显存"""
        if self.sd is not None:
            self.__isFinished = self.sd.isFinished
            self.__progress = self.sd.progress_total
            self.sd = None
        torch.cuda.empty_cache()


def get_base_dir():
    current_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_path, '../../data/')
    return data_path


def get_input_dir():
    input_dir = os.path.join(get_base_dir(), 'input')
    util.mkdir(input_dir)
    return input_dir


def get_output_dir():
    output_dir = os.path.join(get_base_dir(), 'output')
    util.mkdir(output_dir)
    return output_dir


def get_worker(process_id) -> Worker:
    return workers.get(process_id, None)


def remove_worker(process_id):
    if process_id in workers:
        del workers[process_id]


def submit(worker: Worker):
    print(f'提交任务：{worker.process_id}')
    success = thread_pool.submit(worker.run)
    if success:
        workers[worker.process_id] = worker
    else:
        worker.release()
    return success


def get_worker_state(process_id) -> dict:
    worker = get_worker(process_id)
    result = dict()
    result['info'] = info = {}

    if worker is None:
        result['success'] = False
        info['error'] = 'The process_id is wrong, or the process has been deleted.'
    else:
        result['success'] = True
        info['finished'] = worker.isFinished
        info['progress'] = worker.progress
    return result
