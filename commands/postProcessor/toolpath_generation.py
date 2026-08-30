from typing import Callable
import time


def ensure_toolpath_generated(
    setup,
    checkToolpath: Callable[[object], bool],
    generateToolpath: Callable[[object], object],
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    if checkToolpath(setup):
        return

    generation = generateToolpath(setup)
    while not generation.isGenerationCompleted:
        sleep(0.1)
