from types import SimpleNamespace

from addin_import import import_addin_module


ensureToolpathGenerated = import_addin_module(
    "commands.postProcessor.toolpath_generation"
).ensureToolpathGenerated


def test_existing_toolpath_is_not_generated():
    generated = []

    ensureToolpathGenerated(
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

    ensureToolpathGenerated(
        "setup",
        checkToolpath=lambda setup: False,
        generateToolpath=lambda setup: generation,
        sleep=sleep,
    )

    assert sleeps == [0.1, 0.1, 0.1]
