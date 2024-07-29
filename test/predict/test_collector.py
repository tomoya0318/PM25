from predict.collector import collect_triggerable_patches

def test_collect_triggerable_patches(pattern_data):
    expected = {('=i=dic', '-[', "='NUMBER", '-]'), ('=i=dic', '-[', '=STRING', '-]')}
    triggers = collect_triggerable_patches(pattern_data)
    assert triggers == expected