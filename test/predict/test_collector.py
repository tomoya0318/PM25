from predict.collector import collect_triggerable_patches

def test_collect_triggerable_patches(pattern_data):
    print(collect_triggerable_patches(pattern_data))