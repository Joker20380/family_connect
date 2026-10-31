"""Build the accepted dynamically linked Codec2/JNI pair from pinned public source."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


REVISION = '06d4c11e699b0351765f10398abb4f663a984f36'
ABIS = {
    'arm64-v8a': 'aarch64-linux-android26-clang',
    'armeabi-v7a': 'armv7a-linux-androideabi26-clang',
    'x86': 'i686-linux-android26-clang',
    'x86_64': 'x86_64-linux-android26-clang',
}
SPEECH = {
    'dump.c', 'lpc.c', 'nlp.c', 'postfilter.c', 'sine.c', 'codec2.c',
    'codec2_fft.c', 'kiss_fft.c', 'kiss_fftr.c', 'interp.c', 'lsp.c',
    'mbest.c', 'newamp1.c', 'phase.c', 'quantise.c', 'pack.c',
}
ROOT = Path(__file__).resolve().parent


def run(*arguments, **kwargs):
    return subprocess.run([str(argument) for argument in arguments], check=True, **kwargs)


def verify_source(source):
    revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True)
    if revision != REVISION or dirty:
        raise ValueError('Exact clean Codec2 source required')


def objects_for_link(build):
    objects = sorted((build / 'src/CMakeFiles/codec2.dir').rglob('*.o'))
    selected = [path for path in objects if path.name.removesuffix('.o') in SPEECH
                or path.name.startswith('codebook')]
    if not SPEECH.issubset({path.name.removesuffix('.o') for path in selected}):
        raise ValueError('Incomplete Codec2 speech objects')
    if not any(path.name.startswith('codebook') for path in selected):
        raise ValueError('Missing Codec2 codebooks')
    return selected


def build(source, ndk, output, abi, cmake):
    verify_source(source)
    if output.exists():
        raise ValueError('Fresh audio output required')
    output.mkdir(parents=True)
    abis = ABIS if abi == 'all' else {abi: ABIS[abi]}
    hashes = {}
    with tempfile.TemporaryDirectory(prefix='fc-audio-build-') as temporary:
        workspace = Path(temporary)
        for target, compiler_name in abis.items():
            work = workspace / target
            run(cmake, '-S', source, '-B', work, '-G', 'Ninja',
                '-DCMAKE_TOOLCHAIN_FILE=' + str(ndk / 'build/cmake/android.toolchain.cmake'),
                '-DANDROID_ABI=' + target, '-DANDROID_PLATFORM=android-26',
                '-DCMAKE_BUILD_TYPE=Release', '-DBUILD_SHARED_LIBS=ON', '-DUNITTEST=OFF', '-DLPCNET=OFF')
            run(cmake, '--build', work, '--target', 'codec2', '-j2')
            native = output / 'jniLibs' / target
            native.mkdir(parents=True)
            compiler = ndk / 'toolchains/llvm/prebuilt/linux-x86_64/bin' / compiler_name
            run(compiler, '-shared', '-Wl,-soname,libcodec2.so', '-Wl,--no-undefined',
                '-Wl,-z,max-page-size=16384', *objects_for_link(work), '-lm', '-o', native / 'libcodec2.so')
            run(compiler, '-shared', '-fPIC', '-O2', '-Wall', '-Wextra',
                '-I' + str(source / 'src'), '-I' + str(work), ROOT / 'native/radio.c',
                '-L' + str(native), '-lcodec2', '-Wl,-soname,libexit_audio.so',
                '-Wl,-z,max-page-size=16384', '-o', native / 'libexit_audio.so')
            hashes[target] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                              for path in sorted(native.glob('*.so'))}
    materials = output / 'corresponding-source'
    materials.mkdir()
    run('git', '-C', source, 'archive', '--format=tar.gz', '--prefix=codec2/',
        '-o', materials / 'codec2-source.tar.gz', REVISION)
    shutil.copy2(__file__, materials / 'build.py')
    shutil.copytree(ROOT / 'native', materials / 'native')
    shutil.copytree(ROOT / 'assets/audio-licenses', materials / 'assets/audio-licenses')
    receipt = {'schema': 1, 'codec2_revision': REVISION, 'abis': hashes,
               'jni_source_sha256': hashlib.sha256((ROOT / 'native/radio.c').read_bytes()).hexdigest(),
               'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'source_archive_sha256': hashlib.sha256((materials / 'codec2-source.tar.gz').read_bytes()).hexdigest()}
    (output / 'audio-build.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--ndk', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--abi', choices=['all', *ABIS], default='arm64-v8a')
    parser.add_argument('--cmake', default='cmake')
    args = parser.parse_args()
    print(json.dumps(build(args.source.resolve(), args.ndk.resolve(), args.out.resolve(), args.abi, args.cmake)))


if __name__ == '__main__':
    main()
