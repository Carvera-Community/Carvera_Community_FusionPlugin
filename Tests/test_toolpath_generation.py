from types import SimpleNamespace

from addin_import import import_addin_module


ensure_toolpath_generated = import_addin_module(
    "commands.postProcessor.toolpath_generation"
).ensure_toolpath_generated


def test_existing_toolpath_is_not_generated():
    generated = []

    ensure_toolpath_generated(
        "setup",
        checkToolpath=lambda setup: True,
        generateToolpath=lambda setup: generated.append(setup),
    )

    assert generated == []


def test_generation_is_polled_until_complete():
    generation = SimpleNamespace(isGenerationCompleted=False)
    sleeps = []

    def sleep(delay):
        sleeps.append(delay)
        if len(sleeps) == 3:
            generation.isGenerationCompleted = True

    ensure_toolpath_generated(
        "setup",
        checkToolpath=lambda setup: False,
        generateToolpath=lambda setup: generation,
        sleep=sleep,
    )

    assert sleeps == [0.1, 0.1, 0.1]
