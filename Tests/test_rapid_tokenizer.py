from addin_import import import_addin_module


tokenizer = import_addin_module(
    "commands.postProcessor.operations.operation.rapid_moves.tokenizer"
)


def test_tokenizer_ignores_comments_and_tracks_modal_motion_and_axes():
    result = tokenizer.parse_line("g01 X1.5 Y-2 F100 (Z99 G3)")

    assert result.localMotion == tokenizer.MOTIONS.G1
    assert result.sawX
    assert result.sawY
    assert not result.sawZ
