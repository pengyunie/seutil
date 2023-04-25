import sys
import threading
import time
from typing import Optional, TextIO

from tqdm.std import tqdm as std_tqdm
from tqdm.utils import _screen_shape_wrapper


class PBarManager:
    def __init__(self, out: TextIO, switch_interval: float = 2.5):
        self.out = out
        self.switch_interval = switch_interval

        self.instances = []
        self.cur = 0
        self.last_switch = time.time()

        self.modify_lock = threading.Lock()
        self.cv_update = threading.Condition()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        while True:
            with self.cv_update:
                self.cv_update.wait()

                self.switch()

                self.out.write("\r")
                if self.cur < 0:
                    self.out.flush()
                    continue

                # write summaries of all instances
                summaries = self.format_summaries()
                self.out.write(summaries)

                # write details of the current focused instance
                focus = self.instances[self.cur]
                ncols = _screen_shape_wrapper()(self.out)[0] - len(summaries)
                self.out.write(
                    focus.format_meter(**{**focus.format_dict, "ncols": ncols})
                )

                self.out.flush()

    def format_summaries(self) -> str:
        s = ""
        for i, instance in enumerate(self.instances):
            if i > 0:
                s += "|"
            if i == self.cur:
                s += "["
            s += self.format_summary(instance)
            if i == self.cur:
                s += "]"
        s += "| "
        return s

    def format_summary(self, instance):
        if instance.total is not None:
            return f"{instance.n/instance.total:.0%}"
        else:
            return f"{instance.n:d}"

    def update(self):
        with self.cv_update:
            self.cv_update.notify()

    def add(self, instance: "tqdm_managed"):
        with self.modify_lock:
            self.instances.append(instance)
            self.switch(len(self.instances) - 1)
        self.update()

    def remove(self, instance: "tqdm_managed"):
        with self.modify_lock:
            try:
                index = self.instances.index(instance)
                if self.cur == index:
                    self.switch(index - 1)
                del self.instances[index]
            except ValueError:
                print(f"WARNING: removing an instance that is not managed by me")
                pass
        self.update()

    def switch(self, to: Optional[int] = None):
        if len(self.instances) == 0:
            self.cur = -1

        now = time.time()
        if to is not None or now - self.last_switch > self.switch_interval:
            self.last_switch = now
            if to is None:
                to = self.cur + 1
            self.cur = to % len(self.instances)


stderr_pbar = PBarManager(out=sys.stderr)


class tqdm_managed(std_tqdm):
    def __init__(self, *args, **kwargs):
        self.manager = stderr_pbar
        super().__init__(*args, **kwargs)

        if self.disable:
            return

        self.manager.add(self)

    def close(self):
        if self.disable:
            return

        self.disable = True

        with self.get_lock():
            self.manager.remove(self)

    def clear(self, *_, **__):
        pass

    def display(self, *_, **__):
        self.manager.update()


tqdm = tqdm_managed
